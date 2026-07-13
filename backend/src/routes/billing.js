/**
 * ParkiPay — Billing routes (Redis-enhanced)
 *
 * POST /api/billing/generate/           — Generate bill (duplicate-safe)
 * GET  /api/billing/history/            — Officer's bills today
 * GET  /api/billing/stats/              — Officer's today totals
 * GET  /api/billing/active-bill/?plate= — Check existing active bill
 * GET  /api/billing/:cn/status/         — Bill status by control number
 */

const { Router } = require('express');
const { z } = require('zod');

const prisma = require('../lib/prisma');
const redis = require('../lib/redis');
const logAction = require('../lib/audit');
const { authenticate } = require('../middleware/auth');
const cfg = require('../config');

const {
  generateControlNumber,
  getActiveBillForPlate,
} = require('../lib/controlNumber');

const { isValidTzMobile } = require('../lib/phone');


function fmtDarEsSalaam(date) {
  const d = new Date(date.getTime() + 3 * 60 * 60 * 1000);

  const pad = (n) => String(n).padStart(2, '0');

  const day = pad(d.getUTCDate());
  const month = pad(d.getUTCMonth() + 1);
  const year = d.getUTCFullYear();
  const hh = pad(d.getUTCHours());
  const mm = pad(d.getUTCMinutes());

  return `${day}/${month}/${year} ${hh}:${mm}`;
}


function buildBillSms({
  plateNumber,
  controlNumber,
  amountDue,
  locationName,
  generatedAt,
  expiresAt,
}) {
  const amountFmt = `TZS ${Number(amountDue).toLocaleString('en-US')}`;

  return (
    `ParkiPay: Bili ya maegesho - ${locationName}\n` +
    `Gari: ${plateNumber}\n` +
    `Namba ya Malipo: ${controlNumber}\n` +
    `Kiasi cha Kulipa: ${amountFmt}\n` +
    `Muda wa Kutolewa: ${fmtDarEsSalaam(new Date(generatedAt))}\n` +
    `Inaisha: ${fmtDarEsSalaam(new Date(expiresAt))}\n` +
    `Lipa kupitia namba ya malipo hapo juu kabla ya muda kuisha. Asante kwa kutumia ParkiPay.`
  );
}


const router = Router();

router.use(authenticate);

const ACTIVE_BILL_TTL = 120;


const GenerateSchema = z.object({
  plate_number: z.string().min(1, 'plate_number is required'),
  location_id: z.number().int().positive(),
});


// -----------------------------------------------------------------------------
// POST /billing/generate/
// -----------------------------------------------------------------------------
router.post('/generate/', async (req, res, next) => {
  try {
    const parsed = GenerateSchema.safeParse(req.body);

    if (!parsed.success) {
      return res.status(400).json({
        error: 'validation_error',
        detail: parsed.error.flatten(),
      });
    }


    const {
      plate_number,
      location_id,
    } = parsed.data;


    const plate = plate_number
      .trim()
      .toUpperCase()
      .replace(/\s/g, '');


    const billCacheKey =
      `active_bill:${plate}:${location_id}`;


    let existing = await redis.cacheGet(billCacheKey);


    if (!existing) {
      existing = await getActiveBillForPlate(
        plate,
        location_id
      );
    }


    if (existing) {

      const cooldownSecs =
        (cfg.billing.cooldownMinutes ?? 1) * 60;


      await redis.cacheSet(
        billCacheKey,
        existing,
        cooldownSecs
      );


      await logAction(
        req.officer,
        logAction.ACTIONS.BILL_DUPLICATE_BLOCKED,
        {
          plateNumber: plate,
          controlNumber: existing.controlNumber,
          result: 'duplicate_blocked',
          req,
        }
      );


      const cooldownMs =
        (cfg.billing.cooldownMinutes ?? 1) *
        60 *
        1000;


      const allowedAfter =
        new Date(
          new Date(existing.generatedAt).getTime()
          + cooldownMs
        );


      return res.status(409).json({
        error: 'duplicate_bill',
        detail:
          `Vehicle already billed. New bill allowed after ${cfg.billing.cooldownMinutes} minute(s).`,
        allowed_after: allowedAfter.toISOString(),
        existing_bill: {
          control_number: existing.controlNumber,
          expires_at: existing.expiresAt,
          issued_by: existing.officer?.fullName ?? null,
          officer_id: existing.officer?.employeeId ?? null,
          location: existing.location?.name ?? null,
          amount_due: existing.amountDue,
          generated_at: existing.generatedAt,
        },
      });
    }


    const location =
      await prisma.parkingLocation.findUnique({
        where: {
          id: location_id,
        },
      });


    if (!location || !location.isActive) {
      return res.status(400).json({
        error: 'invalid_location',
        detail:
          'Parking location not found or inactive.',
      });
    }


    const vehicleCacheKey =
      `vehicle:${plate}`;


    let vehicle =
      await redis.cacheGet(vehicleCacheKey);


    if (!vehicle) {
      vehicle =
        await prisma.vehicle.findUnique({
          where: {
            plateNumber: plate,
          },
        });
    }


    const feeMap = {
      MOTORCYCLE: location.feeMotorcycle,
      PRIVATE_CAR: location.feePrivateCar,
      MINIBUS: location.feeMinibus,
      BUS: location.feeBus,
      TRUCK: location.feeTruck,
      GOVERNMENT: location.feeGovernment,
    };


    const amountDue =
      feeMap[vehicle?.category ?? 'PRIVATE_CAR']
      ?? location.feePrivateCar;



    const expiresAt =
      new Date(
        Date.now()
        + cfg.billing.validityHours * 3600000
      );


    const bill =
      await prisma.controlNumber.create({
        data: {
          controlNumber: generateControlNumber(),
          plateNumber: plate,
          vehicleId: vehicle?.id ?? null,
          officerId: req.officer.id,
          locationId: location.id,
          amountDue,
          expiresAt,
        },
        include: {
          officer: true,
          location: true,
          vehicle: true,
        },
      });



    await redis.cacheSet(
      billCacheKey,
      bill,
      ACTIVE_BILL_TTL
    );


    await redis.cacheDel(
      `stats:${req.officer.id}`
    );



    if (
      vehicle?.ownerPhone &&
      isValidTzMobile(vehicle.ownerPhone)
    ) {

      const { sendSMS } =
        require('../lib/sms');


      const smsText =
        buildBillSms({
          plateNumber: bill.plateNumber,
          controlNumber: bill.controlNumber,
          amountDue: bill.amountDue,
          locationName: location.name,
          generatedAt: bill.generatedAt,
          expiresAt: bill.expiresAt,
        });


      sendSMS(vehicle.ownerPhone, smsText)
        .catch((err) =>
          console.error(
            '[Billing] SMS error:',
            err.message
          )
        );

    }


    await logAction(
      req.officer,
      logAction.ACTIONS.BILL_GENERATED,
      {
        plateNumber: plate,
        controlNumber: bill.controlNumber,
        result: 'success',
        req,
      }
    );


    return res.status(201).json(bill);


  } catch (err) {
    next(err);
  }
});


// Other routes (/history, /stats, /active-bill, /:cn/status)
// remain unchanged from your existing file.

module.exports = router;

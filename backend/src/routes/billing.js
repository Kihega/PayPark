/**
 * ParkiPay — Billing routes  (Redis-enhanced)
 *
 * POST /api/billing/generate/           — Generate bill (duplicate-safe)
 * GET  /api/billing/history/            — Officer's bills today
 * GET  /api/billing/stats/              — Officer's today totals (count + amount)
 * GET  /api/billing/active-bill/?plate= — Check for existing active bill
 * GET  /api/billing/:cn/status/         — Bill status by control number
 */
const { Router }       = require('express');
const { z }            = require('zod');
const prisma           = require('../lib/prisma');
const redis            = require('../lib/redis');
const logAction        = require('../lib/audit');
const { authenticate } = require('../middleware/auth');
const cfg              = require('../config');
const {
  generateControlNumber,
  getActiveBillForPlate,
} = require('../lib/controlNumber');
const { isValidTzMobile } = require('../lib/phone');

// ── Swahili SMS bill formatter ────────────────────────────────────────────
// Dar es Salaam is UTC+3 year-round (no DST), so a fixed-offset format
// avoids depending on the server's local timezone/ICU data.
function fmtDarEsSalaam(date) {
  const d = new Date(date.getTime() + 3 * 60 * 60 * 1000); // shift to EAT
  const pad = (n) => String(n).padStart(2, '0');
  const day   = pad(d.getUTCDate());
  const month = pad(d.getUTCMonth() + 1);
  const year  = d.getUTCFullYear();
  const hh    = pad(d.getUTCHours());
  const mm    = pad(d.getUTCMinutes());
  return `${day}/${month}/${year} ${hh}:${mm}`;
}

function buildBillSms({ ownerName, plateNumber, controlNumber, amountDue, locationName, generatedAt, expiresAt }) {
  const amountFmt = `TZS ${Number(amountDue).toLocaleString('en-US')}`;
  return (
    `ParkiPay: Bili ya maegesho - ${locationName}\n` +
    `Gari: ${plateNumber}\n` +
    `Namba ya Udhibiti: ${controlNumber}\n` +
    `Kiasi cha Kulipa: ${amountFmt}\n` +
    `Muda wa Kutolewa: ${fmtDarEsSalaam(new Date(generatedAt))}\n` +
    `Inaisha: ${fmtDarEsSalaam(new Date(expiresAt))}\n` +
    `Lipa kupitia namba ya udhibiti hapo juu kabla ya muda kuisha. Asante kwa kutumia ParkiPay.`
  );
}

const router = Router();
router.use(authenticate);

const ACTIVE_BILL_TTL = 120; // 2 min — short TTL, changes when bill is generated

// ── POST /api/billing/generate/ ───────────────────────────────────────────────
const GenerateSchema = z.object({
  plate_number: z.string().min(1, 'plate_number is required'),
  location_id:  z.number().int().positive('location_id must be a positive integer'),
});

router.post('/generate/', async (req, res, next) => {
  try {
    const parsed = GenerateSchema.safeParse(req.body);
    if (!parsed.success) {
      return res.status(400).json({ error: 'validation_error', detail: parsed.error.flatten() });
    }

    const { plate_number, location_id } = parsed.data;
    const plate = plate_number.trim().toUpperCase().replace(/\s/g, '');

    // ── 1. Duplicate check (Redis-first, per plate+location, 1-min cooldown)
    const billCacheKey = `active_bill:${plate}:${location_id}`;
    let existing = await redis.cacheGet(billCacheKey);
    if (!existing) {
      existing = await getActiveBillForPlate(plate, location_id);
    }

    if (existing) {
      // TTL matches cooldown window so cache expires exactly when a new bill is allowed
      const cooldownSecs = (cfg.billing.cooldownMinutes ?? 1) * 60;
      await redis.cacheSet(billCacheKey, existing, cooldownSecs);
      await logAction(req.officer, logAction.ACTIONS.BILL_DUPLICATE_BLOCKED, {
        plateNumber: plate, controlNumber: existing.controlNumber,
        result: 'duplicate_blocked', req,
      });
      const cooldownMs   = (cfg.billing.cooldownMinutes ?? 1) * 60 * 1000;
      const allowedAfter = new Date(new Date(existing.generatedAt).getTime() + cooldownMs);
      return res.status(409).json({
        error: 'duplicate_bill',
        detail: `This vehicle was already billed at this location. New bill allowed after ${cfg.billing.cooldownMinutes} minute(s).`,
        cooldown_minutes: cfg.billing.cooldownMinutes ?? 1,
        allowed_after:    allowedAfter.toISOString(),
        existing_bill: {
          control_number: existing.controlNumber,
          expires_at:     existing.expiresAt,
          issued_by:      existing.officer?.fullName ?? null,
          officer_id:     existing.officer?.employeeId ?? null,
          location:       existing.location?.name ?? null,
          amount_due:     existing.amountDue,
          generated_at:   existing.generatedAt,
        },
      });
    }

    // ── 2. Validate parking location ──────────────────────────────────────
    const location = await prisma.parkingLocation.findUnique({ where: { id: location_id } });
    if (!location || !location.isActive) {
      return res.status(400).json({ error: 'invalid_location', detail: 'Parking location not found or inactive.' });
    }

    // ── 3. Vehicle registry lookup ────────────────────────────────────────
    const vehicleCacheKey = `vehicle:${plate}`;
    let vehicle = await redis.cacheGet(vehicleCacheKey);
    if (!vehicle) {
      vehicle = await prisma.vehicle.findUnique({ where: { plateNumber: plate } });
    }

    // ── 4. Fee determination ──────────────────────────────────────────────
    const feeMap = {
      MOTORCYCLE:  location.feeMotorcycle,
      PRIVATE_CAR: location.feePrivateCar,
      MINIBUS:     location.feeMinibus,
      BUS:         location.feeBus,
      TRUCK:       location.feeTruck,
      GOVERNMENT:  location.feeGovernment,
    };
    const amountDue = feeMap[vehicle?.category ?? 'PRIVATE_CAR'] ?? location.feePrivateCar;

    // ── 5. Create the bill ─────────────────────────────────────────────────
    const expiresAt = new Date(Date.now() + cfg.billing.validityHours * 3_600_000);
    const bill = await prisma.controlNumber.create({
      data: {
        controlNumber: generateControlNumber(),
        plateNumber:   plate,
        vehicleId:     vehicle?.id ?? null,
        officerId:     req.officer.id,
        locationId:    location.id,
        amountDue,
        expiresAt,
      },
      include: { officer: true, location: true, vehicle: true },
    });

    // ── 6. Cache the new active bill + invalidate officer stats ───────────
    await redis.cacheSet(billCacheKey, bill, ACTIVE_BILL_TTL);
    await redis.cacheDel(`stats:${req.officer.id}`);

    // ── 7. SMS to vehicle owner (if registered + valid TZ number) ─────────
    if (vehicle?.ownerPhone && isValidTzMobile(vehicle.ownerPhone)) {
      const { sendSMS } = require('../lib/sms');
      const smsText = buildBillSms({
        ownerName:     vehicle.ownerName,
        plateNumber:   bill.plateNumber,
        controlNumber: bill.controlNumber,
        amountDue:     bill.amountDue,
        locationName:  location.name,
        generatedAt:   bill.generatedAt,
        expiresAt:     bill.expiresAt,
      });

      sendSMS(vehicle.ownerPhone, smsText).catch((e) =>
        console.error('[Billing] SMS fire-and-forget error:', e.message));
    } else if (vehicle?.ownerPhone) {
      console.warn(`[Billing] Skipped SMS — invalid TZ mobile number on file: ${vehicle.ownerPhone}`);
    }

    await logAction(req.officer, logAction.ACTIONS.BILL_GENERATED, {
      plateNumber: plate, controlNumber: bill.controlNumber, result: 'success', req,
    });

    return res.status(201).json(bill);
  } catch (err) { next(err); }
});

// ── GET /api/billing/history/ ─────────────────────────────────────────────────
router.get('/history/', async (req, res, next) => {
  try {
    const startOfDay = new Date();
    startOfDay.setHours(0, 0, 0, 0);

    const bills = await prisma.controlNumber.findMany({
      where: { officerId: req.officer.id, generatedAt: { gte: startOfDay } },
      include: { location: true, vehicle: true },
      orderBy: { generatedAt: 'desc' },
    });
    return res.json(bills);
  } catch (err) { next(err); }
});

// ── GET /api/billing/stats/ ───────────────────────────────────────────────────
router.get('/stats/', async (req, res, next) => {
  try {
    const cacheKey = `stats:${req.officer.id}`;
    const cached = await redis.cacheGet(cacheKey);
    if (cached) return res.json(cached);

    const startOfDay = new Date();
    startOfDay.setHours(0, 0, 0, 0);

    const bills = await prisma.controlNumber.findMany({
      where: { officerId: req.officer.id, generatedAt: { gte: startOfDay } },
      select: { amountDue: true, status: true },
    });

    const totalBills  = bills.length;
    const totalAmount = bills.reduce((sum, b) => sum + Number(b.amountDue), 0);

    const stats = { totalBills, totalAmount };
    await redis.cacheSet(cacheKey, stats, 60); // 1-min cache
    return res.json(stats);
  } catch (err) { next(err); }
});

// ── GET /api/billing/active-bill/?plate=&location_id= ────────────────────
router.get('/active-bill/', async (req, res, next) => {
  try {
    const raw        = req.query.plate || '';
    const plate      = raw.trim().toUpperCase().replace(/\s/g, '');
    const locationId = req.query.location_id ? parseInt(req.query.location_id, 10) : null;
    if (!plate) return res.status(400).json({ error: 'validation_error', detail: '`plate` is required.' });

    const cacheKey = locationId ? `active_bill:${plate}:${locationId}` : `active_bill:${plate}`;
    let bill = await redis.cacheGet(cacheKey);
    if (!bill) {
      bill = await getActiveBillForPlate(plate, locationId);
      if (bill) {
        const cooldownSecs = (cfg.billing?.cooldownMinutes ?? 1) * 60;
        await redis.cacheSet(cacheKey, bill, cooldownSecs);
      }
    }

    if (!bill) return res.json({ active: false, bill: null });

    return res.json({
      active: true,
      bill: {
        control_number: bill.controlNumber,
        expires_at:     bill.expiresAt,
        issued_by:      bill.officer?.fullName ?? null,
        officer_id:     bill.officer?.employeeId ?? null,
        location:       bill.location?.name ?? null,
        amount_due:     bill.amountDue,
        generated_at:   bill.generatedAt,
      },
    });
  } catch (err) { next(err); }
});

// ── GET /api/billing/:cn/status/ ──────────────────────────────────────────────
router.get('/:cn/status/', async (req, res, next) => {
  try {
    const bill = await prisma.controlNumber.findUnique({
      where: { controlNumber: req.params.cn }, include: { officer: true, location: true },
    });
    if (!bill) return res.status(404).json({ error: 'not_found', detail: 'Control number not found.' });

    const minutesRemaining = Math.max(
      0, Math.floor((new Date(bill.expiresAt) - Date.now()) / 60_000),
    );
    return res.json({ ...bill, minutesRemaining });
  } catch (err) { next(err); }
});

module.exports = router;

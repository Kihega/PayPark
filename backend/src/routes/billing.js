/**
 * ParkiPay — Billing routes (Sprint 3)
 * POST /api/billing/generate/           — global duplicate check + generate
 * GET  /api/billing/history/            — officer daily bill history
 * GET  /api/billing/:cn/status/         — bill status
 */
const { Router } = require('express');
const { z }   = require('zod');
const prisma  = require('../lib/prisma');
const logAction = require('../lib/audit');
const { generateControlNumber, getActiveBillForPlate } = require('../lib/controlNumber');
const { authenticate } = require('../middleware/auth');
const cfg = require('../config');

const router = Router();
router.use(authenticate);

// ── POST /api/billing/generate/ ───────────────────────────────────────────────

const GenerateSchema = z.object({
  plate_number: z.string().min(1),
  location_id:  z.number().int().positive(),
});

router.post('/generate/', async (req, res, next) => {
  try {
    const parsed = GenerateSchema.safeParse(req.body);
    if (!parsed.success) {
      return res.status(400).json({ error: 'validation_error', detail: parsed.error.flatten() });
    }
    const { plate_number, location_id } = parsed.data;
    const plate = plate_number.trim().toUpperCase().replace(/\s/g, '');

    // 1. Global duplicate check
    const existing = await getActiveBillForPlate(plate);
    if (existing) {
      await logAction(req.officer, logAction.ACTIONS.BILL_DUPLICATE_BLOCKED, {
        plateNumber: plate,
        controlNumber: existing.controlNumber,
        result: 'duplicate_blocked',
        req,
      });
      return res.status(409).json({
        error: 'duplicate_bill',
        detail: 'This vehicle already has an active parking bill.',
        existing_bill: {
          control_number:  existing.controlNumber,
          expires_at:      existing.expiresAt,
          issued_by:       existing.officer?.fullName ?? null,
          location:        existing.location?.name ?? null,
        },
      });
    }

    // 2. Validate location
    const location = await prisma.parkingLocation.findUnique({ where: { id: location_id } });
    if (!location || !location.isActive) {
      return res.status(400).json({ error: 'invalid_location', detail: 'Parking location not found or inactive.' });
    }

    // 3. Lookup vehicle (optional — bill can be issued without registry hit)
    const vehicle = await prisma.vehicle.findUnique({ where: { plateNumber: plate } });

    // 4. Determine fee
    const feeMap = {
      MOTORCYCLE:  location.feeMotorcycle,
      PRIVATE_CAR: location.feePrivateCar,
      MINIBUS:     location.feeMinibus,
      BUS:         location.feeBus,
      TRUCK:       location.feeTruck,
      GOVERNMENT:  location.feeGovernment,
    };
    const amountDue = feeMap[vehicle?.category ?? 'PRIVATE_CAR'] ?? location.feePrivateCar;

    // 5. Create bill
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

    await logAction(req.officer, logAction.ACTIONS.BILL_GENERATED, {
      plateNumber:   plate,
      controlNumber: bill.controlNumber,
      result:        'success',
      req,
    });

    return res.status(201).json(bill);
  } catch (err) { next(err); }
});

// ── GET /api/billing/history/ ─────────────────────────────────────────────────

router.get('/history/', async (req, res, next) => {
  try {
    const since = new Date();
    since.setHours(0, 0, 0, 0); // start of today

    const bills = await prisma.controlNumber.findMany({
      where: { officerId: req.officer.id, generatedAt: { gte: since } },
      include: { location: true, vehicle: true },
      orderBy: { generatedAt: 'desc' },
    });

    return res.json(bills);
  } catch (err) { next(err); }
});

// ── GET /api/billing/:cn/status/ ──────────────────────────────────────────────

router.get('/:cn/status/', async (req, res, next) => {
  try {
    const bill = await prisma.controlNumber.findUnique({
      where: { controlNumber: req.params.cn },
      include: { officer: true, location: true },
    });

    if (!bill) {
      return res.status(404).json({ error: 'not_found', detail: 'Control number not found.' });
    }

    const minutesRemaining = Math.max(0, Math.floor((bill.expiresAt - Date.now()) / 60_000));
    return res.json({ ...bill, minutesRemaining });
  } catch (err) { next(err); }
});

module.exports = router;

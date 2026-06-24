/**
 * ParkiPay — Admin routes
 *
 * Officers:
 *   GET    /api/admin/officers/              — list all officers
 *   POST   /api/admin/officers/              — create officer
 *   DELETE /api/admin/officers/:id/          — remove officer
 *   PATCH  /api/admin/officers/:id/location/ — move officer to location
 *   GET    /api/admin/locations/             — list parking locations
 *
 * Vehicles (registry management):
 *   GET    /api/admin/vehicles/              — list all registered vehicles
 *   POST   /api/admin/vehicles/              — register new vehicle (SMS owner)
 *   DELETE /api/admin/vehicles/:id/          — remove vehicle from registry
 */
const { Router } = require('express');
const { z }      = require('zod');
const prisma     = require('../lib/prisma');
const redis      = require('../lib/redis');
const { sendSMS } = require('../lib/sms');
const { authenticate } = require('../middleware/auth');

const router = Router();

function adminOnly(req, res, next) {
  const role = req.officer?.role;
  if (role !== 'SUPERVISOR') {
    return res.status(403).json({ error: 'forbidden', detail: 'Supervisor role required.' });
  }
  next();
}

router.use(authenticate, adminOnly);

// ── GET /api/admin/officers/ ──────────────────────────────────────────────────
router.get('/officers/', async (req, res, next) => {
  try {
    const officers = await prisma.officer.findMany({
      include: { location: true },
      orderBy: { createdAt: 'asc' },
    });
    res.json(officers.map(o => ({
      id:           o.id,
      employeeId:   o.employeeId,
      fullName:     o.fullName,
      role:         o.role,
      isActive:     o.isActive,
      locationName: o.location ? o.location.name : null,
      locationId:   o.locationId,
    })));
  } catch (err) { next(err); }
});

// ── POST /api/admin/officers/ ─────────────────────────────────────────────────
const CreateOfficerSchema = z.object({
  employeeId: z.string().min(2).max(20),
  fullName:   z.string().min(2),
  locationId: z.number().int().positive().nullable().optional(),
  role:       z.enum(['ATTENDANT','SUPERVISOR']).default('ATTENDANT'),
});

router.post('/officers/', async (req, res, next) => {
  try {
    const parsed = CreateOfficerSchema.safeParse(req.body);
    if (!parsed.success)
      return res.status(400).json({ error: 'validation_error', detail: parsed.error.flatten() });

    const { employeeId, fullName, locationId, role } = parsed.data;
    const exists = await prisma.officer.findUnique({ where: { employeeId } });
    if (exists)
      return res.status(409).json({ error: 'duplicate', detail: 'Employee ID already exists.' });

    const officer = await prisma.officer.create({
      data: { employeeId, fullName, role, passwordHash: '', locationId: locationId ?? null },
      include: { location: true },
    });

    res.status(201).json({
      id: officer.id, employeeId: officer.employeeId,
      fullName: officer.fullName, role: officer.role,
      locationName: officer.location?.name ?? null,
    });
  } catch (err) { next(err); }
});

// ── DELETE /api/admin/officers/:id/ ──────────────────────────────────────────
router.delete('/officers/:id/', async (req, res, next) => {
  try {
    const id = parseInt(req.params.id, 10);
    if (isNaN(id)) return res.status(400).json({ error: 'invalid_id', detail: 'Invalid officer ID.' });

    const officer = await prisma.officer.findUnique({ where: { id }, select: { id: true, fullName: true } });
    if (!officer) return res.status(404).json({ error: 'not_found', detail: 'Officer not found.' });

    if (id === req.officer.id) {
      return res.status(400).json({ error: 'self_delete', detail: 'You cannot remove your own account.' });
    }

    // Interactive transaction: nullify all FK references, then delete
    // Uses tx (not prisma) so everything is inside ONE database transaction.
    await prisma.$transaction(async (tx) => {
      // 1. Nullify FK on audit_logs  (officerId is optional → can be set null)
      await tx.auditLog.updateMany({ where: { officerId: id }, data: { officerId: null } });
      // 2. Nullify FK on control_numbers  (same)
      await tx.controlNumber.updateMany({ where: { officerId: id }, data: { officerId: null } });
      // 3. OfficerBiometric has onDelete: Cascade in schema — Prisma handles it automatically
      // 4. Now safe to delete the officer row
      await tx.officer.delete({ where: { id } });
    });

    // Bust Redis caches for this officer
    await redis.cacheDel(`officer:${id}`, `stats:${id}`);

    res.json({ detail: `Officer "${officer.fullName}" removed successfully.` });
  } catch (err) {
    // Surface the real Prisma error message in development
    console.error('[Admin] Officer delete failed:', err.message);
    next(err);
  }
});

// ── PATCH /api/admin/officers/:id/location/ ───────────────────────────────────
router.patch('/officers/:id/location/', async (req, res, next) => {
  try {
    const id         = parseInt(req.params.id, 10);
    const locationId = parseInt(req.body.locationId, 10);
    const officer = await prisma.officer.update({
      where: { id }, data: { locationId }, include: { location: true },
    });
    // Invalidate cached officer profile
    await redis.cacheDel(`officer:${id}`);
    res.json({ id: officer.id, locationName: officer.location?.name ?? null });
  } catch (err) { next(err); }
});

// ── GET /api/admin/locations/ ─────────────────────────────────────────────────
router.get('/locations/', async (req, res, next) => {
  try {
    const locs = await prisma.parkingLocation.findMany({
      where: { isActive: true }, orderBy: { name: 'asc' },
      select: { id:true, name:true, region:true },
    });
    res.json(locs);
  } catch (err) { next(err); }
});

// ═══════════════════════════════════════════════════════════════════════════════
//  VEHICLE REGISTRY MANAGEMENT
// ═══════════════════════════════════════════════════════════════════════════════

// ── GET /api/admin/vehicles/ ──────────────────────────────────────────────────
router.get('/vehicles/', async (req, res, next) => {
  try {
    const vehicles = await prisma.vehicle.findMany({
      orderBy: { createdAt: 'desc' },
      select: {
        id: true, plateNumber: true, ownerName: true, ownerPhone: true,
        make: true, model: true, category: true, isValid: true, createdAt: true,
      },
    });
    res.json(vehicles);
  } catch (err) { next(err); }
});

// ── POST /api/admin/vehicles/ ─────────────────────────────────────────────────
const RegisterVehicleSchema = z.object({
  plateNumber: z.string().min(3).max(15),
  ownerName:   z.string().min(2),
  ownerPhone:  z.string().min(10).max(15),
  make:        z.string().optional().default(''),
  model:       z.string().optional().default(''),
  category:    z.enum(['MOTORCYCLE','PRIVATE_CAR','MINIBUS','BUS','TRUCK','GOVERNMENT'])
                 .optional().default('PRIVATE_CAR'),
});

router.post('/vehicles/', async (req, res, next) => {
  try {
    const parsed = RegisterVehicleSchema.safeParse(req.body);
    if (!parsed.success)
      return res.status(400).json({ error: 'validation_error', detail: parsed.error.flatten() });

    const { plateNumber: rawPlate, ownerName, ownerPhone, make, model, category } = parsed.data;
    const plateNumber = rawPlate.trim().toUpperCase().replace(/\s+/g, '');

    const existing = await prisma.vehicle.findUnique({ where: { plateNumber } });
    if (existing)
      return res.status(409).json({ error: 'duplicate', detail: `Plate ${plateNumber} is already registered.` });

    const vehicle = await prisma.vehicle.create({
      data: { plateNumber, ownerName, ownerPhone, make: make ?? '', model: model ?? '', category },
    });

    // Invalidate any cached lookup for this plate
    await redis.cacheDel(`vehicle:${plateNumber}`);

    // Send SMS to owner with registration confirmation
    const smsText =
      `ParkiPay: Gari lako (${plateNumber}) limesajiliwa kwenye mfumo wa maegesho. ` +
      `Ukipata faini utapokea ujumbe mwingine. Asante!`;
    const smsResult = await sendSMS(ownerPhone, smsText);
    if (!smsResult.success) {
      console.warn('[Admin] Vehicle registered but SMS failed:', smsResult.error);
    }

    res.status(201).json({ ...vehicle, smsSent: smsResult.success });
  } catch (err) { next(err); }
});

// ── DELETE /api/admin/vehicles/:id/ ──────────────────────────────────────────
router.delete('/vehicles/:id/', async (req, res, next) => {
  try {
    const id = parseInt(req.params.id, 10);
    if (isNaN(id)) return res.status(400).json({ error: 'invalid_id', detail: 'Invalid vehicle ID.' });

    const vehicle = await prisma.vehicle.findUnique({ where: { id }, select: { plateNumber: true } });
    if (!vehicle)
      return res.status(404).json({ error: 'not_found', detail: 'Vehicle not found.' });

    // Interactive transaction: nullify vehicleId on any bills referencing this vehicle, then delete
    await prisma.$transaction(async (tx) => {
      // Nullify FK on control_numbers.vehicleId (optional field)
      await tx.controlNumber.updateMany({ where: { vehicleId: id }, data: { vehicleId: null } });
      await tx.vehicle.delete({ where: { id } });
    });

    await redis.cacheDel(`vehicle:${vehicle.plateNumber}`);
    res.json({ detail: 'Vehicle removed from registry.' });
  } catch (err) {
    console.error('[Admin] Vehicle delete failed:', err.message);
    next(err);
  }
});

module.exports = router;

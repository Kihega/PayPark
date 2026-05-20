/**
 * ParkiPay — Admin routes  (simple officer management)
 *
 * All routes require a valid JWT with role SUPERVISOR or ADMIN.
 *
 * GET    /api/admin/officers/              — list all officers
 * POST   /api/admin/officers/              — create officer
 * DELETE /api/admin/officers/:id/          — remove officer
 * PATCH  /api/admin/officers/:id/location/ — move officer to location
 * GET    /api/admin/locations/             — list parking locations
 */
const { Router } = require('express');
const { z }      = require('zod');
const prisma     = require('../lib/prisma');
const { authenticate } = require('../middleware/auth');

const router = Router();

// ── Middleware: admin/supervisor only ─────────────────────────────────────────
function adminOnly(req, res, next) {
  const role = req.officer?.role;
  if (role !== 'SUPERVISOR' && role !== 'ADMIN') {
    return res.status(403).json({ error: 'forbidden', detail: 'Supervisor or Admin role required.' });
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
      locationName: o.location ? `${o.location.name}` : null,
      locationId:   o.locationId,
    })));
  } catch (err) { next(err); }
});

// ── POST /api/admin/officers/ ─────────────────────────────────────────────────
const CreateSchema = z.object({
  employeeId: z.string().min(2).max(20),
  fullName:   z.string().min(2),
  locationId: z.number().int().positive().nullable().optional(),
  role:       z.enum(['FIELD_OFFICER','SUPERVISOR']).default('FIELD_OFFICER'),
});

router.post('/officers/', async (req, res, next) => {
  try {
    const parsed = CreateSchema.safeParse(req.body);
    if (!parsed.success)
      return res.status(400).json({ error: 'validation_error', detail: parsed.error.flatten() });

    const { employeeId, fullName, locationId, role } = parsed.data;
    const exists = await prisma.officer.findUnique({ where: { employeeId } });
    if (exists)
      return res.status(409).json({ error: 'duplicate', detail: 'Employee ID already exists.' });

    const officer = await prisma.officer.create({
      data: { employeeId, fullName, role,
        passwordHash: '', // no password — ID-only auth
        locationId:   locationId ?? null },
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
    await prisma.officer.delete({ where: { id } });
    res.json({ detail: 'Officer removed.' });
  } catch (err) { next(err); }
});

// ── PATCH /api/admin/officers/:id/location/ ───────────────────────────────────
router.patch('/officers/:id/location/', async (req, res, next) => {
  try {
    const id         = parseInt(req.params.id, 10);
    const locationId = parseInt(req.body.locationId, 10);
    const officer = await prisma.officer.update({
      where: { id },
      data:  { locationId },
      include: { location: true },
    });
    res.json({ id: officer.id, locationName: officer.location?.name ?? null });
  } catch (err) { next(err); }
});

// ── GET /api/admin/locations/ ─────────────────────────────────────────────────
router.get('/locations/', async (req, res, next) => {
  try {
    const locs = await prisma.parkingLocation.findMany({
      where:   { isActive: true },
      orderBy: { name: 'asc' },
      select:  { id:true, name:true, region:true },
    });
    res.json(locs);
  } catch (err) { next(err); }
});

module.exports = router;

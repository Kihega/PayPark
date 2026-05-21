/**
 * ParkiPay — Vehicle routes  (Redis-cached lookup)
 *
 * GET /api/vehicles/lookup/?plate=  — Vehicle registry lookup  (cached 10 min)
 * GET /api/vehicles/locations/      — Active parking locations
 */
const { Router }       = require('express');
const prisma           = require('../lib/prisma');
const redis            = require('../lib/redis');
const logAction        = require('../lib/audit');
const { authenticate } = require('../middleware/auth');

const router = Router();
router.use(authenticate);

const VEHICLE_CACHE_TTL = 600; // 10 minutes

// ── GET /api/vehicles/lookup/?plate= ─────────────────────────────────────────
router.get('/lookup/', async (req, res, next) => {
  try {
    const raw   = req.query.plate || '';
    const plate = raw.trim().toUpperCase().replace(/\s/g, '');

    if (!plate) {
      return res.status(400).json({
        error: 'validation_error', detail: '`plate` query parameter is required.',
      });
    }

    // ── Redis cache ────────────────────────────────────────────────────────
    const cacheKey = `vehicle:${plate}`;
    let vehicle = await redis.cacheGet(cacheKey);

    if (!vehicle) {
      vehicle = await prisma.vehicle.findUnique({ where: { plateNumber: plate } });
      if (vehicle) {
        await redis.cacheSet(cacheKey, vehicle, VEHICLE_CACHE_TTL);
      }
    }

    if (!vehicle) {
      await logAction(req.officer, logAction.ACTIONS.PLATE_NOT_FOUND, {
        plateNumber: plate, result: 'not_found', req,
      });
      return res.status(404).json({ error: 'not_found', detail: 'Vehicle not found in registry.' });
    }

    await logAction(req.officer, logAction.ACTIONS.VEHICLE_LOOKUP, {
      plateNumber: plate, result: 'found', req,
    });

    return res.json(vehicle);
  } catch (err) { next(err); }
});

// ── GET /api/vehicles/locations/ ─────────────────────────────────────────────
router.get('/locations/', async (_req, res, next) => {
  try {
    const locations = await prisma.parkingLocation.findMany({
      where: { isActive: true }, orderBy: [{ region: 'asc' }, { name: 'asc' }],
    });
    return res.json(locations);
  } catch (err) { next(err); }
});

module.exports = router;

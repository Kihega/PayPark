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



// ── POST /api/vehicles/ocr-plate/ ────────────────────────────────────────────
// Accepts a base64 image → runs Tesseract OCR → extracts TZ plate number
// Body: { image: "<base64 string>", mimeType: "image/jpeg" }
router.post('/ocr-plate/', async (req, res, next) => {
  try {
    const { image, mimeType = 'image/jpeg' } = req.body;
    if (!image) {
      return res.status(400).json({ error: 'validation_error', detail: '`image` (base64) is required.' });
    }

    // Write base64 to temp file
    const os   = require('os');
    const path = require('path');
    const fs   = require('fs');
    const tmpFile = path.join(os.tmpdir(), `plate_${Date.now()}.jpg`);

    const imgBuffer = Buffer.from(image.replace(/^data:image\/\w+;base64,/, ''), 'base64');
    fs.writeFileSync(tmpFile, imgBuffer);

    let extractedPlate = null;
    let rawText        = '';

    try {
      const Tesseract = require('tesseract.js');
      const { data: { text } } = await Tesseract.recognize(tmpFile, 'eng', {
        logger: () => {},  // silence progress logs
        tessedit_char_whitelist: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ',
      });
      rawText = text;
      console.log('[OCR] Raw text:', text.replace(/\n/g, ' ').trim());

      // Extract Tanzania plate pattern: T + 3 digits + 3 letters  (e.g. T882DXZ)
      // Also handle with spaces: T 882 DXZ
      const plateRegex = /\bT\s*(\d{3})\s*([A-Z]{3})\b/i;
      const match = text.replace(/\s+/g, ' ').toUpperCase().match(plateRegex);
      if (match) {
        extractedPlate = `T${match[1]}${match[2]}`;
        console.log('[OCR] Extracted plate:', extractedPlate);
      }
    } finally {
      // Clean up temp file
      try { fs.unlinkSync(tmpFile); } catch {}
    }

    if (extractedPlate) {
      return res.json({
        success:  true,
        plate:    extractedPlate,
        rawText:  rawText.trim(),
      });
    }

    return res.json({
      success:  false,
      plate:    null,
      rawText:  rawText.trim(),
      detail:   'Could not extract a valid Tanzania plate number from the image. Try again with better lighting.',
    });
  } catch (err) {
    console.error('[OCR] Error:', err.message);
    next(err);
  }
});
module.exports = router;

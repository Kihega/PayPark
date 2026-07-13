/**
 * ParkiPay — Authentication Routes
 *
 * POST /api/auth/login/
 * POST /api/auth/refresh/
 * POST /api/auth/logout/
 * GET  /api/auth/me/
 */

const { Router } = require('express');
const { z } = require('zod');

const prisma = require('../lib/prisma');
const jwtLib = require('../lib/jwt');
const logAction = require('../lib/audit');
const { authenticate } = require('../middleware/auth');

const router = Router();

function officerProfile(officer) {
  return {
    id: officer.id,
    employeeId: officer.employeeId,
    fullName: officer.fullName,
    phone: officer.phone,
    email: officer.email,
    role: officer.role,
    locationId: officer.locationId ?? null,
    locationName: officer.location
      ? `${officer.location.name}, ${officer.location.region}`
      : null,
    isActive: officer.isActive,
    lastLogin: officer.lastLogin,
  };
}

const LoginSchema = z.object({
  employee_id: z.string().min(1, 'employee_id is required'),
});

// -----------------------------------------------------------------------------
// POST /login/
// -----------------------------------------------------------------------------
router.post('/login/', async (req, res, next) => {
  try {
    const parsed = LoginSchema.safeParse(req.body);

    if (!parsed.success) {
      return res.status(400).json({
        error: 'validation_error',
        detail: parsed.error.flatten(),
      });
    }

    const { employee_id: employeeId } = parsed.data;

    const officer = await prisma.officer.findUnique({
      where: { employeeId },
      include: { location: true },
    });

    if (!officer || !officer.isActive) {
      await logAction(null, 'LOGIN_FAILURE', {
        result: 'not_found',
        req,
      });

      return res.status(401).json({
        error: 'invalid_credentials',
        detail: 'Employee ID not found or account is inactive.',
      });
    }

    await prisma.officer.update({
      where: { id: officer.id },
      data: {
        lastLogin: new Date(),
        failedLoginAttempts: 0,
      },
    });

    const access = jwtLib.signAccess(officer);
    const { token: refresh } = jwtLib.signRefresh(officer);

    await logAction(officer, 'LOGIN_SUCCESS', {
      result: 'success',
      req,
    });

    return res.json({
      access,
      refresh,
      officer: officerProfile(officer),
    });
  } catch (err) {
    next(err);
  }
});

// -----------------------------------------------------------------------------
// POST /refresh/
// -----------------------------------------------------------------------------
router.post('/refresh/', async (req, res, next) => {
  try {
    const { refresh } = req.body;

    if (!refresh) {
      return res.status(400).json({
        error: 'refresh_required',
      });
    }

    let payload;

    try {
      payload = jwtLib.verify(refresh);
    } catch (err) {
      return res.status(401).json({
        error: 'invalid_token',
      });
    }

    if (await jwtLib.isBlacklisted(payload.jti)) {
      return res.status(401).json({
        error: 'token_blacklisted',
      });
    }

    await jwtLib.blacklist(payload.jti, payload.exp);

    const officer = await prisma.officer.findUnique({
      where: {
        id: Number(payload.sub),
      },
    });

    if (!officer || !officer.isActive) {
      return res.status(401).json({
        error: 'unauthorized',
      });
    }

    const access = jwtLib.signAccess(officer);
    const { token: newRefresh } = jwtLib.signRefresh(officer);

    return res.json({
      access,
      refresh: newRefresh,
    });
  } catch (err) {
    next(err);
  }
});

// -----------------------------------------------------------------------------
// POST /logout/
// -----------------------------------------------------------------------------
router.post('/logout/', async (req, res, next) => {
  try {
    const { refresh } = req.body;

    if (!refresh) {
      return res.status(400).json({
        error: 'refresh_required',
      });
    }

    let payload;

    try {
      payload = jwtLib.verify(refresh);
    } catch (err) {
      return res.json({
        detail: 'Logged out.',
      });
    }

    if (!(await jwtLib.isBlacklisted(payload.jti))) {
      await jwtLib.blacklist(payload.jti, payload.exp);
    }

    return res.json({
      detail: 'Logged out successfully.',
    });
  } catch (err) {
    next(err);
  }
});

// -----------------------------------------------------------------------------
// GET /me/
// -----------------------------------------------------------------------------
router.get('/me/', authenticate, (req, res) => {
  res.json(officerProfile(req.officer));
});

module.exports = router;

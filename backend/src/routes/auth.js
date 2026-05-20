/**
 * ParkiPay — Auth routes  (v2: employee-ID only, no password)
 *
 * POST /api/auth/login/    — { employee_id } → { access, refresh, officer }
 * POST /api/auth/refresh/  — { refresh }
 * POST /api/auth/logout/   — 200 OK
 * GET  /api/auth/me/       — officer profile
 */
const { Router }       = require('express');
const { z }            = require('zod');
const cfg              = require('../config');
const prisma           = require('../lib/prisma');
const jwtLib           = require('../lib/jwt');
const logAction        = require('../lib/audit');
const { authenticate } = require('../middleware/auth');

const router = Router();

function officerProfile(o) {
  return {
    id:           o.id,
    employeeId:   o.employeeId,
    fullName:     o.fullName,
    phone:        o.phone,
    email:        o.email,
    role:         o.role,
    locationName: o.location ? `${o.location.name}, ${o.location.region}` : null,
    isActive:     o.isActive,
    lastLogin:    o.lastLogin,
  };
}

// ── POST /api/auth/login/ ─────────────────────────────────────────────────────

const LoginSchema = z.object({
  employee_id: z.string().min(1, 'employee_id is required'),
});

router.post('/login/', async (req, res, next) => {
  try {
    const parsed = LoginSchema.safeParse(req.body);
    if (!parsed.success) {
      return res.status(400).json({ error: 'validation_error', detail: parsed.error.flatten() });
    }

    const { employee_id: employeeId } = parsed.data;

    const officer = await prisma.officer.findUnique({
      where:   { employeeId },
      include: { location: true },
    });

    if (!officer || !officer.isActive) {
      await logAction(null, 'LOGIN_FAILURE', { result: 'not_found', req });
      return res.status(401).json({
        error:  'invalid_credentials',
        detail: 'Employee ID not found or account is inactive.',
      });
    }

    // Update last login
    await prisma.officer.update({
      where: { id: officer.id },
      data:  { lastLogin: new Date(), failedLoginAttempts: 0 },
    });

    const access             = jwtLib.signAccess(officer);
    const { token: refresh } = jwtLib.signRefresh(officer);

    await logAction(officer, 'LOGIN_SUCCESS', { result: 'success', req });
    return res.json({ access, refresh, officer: officerProfile(officer) });
  } catch (err) { next(err); }
});

// ── POST /api/auth/refresh/ ───────────────────────────────────────────────────

router.post('/refresh/', async (req, res, next) => {
  try {
    const { refresh } = req.body;
    if (!refresh) return res.status(400).json({ error: 'refresh_required' });

    let payload;
    try { payload = jwtLib.verify(refresh); }
    catch { return res.status(401).json({ error: 'invalid_token' }); }

    if (await jwtLib.isBlacklisted(payload.jti))
      return res.status(401).json({ error: 'token_blacklisted' });

    await jwtLib.blacklist(payload.jti, payload.exp);

    const officer = await prisma.officer.findUnique({ where: { id: parseInt(payload.sub, 10) } });
    if (!officer || !officer.isActive)
      return res.status(401).json({ error: 'unauthorized' });

    const access              = jwtLib.signAccess(officer);
    const { token: newRefresh } = jwtLib.signRefresh(officer);
    return res.json({ access, refresh: newRefresh });
  } catch (err) { next(err); }
});

// ── POST /api/auth/logout/ ────────────────────────────────────────────────────

router.post('/logout/', async (req, res, next) => {
  try {
    const { refresh } = req.body;
    if (!refresh) return res.status(400).json({ error: 'refresh_required' });
    let payload;
    try { payload = jwtLib.verify(refresh); } catch { return res.json({ detail: 'Logged out.' }); }
    if (!(await jwtLib.isBlacklisted(payload.jti))) await jwtLib.blacklist(payload.jti, payload.exp);
    return res.json({ detail: 'Logged out successfully.' });
  } catch (err) { next(err); }
});

// ── GET /api/auth/me/ ─────────────────────────────────────────────────────────

router.get('/me/', authenticate, (req, res) => res.json(officerProfile(req.officer)));

module.exports = router;

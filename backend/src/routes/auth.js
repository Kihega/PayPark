/**
 * ParkiPay — Auth routes
 * POST /api/auth/login/    → { access, refresh, officer }
 * POST /api/auth/refresh/  → { access, refresh }
 * POST /api/auth/logout/   → 200 OK
 * GET  /api/auth/me/       → officer profile
 */
const { Router } = require('express');
const bcrypt  = require('bcryptjs');
const { z }   = require('zod');
const cfg     = require('../config');
const prisma  = require('../lib/prisma');
const jwtLib  = require('../lib/jwt');
const logAction = require('../lib/audit');
const { authenticate } = require('../middleware/auth');

const router = Router();

// ── Helpers ───────────────────────────────────────────────────────────────────

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
    createdAt:    o.createdAt,
    lastLogin:    o.lastLogin,
  };
}

// ── POST /api/auth/login/ ─────────────────────────────────────────────────────

const LoginSchema = z.object({
  employee_id: z.string().min(1),
  password:    z.string().min(1),
});

router.post('/login/', async (req, res, next) => {
  try {
    const parsed = LoginSchema.safeParse(req.body);
    if (!parsed.success) {
      return res.status(400).json({ error: 'validation_error', detail: parsed.error.flatten() });
    }
    const { employee_id: employeeId, password } = parsed.data;

    // 1. Find officer
    const officer = await prisma.officer.findUnique({
      where: { employeeId },
      include: { location: true },
    });

    if (!officer) {
      await logAction(null, logAction.ACTIONS.LOGIN_FAILURE, { result: 'account_not_found', req });
      return res.status(401).json({
        error: 'invalid_credentials',
        detail: 'Invalid employee ID or password.',
      });
    }

    // 2. Check lockout
    if (officer.lockedUntil && officer.lockedUntil > new Date()) {
      await logAction(officer, logAction.ACTIONS.LOGIN_LOCKED, { result: 'locked', req });
      const remaining = Math.ceil((officer.lockedUntil - Date.now()) / 60000);
      return res.status(403).json({
        error: 'account_locked',
        detail: `Account locked. Try again in ${remaining} minute(s).`,
        locked_until: officer.lockedUntil,
      });
    }

    // 3. Verify password
    const passwordOk = await bcrypt.compare(password, officer.passwordHash);
    if (!passwordOk || !officer.isActive) {
      const newAttempts = officer.failedLoginAttempts + 1;
      const lockData    = newAttempts >= cfg.auth.maxFailedAttempts
        ? { lockedUntil: new Date(Date.now() + cfg.auth.lockoutMinutes * 60_000) }
        : {};
      await prisma.officer.update({
        where: { id: officer.id },
        data: { failedLoginAttempts: newAttempts, ...lockData },
      });
      await logAction(officer, logAction.ACTIONS.LOGIN_FAILURE, { result: 'wrong_password', req });
      const remaining = Math.max(0, cfg.auth.maxFailedAttempts - newAttempts);
      return res.status(401).json({
        error: 'invalid_credentials',
        detail: 'Invalid employee ID or password.',
        remaining_attempts: remaining,
      });
    }

    // 4. Success — reset lockout, update last_login
    await prisma.officer.update({
      where: { id: officer.id },
      data: { failedLoginAttempts: 0, lockedUntil: null, lastLogin: new Date() },
    });

    const access            = jwtLib.signAccess(officer);
    const { token: refresh, jti } = jwtLib.signRefresh(officer);

    await logAction(officer, logAction.ACTIONS.LOGIN_SUCCESS, { result: 'success', req });

    return res.json({
      access,
      refresh,
      officer: officerProfile({ ...officer }),
    });
  } catch (err) { next(err); }
});

// ── POST /api/auth/refresh/ ───────────────────────────────────────────────────

router.post('/refresh/', async (req, res, next) => {
  try {
    const { refresh } = req.body;
    if (!refresh) {
      return res.status(400).json({ error: 'refresh_required', detail: 'Refresh token is required.' });
    }

    let payload;
    try {
      payload = jwtLib.verify(refresh);
    } catch {
      return res.status(401).json({ error: 'invalid_token', detail: 'Refresh token is invalid or expired.' });
    }

    // Check blacklist
    if (await jwtLib.isBlacklisted(payload.jti)) {
      return res.status(401).json({ error: 'token_blacklisted', detail: 'Refresh token has already been used.' });
    }

    // Blacklist old token (rotation)
    await jwtLib.blacklist(payload.jti, payload.exp);

    const officer = await prisma.officer.findUnique({ where: { id: parseInt(payload.sub, 10) } });
    if (!officer || !officer.isActive) {
      return res.status(401).json({ error: 'unauthorized', detail: 'Account inactive.' });
    }

    const access                    = jwtLib.signAccess(officer);
    const { token: newRefresh }     = jwtLib.signRefresh(officer);

    return res.json({ access, refresh: newRefresh });
  } catch (err) { next(err); }
});

// ── POST /api/auth/logout/ ────────────────────────────────────────────────────

router.post('/logout/', authenticate, async (req, res, next) => {
  try {
    const { refresh } = req.body;
    if (!refresh) {
      return res.status(400).json({ error: 'refresh_required', detail: 'Refresh token is required.' });
    }

    let payload;
    try {
      payload = jwtLib.verify(refresh);
    } catch {
      return res.status(400).json({ error: 'invalid_token', detail: 'Refresh token is invalid.' });
    }

    if (!(await jwtLib.isBlacklisted(payload.jti))) {
      await jwtLib.blacklist(payload.jti, payload.exp);
    }

    await logAction(req.officer, logAction.ACTIONS.LOGOUT, { result: 'success', req });
    return res.json({ detail: 'Logged out successfully.' });
  } catch (err) { next(err); }
});

// ── GET /api/auth/me/ ─────────────────────────────────────────────────────────

router.get('/me/', authenticate, (req, res) => {
  res.json(officerProfile(req.officer));
});

module.exports = router;

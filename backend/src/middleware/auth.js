// ParkiPay — JWT auth middleware + role guards  (Redis-cached officer lookup)
const { verify }  = require('../lib/jwt');
const prisma      = require('../lib/prisma');
const redis       = require('../lib/redis');

const OFFICER_TTL = 300; // 5 min

/**
 * authenticate
 * Verifies Bearer token. Reads officer from Redis cache first; falls back to
 * Postgres and re-populates the cache. Attaches full Officer row to req.officer.
 */
async function authenticate(req, res, next) {
  const header = req.headers['authorization'] || '';
  const token  = header.startsWith('Bearer ') ? header.slice(7).trim() : null;

  if (!token) {
    return res.status(401).json({ error: 'unauthorized', detail: 'No token provided.' });
  }

  try {
    const payload  = verify(token);
    const officerId = parseInt(payload.sub, 10);

    // ── Try Redis cache first ─────────────────────────────────────────────
    const cacheKey = `officer:${officerId}`;
    let officer = await redis.cacheGet(cacheKey);

    if (!officer) {
      officer = await prisma.officer.findUnique({
        where:   { id: officerId },
        include: { location: true },
      });
      if (officer) {
        await redis.cacheSet(cacheKey, officer, OFFICER_TTL);
      }
    }

    if (!officer || !officer.isActive) {
      return res.status(401).json({ error: 'unauthorized', detail: 'Account inactive or not found.' });
    }

    req.officer = officer;
    return next();
  } catch (_err) {
    return res.status(401).json({ error: 'unauthorized', detail: 'Invalid or expired token.' });
  }
}

function requireRole(...roles) {
  return (req, res, next) => {
    if (!req.officer || !roles.includes(req.officer.role)) {
      return res.status(403).json({ error: 'forbidden', detail: 'Insufficient permissions.' });
    }
    return next();
  };
}

const isSupervisor = requireRole('SUPERVISOR', 'ADMIN');
const isAdmin      = requireRole('ADMIN');

module.exports = { authenticate, requireRole, isSupervisor, isAdmin };

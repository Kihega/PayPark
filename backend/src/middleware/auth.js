// ParkiPay — JWT auth middleware + role guards
const { verify }  = require('../lib/jwt');
const prisma      = require('../lib/prisma');

/**
 * authenticate
 * Verifies the Bearer access token in the Authorization header and attaches
 * the full Officer row (with location) to req.officer.
 * Responds with 401 on any failure — never calls next(err).
 */
async function authenticate(req, res, next) {
  const header = req.headers['authorization'] || '';
  const token  = header.startsWith('Bearer ') ? header.slice(7).trim() : null;

  if (!token) {
    return res.status(401).json({ error: 'unauthorized', detail: 'No token provided.' });
  }

  try {
    const payload = verify(token);

    const officer = await prisma.officer.findUnique({
      where:   { id: parseInt(payload.sub, 10) },
      include: { location: true },
    });

    if (!officer || !officer.isActive) {
      return res.status(401).json({ error: 'unauthorized', detail: 'Account inactive or not found.' });
    }

    req.officer = officer;
    return next();
  } catch (_err) {
    return res.status(401).json({ error: 'unauthorized', detail: 'Invalid or expired token.' });
  }
}

/**
 * requireRole
 * Factory that returns a middleware enforcing role membership.
 * Must be chained AFTER authenticate.
 *
 * @param {...string} roles  Allowed role strings
 * @returns {Function} Express middleware
 */
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

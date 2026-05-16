// ParkiPay — JWT auth middleware + role guards
const { verify, isBlacklisted } = require('../lib/jwt');
const prisma = require('../lib/prisma');

/**
 * authenticate — verifies the Bearer access token and attaches req.officer
 */
async function authenticate(req, res, next) {
  const header = req.headers['authorization'] || '';
  const token  = header.startsWith('Bearer ') ? header.slice(7) : null;

  if (!token) {
    return res.status(401).json({ error: 'unauthorized', detail: 'No token provided.' });
  }

  try {
    const payload = verify(token);
    const officer = await prisma.officer.findUnique({
      where: { id: parseInt(payload.sub, 10) },
      include: { location: true },
    });

    if (!officer || !officer.isActive) {
      return res.status(401).json({ error: 'unauthorized', detail: 'Account inactive or not found.' });
    }

    req.officer = officer;
    next();
  } catch (err) {
    return res.status(401).json({ error: 'unauthorized', detail: 'Invalid or expired token.' });
  }
}

/**
 * requireRole — factory that returns a middleware checking officer.role
 */
function requireRole(...roles) {
  return (req, res, next) => {
    if (!roles.includes(req.officer?.role)) {
      return res.status(403).json({ error: 'forbidden', detail: 'Insufficient permissions.' });
    }
    next();
  };
}

const isSupervisor = requireRole('SUPERVISOR', 'ADMIN');
const isAdmin      = requireRole('ADMIN');

module.exports = { authenticate, requireRole, isSupervisor, isAdmin };

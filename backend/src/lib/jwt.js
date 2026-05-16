// ParkiPay — JWT helpers (access + refresh with rotation & blacklist)
const jwt  = require('jsonwebtoken');
const { v4: uuidv4 } = require('uuid');
const cfg    = require('../config');
const prisma = require('./prisma');

/**
 * Sign an access token — embeds role for fast permission checks.
 */
function signAccess(officer) {
  return jwt.sign(
    {
      sub:        String(officer.id),
      employeeId: officer.employeeId,
      fullName:   officer.fullName,
      role:       officer.role,
    },
    cfg.jwt.secret,
    { expiresIn: cfg.jwt.accessExpiresIn },
  );
}

/**
 * Sign a refresh token — includes a unique jti so it can be blacklisted.
 */
function signRefresh(officer) {
  const jti = uuidv4();
  const token = jwt.sign(
    { sub: String(officer.id), jti },
    cfg.jwt.secret,
    { expiresIn: cfg.jwt.refreshExpiresIn },
  );
  return { token, jti };
}

/**
 * Verify any token. Throws if invalid or expired.
 */
function verify(token) {
  return jwt.verify(token, cfg.jwt.secret);
}

/**
 * Blacklist a refresh token (prevents reuse after logout / rotation).
 */
async function blacklist(jti, expiresAt) {
  await prisma.blacklistedToken.create({ data: { jti, expiresAt: new Date(expiresAt * 1000) } });
}

/**
 * Returns true if the jti is blacklisted.
 */
async function isBlacklisted(jti) {
  const found = await prisma.blacklistedToken.findUnique({ where: { jti } });
  return Boolean(found);
}

module.exports = { signAccess, signRefresh, verify, blacklist, isBlacklisted };

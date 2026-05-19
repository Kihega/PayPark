// ParkiPay — JWT helpers
// Access tokens: short-lived (60 min), embed role for fast permission checks.
// Refresh tokens: long-lived (7 days), include a unique jti (UUID) so they
//   can be individually blacklisted on logout or rotation.
const jwt             = require('jsonwebtoken');
const { v4: uuidv4 } = require('uuid');
const cfg             = require('../config');
const prisma          = require('./prisma');

/**
 * Sign an access token for the given officer.
 * @param {object} officer  Prisma Officer row
 * @returns {string}        Signed JWT string
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
 * Sign a refresh token for the given officer.
 * @param {object} officer  Prisma Officer row
 * @returns {{ token: string, jti: string }}
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
 * Verify any token — throws JsonWebTokenError or TokenExpiredError on failure.
 * @param {string} token
 * @returns {object} decoded payload
 */
function verify(token) {
  return jwt.verify(token, cfg.jwt.secret);
}

/**
 * Persist a refresh token jti to the blacklist so it cannot be reused.
 * @param {string} jti       UUID from token payload
 * @param {number} expiresAt Unix timestamp (seconds) from payload.exp
 */
async function blacklist(jti, expiresAt) {
  await prisma.blacklistedToken.create({
    data: { jti, expiresAt: new Date(expiresAt * 1000) },
  });
}

/**
 * Returns true if the jti is in the blacklist (token already used/revoked).
 * @param {string} jti
 * @returns {Promise<boolean>}
 */
async function isBlacklisted(jti) {
  const found = await prisma.blacklistedToken.findUnique({ where: { jti } });
  return Boolean(found);
}

module.exports = { signAccess, signRefresh, verify, blacklist, isBlacklisted };

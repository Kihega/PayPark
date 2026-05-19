// ParkiPay — Control number generation + duplicate prevention
const prisma = require('./prisma');

/**
 * Generate a human-readable, unique-enough control number.
 * Format: PKP-YYYYMMDD-XXXXXX   e.g. PKP-20260517-A3F9K2
 *
 * The random component gives 36^6 ≈ 2.1 billion combinations per day,
 * which is more than sufficient for this use case. Uniqueness is enforced
 * at the DB level via a @unique constraint on controlNumber.
 *
 * @returns {string}
 */
function generateControlNumber() {
  const date   = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  const chars  = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  const random = Array.from(
    { length: 6 },
    () => chars[Math.floor(Math.random() * chars.length)],
  ).join('');
  return `PKP-${date}-${random}`;
}

/**
 * THE central duplicate-prevention query.
 *
 * Returns the single ACTIVE ControlNumber for a plate number across ALL
 * officers and ALL locations, or null if none exists.
 *
 * Any bill-generation request MUST call this first. If a non-null result
 * is returned, the caller MUST reject the request with HTTP 409.
 *
 * @param {string} plateNumber  Raw plate string (already normalised by caller)
 * @returns {Promise<object|null>}  Prisma ControlNumber row with relations
 */
async function getActiveBillForPlate(plateNumber) {
  return prisma.controlNumber.findFirst({
    where: {
      plateNumber: {
        equals: plateNumber.trim().toUpperCase(),
        mode:   'insensitive',
      },
      status:    'ACTIVE',
      expiresAt: { gt: new Date() },
    },
    include: { officer: true, location: true, vehicle: true },
  });
}

module.exports = { generateControlNumber, getActiveBillForPlate };

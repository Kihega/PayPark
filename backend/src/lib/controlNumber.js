// ParkiPay — Control number generation + duplicate prevention
const prisma = require('./prisma');

/**
 * Generate a human-readable control number.
 * Format: PKP-YYYYMMDD-XXXXXX  e.g. PKP-20260515-A3F9K2
 */
function generateControlNumber() {
  const now = new Date();
  const date = now.toISOString().slice(0, 10).replace(/-/g, '');
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  const random = Array.from({ length: 6 }, () => chars[Math.floor(Math.random() * chars.length)]).join('');
  return `PKP-${date}-${random}`;
}

/**
 * THE central duplicate-prevention query.
 * Returns the single ACTIVE ControlNumber for a plate across ALL officers
 * and ALL locations, or null if no active bill exists.
 */
async function getActiveBillForPlate(plateNumber) {
  return prisma.controlNumber.findFirst({
    where: {
      plateNumber: { equals: plateNumber.trim().toUpperCase(), mode: 'insensitive' },
      status: 'ACTIVE',
      expiresAt: { gt: new Date() },
    },
    include: { officer: true, location: true, vehicle: true },
  });
}

module.exports = { generateControlNumber, getActiveBillForPlate };

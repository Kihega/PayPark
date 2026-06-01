// ParkiPay — Control number generation + duplicate prevention
// Format: 11 pure digits  e.g. 20260522743  (YYYYMMDD + 3 random digits)
const prisma = require('./prisma');
const cfg    = require('../config');

function generateControlNumber() {
  const d    = new Date();
  const yyyy = String(d.getFullYear());
  const mm   = String(d.getMonth() + 1).padStart(2, '0');
  const dd   = String(d.getDate()).padStart(2, '0');
  const rand = String(Math.floor(Math.random() * 1000)).padStart(3, '0');
  return `${yyyy}${mm}${dd}${rand}`.replace(/\D/g, '').slice(0, 11).padStart(11, '0');
}

/**
 * Check if a duplicate bill should be blocked.
 *
 * A bill is considered a duplicate when BOTH conditions are true:
 *   1. Same plateNumber  (case-insensitive)
 *   2. Same locationId
 *   3. The bill was generated within the last BILLING_COOLDOWN_MINUTES minutes
 *
 * This allows the SAME vehicle to be billed at DIFFERENT locations without
 * triggering a duplicate, and allows re-billing after the cooldown.
 */
async function getActiveBillForPlate(plateNumber, locationId = null) {
  const cooldownMs  = (cfg.billing.cooldownMinutes ?? 1) * 60 * 1000;
  const cutoffTime  = new Date(Date.now() - cooldownMs);

  const where = {
    plateNumber: { equals: plateNumber.trim().toUpperCase(), mode: 'insensitive' },
    status:      'ACTIVE',
    generatedAt: { gte: cutoffTime },   // within cooldown window
  };

  // If locationId provided, also match location (same plate, different location = OK)
  if (locationId) {
    where.locationId = locationId;
  }

  return prisma.controlNumber.findFirst({
    where,
    include: { officer: true, location: true, vehicle: true },
    orderBy: { generatedAt: 'desc' },
  });
}

module.exports = { generateControlNumber, getActiveBillForPlate };

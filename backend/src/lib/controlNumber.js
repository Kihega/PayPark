// ParkiPay — Control number generation
// Format: 11 pure digits (no letters ever)
// Structure: YYYYMMDD (8) + 3 random digits = "20260522743"
const prisma = require('./prisma');

function generateControlNumber() {
  const d    = new Date();
  const yyyy = String(d.getFullYear());
  const mm   = String(d.getMonth() + 1).padStart(2, '0');
  const dd   = String(d.getDate()).padStart(2, '0');
  const rand = String(Math.floor(Math.random() * 1000)).padStart(3, '0');
  const cn   = `${yyyy}${mm}${dd}${rand}`;
  // Defensive: strip any non-digit character (belt-and-suspenders)
  const numeric = cn.replace(/\D/g, '').slice(0, 11).padStart(11, '0');
  return numeric;
}

async function getActiveBillForPlate(plateNumber) {
  return prisma.controlNumber.findFirst({
    where: {
      plateNumber: { equals: plateNumber.trim().toUpperCase(), mode: 'insensitive' },
      status:      'ACTIVE',
      expiresAt:   { gt: new Date() },
    },
    include: { officer: true, location: true, vehicle: true },
  });
}

module.exports = { generateControlNumber, getActiveBillForPlate };

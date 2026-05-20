/**
 * seed_biometrics.js
 * Seeds officer_biometrics with inactive placeholder tokens.
 * Uses DIRECT_URL (port 5432) to bypass pgBouncer prepared-statement limit.
 *
 * Run from backend/:
 *   node prisma/migrations/biometric/seed_biometrics.js
 */
require('dotenv').config();           // load .env from backend/
const { PrismaClient } = require('@prisma/client');
const crypto           = require('crypto');

// Force the direct connection — pgBouncer (pooler) rejects prepared statements
const directUrl = process.env.DIRECT_URL || process.env.DATABASE_URL;
if (!directUrl) {
  console.error('❌  Set DIRECT_URL (or DATABASE_URL) in backend/.env');
  process.exit(1);
}

const prisma = new PrismaClient({
  datasources: { db: { url: directUrl } },
});

async function main() {
  const officers = await prisma.officer.findMany({ where: { isActive: true } });

  if (!officers.length) {
    console.log('No active officers found — make sure the seed SQL ran first.');
    return;
  }

  console.log(`Seeding biometrics for ${officers.length} officer(s)…`);

  for (const officer of officers) {
    const token = crypto.randomBytes(32).toString('hex');   // 64 hex chars

    // Use queryRaw instead of executeRaw to avoid the prepared-statement cache
    await prisma.$queryRawUnsafe(`
      INSERT INTO officer_biometrics (officer_id, token, device_hint, is_active, created_at, updated_at)
      VALUES ($1, $2, $3, false, NOW(), NOW())
      ON CONFLICT (officer_id) DO NOTHING
    `, officer.id, token, 'seed_device');

    console.log(`  ✓ ${officer.employeeId} (id=${officer.id}) → token seeded (is_active=false)`);
  }

  console.log('\nDone. Tokens are inactive until the officer enrols from the app.');
  console.log('Real tokens are generated on-device via expo-local-authentication.');
}

main().catch(console.error).finally(() => prisma.$disconnect());

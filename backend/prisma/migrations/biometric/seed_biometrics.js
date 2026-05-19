/**
 * seed_biometrics.js
 * Seed the officer_biometrics table with test rows for local development.
 * Run from backend/:   node prisma/migrations/biometric/seed_biometrics.js
 */
const { PrismaClient } = require('@prisma/client');
const crypto           = require('crypto');

const prisma = new PrismaClient();

async function main() {
  const officers = await prisma.officer.findMany({ where: { isActive: true } });
  console.log(`Seeding biometrics for ${officers.length} officer(s)…`);

  for (const officer of officers) {
    // Generate a random token (same length as the device would)
    const token = crypto.randomBytes(32).toString('hex');

    await prisma.$executeRaw`
      INSERT INTO officer_biometrics (officer_id, token, device_hint, is_active, created_at, updated_at)
      VALUES (
        ${officer.id},
        ${token},
        ${'seed_device'},
        false,
        NOW(),
        NOW()
      )
      ON CONFLICT (officer_id) DO NOTHING
    `;
    console.log(`  officer ${officer.employeeId} → token seeded (is_active=false)`);
  }
  console.log('Done. Tokens are inactive until the officer enrols from the app.');
}

main().catch(console.error).finally(() => prisma.$disconnect());

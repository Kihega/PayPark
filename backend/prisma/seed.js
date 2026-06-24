// ParkiPay — Development seed data
// Creates test users, a sample parking location, and a sample vehicle.
//
// ╔═══════════════════════════════════════════════════════════╗
// ║                   TEST USER CREDENTIALS                   ║
// ╠═══════════════════╦═════════════╦═════════════════════════╣
// ║ Role              ║ Employee ID ║ Password                ║
// ╠═══════════════════╬═════════════╬═════════════════════════╣
// ║ Attendant         ║ TZ-0001     ║ Officer@1234            ║
// ║ Supervisor        ║ SUP-0001    ║ Supervisor@1234         ║
// ╚═══════════════════╩═════════════╩═════════════════════════╝
//
// Run:  npm run db:seed

const { PrismaClient } = require('@prisma/client');
const bcrypt           = require('bcryptjs');

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Seeding development data...');

  // ── Parking location ──────────────────────────────────────────────────────
  const dar = await prisma.parkingLocation.upsert({
    where:  { id: 1 },
    update: {},
    create: {
      id:            1,
      name:          'Kariakoo Bus Stand',
      region:        'Dar es Salaam',
      district:      'Ilala',
      feeMotorcycle: 500,
      feePrivateCar: 1000,
      feeMinibus:    2000,
      feeBus:        3000,
      feeTruck:      5000,
      feeGovernment: 0,
    },
  });
  console.log(`  ✅ Location: ${dar.name}`);

  // ── Sample vehicle ────────────────────────────────────────────────────────
  const vehicle = await prisma.vehicle.upsert({
    where:  { plateNumber: 'TZ001ABC' },
    update: {},
    create: {
      plateNumber: 'TZ001ABC',
      ownerName:   'Juma Hassan',
      ownerPhone:  '+255712345678',
      ownerEmail:  'juma.hassan@example.com',
      make:        'Toyota',
      model:       'Corolla',
      color:       'White',
      year:        2018,
      category:    'PRIVATE_CAR',
    },
  });
  console.log(`  ✅ Sample vehicle: ${vehicle.plateNumber} (${vehicle.ownerName})`);

  // ── Supervisor (test, SUP-XXXX format) ───────────────────────────────────
  const supervisor = await prisma.officer.upsert({
    where:  { employeeId: 'SUP-0001' },
    update: {},
    create: {
      employeeId:   'SUP-0001',
      fullName:     'Test Supervisor',
      phone:        '+255700000002',
      email:        'supervisor@parkipay.go.tz',
      role:         'SUPERVISOR',
      passwordHash: await bcrypt.hash('Supervisor@1234', 12),
      locationId:   dar.id,
    },
  });
  console.log(`  ✅ Supervisor: ${supervisor.employeeId} (password: Supervisor@1234)`);

  // ── Field officer (TZ-XXXX format) ───────────────────────────────────────
  const attendant = await prisma.officer.upsert({
    where:  { employeeId: 'TZ-0001' },
    update: {},
    create: {
      employeeId:   'TZ-0001',
      fullName:     'John Mwangi',
      phone:        '+255712345678',
      email:        'j.mwangi@parkipay.go.tz',
      role:         'ATTENDANT',
      passwordHash: await bcrypt.hash('Officer@1234', 12),
      locationId:   dar.id,
    },
  });
  console.log(`  ✅ Attendant: ${attendant.employeeId} (password: Officer@1234)`);

  console.log('\n🎉 Seed complete. You can log in with:');
  console.log('   Attendant:   TZ-0001    / Officer@1234');
  console.log('   Supervisor:  SUP-0001   / Supervisor@1234');
}

main()
  .catch((err) => {
    console.error('❌ Seed failed:', err);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());

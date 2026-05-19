// ParkiPay — Development seed data
// Creates test users, a sample parking location, and a sample vehicle.
//
// ╔═══════════════════════════════════════════════════════════╗
// ║                   TEST USER CREDENTIALS                   ║
// ╠═══════════════════╦═════════════╦═════════════════════════╣
// ║ Role              ║ Employee ID ║ Password                ║
// ╠═══════════════════╬═════════════╬═════════════════════════╣
// ║ Admin             ║ ADMIN001    ║ Admin@1234              ║
// ║ Field Officer     ║ OFF001      ║ Officer@1234            ║
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

  // ── Admin officer ─────────────────────────────────────────────────────────
  const admin = await prisma.officer.upsert({
    where:  { employeeId: 'ADMIN001' },
    update: {},
    create: {
      employeeId:   'ADMIN001',
      fullName:     'System Administrator',
      phone:        '+255700000001',
      email:        'admin@parkipay.go.tz',
      role:         'ADMIN',
      passwordHash: await bcrypt.hash('Admin@1234', 12),
      locationId:   dar.id,
    },
  });
  console.log(`  ✅ Admin officer: ${admin.employeeId} (password: Admin@1234)`);

  // ── Field officer ─────────────────────────────────────────────────────────
  const officer = await prisma.officer.upsert({
    where:  { employeeId: 'OFF001' },
    update: {},
    create: {
      employeeId:   'OFF001',
      fullName:     'John Mwangi',
      phone:        '+255712345678',
      email:        'j.mwangi@parkipay.go.tz',
      role:         'FIELD_OFFICER',
      passwordHash: await bcrypt.hash('Officer@1234', 12),
      locationId:   dar.id,
    },
  });
  console.log(`  ✅ Field officer: ${officer.employeeId} (password: Officer@1234)`);

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

  console.log('\n🎉 Seed complete. You can log in with:');
  console.log('   Admin:         ADMIN001   / Admin@1234');
  console.log('   Field Officer: OFF001     / Officer@1234');
}

main()
  .catch((err) => {
    console.error('❌ Seed failed:', err);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());

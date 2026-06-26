// ParkiPay — Development seed data
// Wipes existing data, then seeds 5 zones (5 parking locations each),
// two test officers, and one sample vehicle.
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

// 5 zones across different regions, each with 5 sample parking locations.
const ZONES = [
  {
    zoneName: 'Kinondoni Zone', region: 'Dar es Salaam', district: 'Kinondoni',
    locations: [
      'Kinondoni - Mwenge Bus Stand',
      'Kinondoni - Sinza Market',
      'Kinondoni - Magomeni Stand',
      'Kinondoni - Kawe Beach Parking',
      'Kinondoni - Makumbusho Terminal',
    ],
  },
  {
    zoneName: 'Ubungo Zone', region: 'Dar es Salaam', district: 'Ubungo',
    locations: [
      'Ubungo - Bus Terminal',
      'Ubungo - Kibo Stand',
      'Ubungo - Mabibo Market',
      'Ubungo - Manzese Stand',
      'Ubungo - Sayona Parking',
    ],
  },
  {
    zoneName: 'Temeke Zone', region: 'Dar es Salaam', district: 'Temeke',
    locations: [
      'Temeke - Mbagala Stand',
      'Temeke - Tandika Market',
      'Temeke - Buguruni Stand',
      'Temeke - Mtoni Parking',
      'Temeke - Chang\'ombe Terminal',
    ],
  },
  {
    zoneName: 'Ilala Zone', region: 'Dar es Salaam', district: 'Ilala',
    locations: [
      'Ilala - Kariakoo Bus Stand',
      'Ilala - Buguruni Market',
      'Ilala - Ilala Boma Parking',
      'Ilala - Tabata Stand',
      'Ilala - Segerea Terminal',
    ],
  },
  {
    zoneName: 'Kigamboni Zone', region: 'Dar es Salaam', district: 'Kigamboni',
    locations: [
      'Kigamboni - Ferry Terminal',
      'Kigamboni - Tungi Beach Parking',
      'Kigamboni - Mjimwema Stand',
      'Kigamboni - Kibada Market',
      'Kigamboni - Vijibweni Stand',
    ],
  },
];

async function main() {
  console.log('🌱 Seeding development data...');

  // ── 0. Clean slate — remove all previous seed/test data ────────────────────
  // Order matters: clear FK-dependent tables first.
  await prisma.controlNumber.deleteMany({});
  await prisma.auditLog.deleteMany({});
  await prisma.officerBiometric.deleteMany({});
  await prisma.officer.deleteMany({});
  await prisma.vehicle.deleteMany({});
  await prisma.parkingLocation.deleteMany({});
  console.log('  🧹 Cleared previous seed data');

  // ── 1. Zones + parking locations ────────────────────────────────────────────
  // Each zone is itself a ParkingLocation (used for supervisor assignment),
  // and each zone's sample stands/markets are ParkingLocations too (used
  // for attendant assignment). All locations are looked up live by the
  // mobile app's location dropdown via GET /api/admin/locations/.
  const zoneRecords = {};      // zoneName -> ParkingLocation row (the zone itself)
  const firstLocationByZone = {}; // zoneName -> first location row inside it

  for (const zone of ZONES) {
    const zoneRow = await prisma.parkingLocation.create({
      data: {
        name:          zone.zoneName,
        region:        zone.region,
        district:      zone.district,
        feeMotorcycle: 500, feePrivateCar: 1000, feeMinibus: 2000,
        feeBus: 3000, feeTruck: 5000, feeGovernment: 0,
      },
    });
    zoneRecords[zone.zoneName] = zoneRow;
    console.log(`  ✅ Zone: ${zoneRow.name} (${zone.region})`);

    for (const locName of zone.locations) {
      const loc = await prisma.parkingLocation.create({
        data: {
          name:          locName,
          region:        zone.region,
          district:      zone.district,
          feeMotorcycle: 500, feePrivateCar: 1000, feeMinibus: 2000,
          feeBus: 3000, feeTruck: 5000, feeGovernment: 0,
        },
      });
      if (!firstLocationByZone[zone.zoneName]) firstLocationByZone[zone.zoneName] = loc;
      console.log(`     • ${loc.name}`);
    }
  }

  // ── 2. Sample vehicle ────────────────────────────────────────────────────────
  const vehicle = await prisma.vehicle.create({
    data: {
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

  // ── 3. Supervisor (test, SUP-XXXX format) — assigned to Kinondoni Zone ──────
  const supervisor = await prisma.officer.create({
    data: {
      employeeId:   'SUP-0001',
      fullName:     'Test Supervisor',
      phone:        '+255700000002',
      email:        'supervisor@parkipay.go.tz',
      role:         'SUPERVISOR',
      passwordHash: await bcrypt.hash('Supervisor@1234', 12),
      locationId:   zoneRecords['Kinondoni Zone'].id,
    },
  });
  console.log(`  ✅ Supervisor: ${supervisor.employeeId} (password: Supervisor@1234) -> Kinondoni Zone`);

  // ── 4. Attendant (TZ-XXXX format) — assigned to a stand inside Kinondoni ───
  const attendantLocation = firstLocationByZone['Kinondoni Zone'];
  const attendant = await prisma.officer.create({
    data: {
      employeeId:   'TZ-0001',
      fullName:     'John Mwangi',
      phone:        '+255712345678',
      email:        'j.mwangi@parkipay.go.tz',
      role:         'ATTENDANT',
      passwordHash: await bcrypt.hash('Officer@1234', 12),
      locationId:   attendantLocation.id,
    },
  });
  console.log(`  ✅ Attendant: ${attendant.employeeId} (password: Officer@1234) -> ${attendantLocation.name}`);

  console.log('\n🎉 Seed complete. You can log in with:');
  console.log('   Attendant:   TZ-0001    / Officer@1234');
  console.log('   Supervisor:  SUP-0001   / Supervisor@1234');
  console.log(`\n   Seeded ${ZONES.length} zones x 5 locations each = ${ZONES.length * 5} parking locations.`);
}

main()
  .catch((err) => {
    console.error('❌ Seed failed:', err);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());

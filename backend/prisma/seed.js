// ParkiPay — Dev seed data (mirrors Django seed_dev_data command)
const { PrismaClient } = require('@prisma/client');
const bcrypt = require('bcryptjs');

const prisma = new PrismaClient();

async function main() {
  console.log('Seeding dev data...');

  // Parking locations
  const dar = await prisma.parkingLocation.upsert({
    where: { id: 1 },
    update: {},
    create: {
      name: 'Kariakoo Bus Stand',
      region: 'Dar es Salaam',
      district: 'Ilala',
      feeMotorcycle: 500,
      feePrivateCar: 1000,
      feeMinibus: 2000,
      feeBus: 3000,
      feeTruck: 5000,
      feeGovernment: 0,
    },
  });

  // Admin officer
  await prisma.officer.upsert({
    where: { employeeId: 'ADMIN001' },
    update: {},
    create: {
      employeeId: 'ADMIN001',
      fullName: 'System Administrator',
      role: 'ADMIN',
      passwordHash: await bcrypt.hash('Admin@1234', 12),
      locationId: dar.id,
    },
  });

  // Field officer
  await prisma.officer.upsert({
    where: { employeeId: 'OFF001' },
    update: {},
    create: {
      employeeId: 'OFF001',
      fullName: 'John Mwangi',
      role: 'FIELD_OFFICER',
      passwordHash: await bcrypt.hash('Officer@1234', 12),
      locationId: dar.id,
    },
  });

  // Sample vehicle
  await prisma.vehicle.upsert({
    where: { plateNumber: 'TZ001ABC' },
    update: {},
    create: {
      plateNumber: 'TZ001ABC',
      ownerName: 'Juma Hassan',
      ownerPhone: '+255712345678',
      make: 'Toyota',
      model: 'Corolla',
      color: 'White',
      year: 2018,
      category: 'PRIVATE_CAR',
    },
  });

  console.log('Seed complete.');
}

main()
  .catch(console.error)
  .finally(() => prisma.$disconnect());

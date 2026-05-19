// ParkiPay — Singleton Prisma client
// Import this module everywhere — Node caches require() so there is only
// ever one PrismaClient instance per process.
const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient({
  log: process.env.NODE_ENV === 'development'
    ? ['query', 'warn', 'error']
    : ['error'],
});

module.exports = prisma;

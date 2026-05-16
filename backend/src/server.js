// ParkiPay — HTTP server entry point
const app    = require('./app');
const cfg    = require('./config');
const prisma = require('./lib/prisma');

async function start() {
  // Verify DB connection before accepting traffic
  await prisma.$connect();
  console.log('Database connected.');

  app.listen(cfg.port, () => {
    console.log(`ParkiPay API running on port ${cfg.port} [${cfg.nodeEnv}]`);
  });
}

start().catch((err) => {
  console.error('Failed to start server:', err);
  process.exit(1);
});

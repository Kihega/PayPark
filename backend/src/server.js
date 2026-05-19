// ParkiPay — HTTP server entry point
// Validates the DB connection before accepting traffic, then starts listening.
const app    = require('./app');
const cfg    = require('./config');
const prisma = require('./lib/prisma');

async function start() {
  // Verify database is reachable before opening the HTTP port
  await prisma.$connect();
  console.log('✅ Database connected.');

  const server = app.listen(cfg.port, () => {
    console.log(`🚀 ParkiPay API running on port ${cfg.port} [${cfg.nodeEnv}]`);
  });

  // Graceful shutdown — finish in-flight requests before closing
  const shutdown = async (signal) => {
    console.log(`\n${signal} received — shutting down gracefully...`);
    server.close(async () => {
      await prisma.$disconnect();
      console.log('Database disconnected. Bye.');
      process.exit(0);
    });
  };

  process.on('SIGTERM', () => shutdown('SIGTERM'));
  process.on('SIGINT',  () => shutdown('SIGINT'));
}

start().catch((err) => {
  console.error('❌ Failed to start server:', err);
  process.exit(1);
});

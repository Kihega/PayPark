// ParkiPay — HTTP server entry point
// Validates DB connection before accepting traffic, then starts listening.

const app = require('./app');
const cfg = require('./config');
const prisma = require('./lib/prisma');

async function start() {
  try {
    console.log('🔄 Connecting to database...');

    // Verify database is reachable before opening HTTP port
    await prisma.$connect();

    console.log('✅ Database connected.');

    // IMPORTANT: bind to 0.0.0.0 for Render
    const server = app.listen(cfg.port, '0.0.0.0', () => {
      console.log(
        `🚀 ParkiPay API running on port ${cfg.port} [${cfg.nodeEnv}]`
      );
    });

    // Graceful shutdown
    const shutdown = async (signal) => {
      console.log(`\n${signal} received — shutting down gracefully...`);

      server.close(async () => {
        try {
          await prisma.$disconnect();
          console.log('✅ Database disconnected.');
          process.exit(0);
        } catch (err) {
          console.error('❌ Error disconnecting database:', err);
          process.exit(1);
        }
      });
    };

    process.on('SIGTERM', () => shutdown('SIGTERM'));
    process.on('SIGINT', () => shutdown('SIGINT'));

  } catch (err) {
    console.error('❌ Failed to start server:', err);
    process.exit(1);
  }
}

start();

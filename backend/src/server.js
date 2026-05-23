// ParkiPay — HTTP server entry point
const app    = require('./app');
const cfg    = require('./config');
const prisma = require('./lib/prisma');
const redis  = require('./lib/redis');

async function start() {
  try {
    // ── Database ──────────────────────────────────────────────────────────
    console.log('🔄 Connecting to database...');
    await prisma.$connect();
    console.log('✅ Database connected.');

    // ── Redis (optional — gracefully skipped if REDIS_URL not set) ────────
    if (cfg.redisUrl) {
      try {
        const client = await redis.getClient();
        if (client?.isReady) {
          console.log('✅ Redis connected.');
        } else {
          console.warn('⚠️  Redis client not ready — caching disabled.');
        }
      } catch (redisErr) {
        console.warn('⚠️  Redis connection failed:', redisErr.message, '— caching disabled.');
      }
    } else {
      console.log('ℹ️  REDIS_URL not set — running without cache.');
    }

    // ── HTTP Server ───────────────────────────────────────────────────────
    const server = app.listen(cfg.port, '0.0.0.0', () => {
      console.log(`🚀 ParkiPay API running on port ${cfg.port} [${cfg.nodeEnv}]`);
    });

    const shutdown = async (signal) => {
      console.log(`\n${signal} received — shutting down gracefully...`);
      server.close(async () => {
        try {
          await prisma.$disconnect();
          console.log('✅ Database disconnected.');
          process.exit(0);
        } catch (err) {
          console.error('❌ Error disconnecting:', err);
          process.exit(1);
        }
      });
    };

    process.on('SIGTERM', () => shutdown('SIGTERM'));
    process.on('SIGINT',  () => shutdown('SIGINT'));

  } catch (err) {
    console.error('❌ Failed to start server:', err);
    process.exit(1);
  }
}

start();

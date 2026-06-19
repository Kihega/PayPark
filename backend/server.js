// ParkiPay — HTTP server entry point

const app    = require('./app');
const cfg    = require('./config');
const prisma = require('./lib/prisma');
const redis  = require('./lib/redis');

function getBaseUrl(port) {
  if (cfg.nodeEnv === 'production' && process.env.RENDER_EXTERNAL_URL) {
    return process.env.RENDER_EXTERNAL_URL;
  }
  return `http://localhost:${port}`;
}

async function start() {
  try {
    console.log('🔄 Connecting to database...');
    await prisma.$connect();
    console.log('✅ Database connected.');

    if (cfg.redisUrl) {
      try {
        const client = await redis.getClient();
        if (client?.isReady) {
          console.log('✅ Redis connected.');
        } else {
          console.warn('⚠️ Redis not ready.');
        }
      } catch (err) {
        console.warn('⚠️ Redis error:', err.message);
      }
    }

    const server = app.listen(cfg.port, '0.0.0.0', () => {
      console.log('━━━━━━━━━━━━━━━━━━━━━━');
      console.log('🚀 ParkiPay API running');
      console.log(`🌍 Environment: ${cfg.nodeEnv}`);
      console.log(`🔗 Base URL: ${getBaseUrl(cfg.port)}`);
      console.log(`📡 Port: ${cfg.port}`);
      console.log('━━━━━━━━━━━━━━━━━━━━━━');
    });

    const shutdown = async (signal) => {
      console.log(`\n${signal} received — shutting down...`);

      server.close(async () => {
        await prisma.$disconnect();
        process.exit(0);
      });
    };

    process.on('SIGINT', () => shutdown('SIGINT'));
    process.on('SIGTERM', () => shutdown('SIGTERM'));

  } catch (err) {
    console.error('❌ Startup failed:', err);
    process.exit(1);
  }
}

start();

// ParkiPay — HTTP server entry point

const app    = require('./app');
const cfg    = require('./config');
const prisma = require('./lib/prisma');
const redis  = require('./lib/redis');

function getBaseUrl(port) {
  const isProd = cfg.nodeEnv === 'production';

  if (isProd && process.env.RENDER_EXTERNAL_URL) {
    return process.env.RENDER_EXTERNAL_URL;
  }

  if (isProd) {
    return `https://your-domain.com`; // fallback (optional)
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
          console.warn('⚠️ Redis not ready — caching disabled.');
        }
      } catch (err) {
        console.warn('⚠️ Redis connection failed:', err.message);
      }
    } else {
      console.log('ℹ️ Redis not configured — running without cache.');
    }

    const server = app.listen(cfg.port, '0.0.0.0', () => {
      const baseUrl = getBaseUrl(cfg.port);

      console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
      console.log(`🚀 ParkiPay API running`);
      console.log(`🌍 Environment: ${cfg.nodeEnv}`);
      console.log(`🔗 Base URL: ${baseUrl}`);
      console.log(`📡 Port: ${cfg.port}`);
      console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    });

    const shutdown = async (signal) => {
      console.log(`\n${signal} received — shutting down...`);

      server.close(async () => {
        try {
          await prisma.$disconnect();
          console.log('✅ Database disconnected.');
          process.exit(0);
        } catch (err) {
          console.error('❌ Shutdown error:', err);
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

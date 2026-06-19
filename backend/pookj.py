import os

ROOT = os.getcwd()

FILES = {
    "Dockerfile": r"""
# ── ParkiPay Backend — Production Image ─────────────────────────────────────

FROM node:20-alpine AS deps
WORKDIR /app

RUN apk add --no-cache openssl

COPY package*.json ./
COPY prisma ./prisma

RUN npm ci
RUN npx prisma generate
RUN npm prune --omit=dev


FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production

RUN apk add --no-cache openssl

RUN addgroup -S parkipay && adduser -S parkipay -G parkipay

COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/node_modules/.prisma ./node_modules/.prisma

COPY prisma ./prisma
COPY src ./src
COPY package*.json ./
COPY entrypoint.sh ./entrypoint.sh

RUN chmod +x ./entrypoint.sh && chown -R parkipay:parkipay /app

USER parkipay

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
""",

    "entrypoint.sh": r"""#!/bin/sh
# ParkiPay — Production Entrypoint

set -e

echo "==> Running database migrations..."
npx prisma migrate deploy

echo "==> Starting ParkiPay API..."
exec node src/server.js
""",

    "server.js": r"""
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
"""
}


def write_file(name, content):
    path = os.path.join(ROOT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"✔ rewritten {name}")


for file, content in FILES.items():
    write_file(file, content)

print("\n✅ All files rewritten successfully.")

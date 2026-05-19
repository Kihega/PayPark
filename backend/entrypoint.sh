#!/bin/sh
# ParkiPay — Docker Entrypoint (production)
# Runs Prisma migrations then starts the Node.js server.
# Using 'set -e' so any failure exits immediately with a non-zero code,
# which causes the container to restart (Render / Docker will see the failure).

set -e

echo "==> Syncing database schema..."
npx prisma db push --accept-data-loss

echo "==> Starting ParkiPay API..."
exec node src/server.js

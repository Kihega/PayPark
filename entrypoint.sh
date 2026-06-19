#!/bin/sh
# ParkiPay — Production Entrypoint

set -e

echo "==> Running database migrations..."
npx prisma migrate deploy

echo "==> Starting ParkiPay API..."
exec node src/server.js

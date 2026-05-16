#!/bin/sh
# ParkiPay — Docker Entrypoint (Express)
set -e

echo "==> Running Prisma migrations..."
npx prisma migrate deploy

echo "==> Starting server..."
exec node src/server.js

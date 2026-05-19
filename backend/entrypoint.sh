#!/bin/sh
# ParkiPay — Docker Entrypoint (production)
# Runs Prisma migrations then starts the Node.js server.
# Using 'set -e' so any failure exits immediately with a non-zero code,
# which causes the container to restart (Render / Docker will see the failure).
#!/bin/sh
set -e

echo "==> Generating Prisma client..."
npx prisma generate

echo "==> Starting ParkiPay API..."
exec node src/server.js

// GET /api/health/
// Used by Render health checks and mobile app connectivity check.
// No auth required.
const { Router } = require('express');
const prisma     = require('../lib/prisma');

const router = Router();

router.get('/', async (_req, res) => {
  // Ping the database so the health check reflects true system health
  let dbStatus = 'ok';
  try {
    await prisma.$queryRaw`SELECT 1`;
  } catch (_err) {
    dbStatus = 'error';
  }

  const status = dbStatus === 'ok' ? 'ok' : 'degraded';
  const code   = status === 'ok' ? 200 : 503;

  res.status(code).json({
    status,
    service:     'ParkiPay API',
    version:     '1.0.0',
    environment: process.env.NODE_ENV || 'development',
    database:    dbStatus,
    timestamp:   new Date().toISOString(),
  });
});

module.exports = router;

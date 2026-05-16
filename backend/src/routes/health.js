// GET /api/health/
const { Router } = require('express');
const router = Router();

router.get('/', (_req, res) => {
  res.json({
    status:      'ok',
    service:     'ParkiPay API',
    version:     '1.0.0',
    timestamp:   new Date().toISOString(),
    environment: process.env.NODE_ENV || 'development',
  });
});

module.exports = router;

// ParkiPay — Express app factory
const express     = require('express');
const helmet      = require('helmet');
const cors        = require('cors');
const morgan      = require('morgan');
const rateLimit   = require('express-rate-limit');
const errorHandler = require('./middleware/errorHandler');

const app = express();

// ── Security & Parsing ────────────────────────────────────────────────────────
app.set('trust proxy', 1);
app.use(helmet());
app.use(cors());
app.use(express.json());
app.use(morgan(process.env.NODE_ENV === 'production' ? 'combined' : 'dev'));

// ── Rate limiting ─────────────────────────────────────────────────────────────
app.use('/api/auth/login/', rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 20,
  message: { error: 'too_many_requests', detail: 'Too many login attempts. Try again later.' },
}));

// ── Routes ────────────────────────────────────────────────────────────────────
app.use('/api/health/',   require('./routes/health'));
app.use('/api/auth/',     require('./routes/auth'));
app.use('/api/vehicles/', require('./routes/vehicles'));
app.use('/api/billing/',  require('./routes/billing'));

// ── 404 ───────────────────────────────────────────────────────────────────────
app.use((_req, res) => res.status(404).json({ error: 'not_found', detail: 'Endpoint not found.' }));

// ── Error handler ─────────────────────────────────────────────────────────────
app.use(errorHandler);

module.exports = app;

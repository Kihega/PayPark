// ParkiPay — Express app factory
// Separated from server.js so tests can import the app without starting
// the HTTP server or opening a DB connection.
const express      = require('express');
const helmet       = require('helmet');
const cors         = require('cors');
const morgan       = require('morgan');
const rateLimit    = require('express-rate-limit');
const errorHandler = require('./middleware/errorHandler');

const app = express();

// ── Security & Parsing ────────────────────────────────────────────────────────
app.set('trust proxy', 1); // Trust first proxy (required on Render / Railway)
app.use(helmet());
app.use(cors());
app.use(express.json());

// Log HTTP requests — 'combined' format in prod (parseable by log aggregators),
// 'dev' format locally for human-readable coloured output.
app.use(morgan(process.env.NODE_ENV === 'production' ? 'combined' : 'dev'));

// ── Rate limiting ─────────────────────────────────────────────────────────────
app.use(
  '/api/auth/login/',
  rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max:      20,
    standardHeaders: true,
    legacyHeaders:   false,
    message: {
      error:  'too_many_requests',
      detail: 'Too many login attempts. Try again later.',
    },
  }),
);

// ── Routes ────────────────────────────────────────────────────────────────────
app.use('/api/health/',   require('./routes/health'));
app.use('/api/auth/',     require('./routes/auth'));
app.use('/api/vehicles/', require('./routes/vehicles'));
app.use('/api/billing/',  require('./routes/billing'));

// ── 404 ───────────────────────────────────────────────────────────────────────
app.use((_req, res) =>
  res.status(404).json({ error: 'not_found', detail: 'Endpoint not found.' }),
);

// ── Global error handler (must be last) ──────────────────────────────────────
app.use(errorHandler);

module.exports = app;

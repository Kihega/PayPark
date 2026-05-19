// ParkiPay — Central config
// Reads every environment variable used in the project.
// Variable names match the real .env file exactly.
// Fails fast in production if required vars are missing.
require('dotenv').config();

function required(key) {
  const val = process.env[key];
  if (!val && process.env.NODE_ENV === 'production') {
    throw new Error(`Missing required environment variable: ${key}`);
  }
  return val || '';
}

const cfg = {
  // ── Server ────────────────────────────────────────────────────────────────
  nodeEnv:      process.env.NODE_ENV       || 'development',
  port:         parseInt(process.env.PORT  || '8000', 10),
  isProduction: process.env.NODE_ENV       === 'production',
  isTest:       process.env.NODE_ENV       === 'test',
  debug:        process.env.DEBUG          === 'True',
  allowedHosts: process.env.ALLOWED_HOSTS  || 'http://localhost:8000',

  // ── Security / JWT ────────────────────────────────────────────────────────
  // SECRET_KEY from .env is used as the JWT signing secret.
  // Also supports legacy JWT_SECRET name for local dev.
  jwt: {
    secret: process.env.SECRET_KEY
         || process.env.JWT_SECRET
         || 'dev-secret-CHANGE-IN-PRODUCTION',

    // Support both naming conventions from .env
    accessExpiresIn:  process.env.JWT_ACCESS_EXPIRES_IN
                   || `${process.env.JWT_ACCESS_TOKEN_LIFETIME_MINUTES || 60}m`,

    refreshExpiresIn: process.env.JWT_REFRESH_EXPIRES_IN
                   || `${process.env.JWT_REFRESH_TOKEN_LIFETIME_DAYS || 7}d`,
  },

  // ── CORS ──────────────────────────────────────────────────────────────────
  // Comma-separated string → array
  corsOrigins: (process.env.CORS_ALLOWED_ORIGINS || 'http://localhost:8081')
    .split(',')
    .map((o) => o.trim())
    .filter(Boolean),

  // ── Auth Policy ───────────────────────────────────────────────────────────
  auth: {
    // .env uses MAX_FAILED_LOGIN_ATTEMPT (no S) — support both
    maxFailedAttempts: parseInt(
      process.env.MAX_FAILED_LOGIN_ATTEMPT
      || process.env.MAX_FAILED_LOGIN_ATTEMPTS
      || '10',
      10,
    ),
    lockoutMinutes: parseInt(process.env.LOCKOUT_DURATION_MINUTES || '15', 10),
  },

  // ── Billing ───────────────────────────────────────────────────────────────
  billing: {
    validityHours: parseInt(process.env.CONTROL_NUMBER_VALIDITY_HOURS || '5', 10),
  },

  // ── Redis (Upstash) ───────────────────────────────────────────────────────
  redisUrl: process.env.REDIS_URL || null,

  // ── Africa's Talking (SMS) ────────────────────────────────────────────────
  africasTalking: {
    username: process.env.AT_USERNAME  || 'sandbox',
    apiKey:   process.env.AT_API_KEY   || '',
    senderId: process.env.AT_SENDER_ID || 'ParkiPay',
    sandbox:  process.env.AT_SANDBOX   === 'True',
  },

  // ── Resend (Email) ────────────────────────────────────────────────────────
  resend: {
    apiKey:    process.env.RESEND_API_KEY || '',
    emailFrom: process.env.EMAIL_FROM     || 'noreply@parkipay.go.tz',
  },

  // ── Render Deploy Hook ────────────────────────────────────────────────────
  renderDeployHook: process.env.RENDER_DEPLOY_HOOK_URL || '',
};

// ── Production startup validation ────────────────────────────────────────────
if (cfg.isProduction) {
  required('SECRET_KEY');
  required('DATABASE_URL');
  required('CORS_ALLOWED_ORIGINS');
  required('AT_API_KEY');
  required('RESEND_API_KEY');
}

module.exports = cfg;

// ParkiPay — Central config
// Reads environment variables and exposes app configuration.

require('dotenv').config();

function required(key) {
  const val = process.env[key];

  if (!val && process.env.NODE_ENV === 'production') {
    throw new Error(`Missing required environment variable: ${key}`);
  }

  return val || '';
}

const cfg = {
  // ── Server ─────────────────────────────────────────────
  nodeEnv: process.env.NODE_ENV || 'development',

  // Render provides PORT automatically
  port: parseInt(process.env.PORT || '8000', 10),

  isProduction: process.env.NODE_ENV === 'production',
  isTest: process.env.NODE_ENV === 'test',

  debug: process.env.DEBUG === 'True',

  allowedHosts:
    process.env.ALLOWED_HOSTS || 'http://localhost:8000',

  // ── JWT / Security ────────────────────────────────────
  jwt: {
    secret:
      process.env.SECRET_KEY ||
      process.env.JWT_SECRET ||
      'dev-secret-CHANGE-IN-PRODUCTION',

    accessExpiresIn:
      process.env.JWT_ACCESS_EXPIRES_IN ||
      `${process.env.JWT_ACCESS_TOKEN_LIFETIME_MINUTES || 60}m`,

    refreshExpiresIn:
      process.env.JWT_REFRESH_EXPIRES_IN ||
      `${process.env.JWT_REFRESH_TOKEN_LIFETIME_DAYS || 7}d`,
  },

  // ── CORS ──────────────────────────────────────────────
  corsOrigins: (() => {
    const origins = (
      process.env.CORS_ALLOWED_ORIGINS ||
      'http://localhost:8081,http://localhost:19006,exp://localhost:19000'
    )
      .split(',')
      .map((o) => o.trim())
      .filter(Boolean);
    
    // If in development, also accept network IPs
    if (process.env.NODE_ENV === 'development') {
      origins.push(/^http:\/\/(192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.)([0-9]{1,3}\.){2}[0-9]{1,3}:[0-9]+$/);
    }
    
    return origins;
  })(),

  // ── Auth Policy ───────────────────────────────────────
  auth: {
    maxFailedAttempts: parseInt(
      process.env.MAX_FAILED_LOGIN_ATTEMPT ||
      process.env.MAX_FAILED_LOGIN_ATTEMPTS ||
      '10',
      10
    ),

    lockoutMinutes: parseInt(
      process.env.LOCKOUT_DURATION_MINUTES || '15',
      10
    ),
  },

  // ── Billing ───────────────────────────────────────────
  billing: {
    validityHours: parseInt(
      process.env.CONTROL_NUMBER_VALIDITY_HOURS || '5',
      10
    ),
  },

  // ── Redis ─────────────────────────────────────────────
  redisUrl: process.env.REDIS_URL || null,

  // ── Africa's Talking ──────────────────────────────────
  africasTalking: {
    username: process.env.AT_USERNAME || 'sandbox',

    apiKey: process.env.AT_API_KEY || '',

    senderId: process.env.AT_SENDER_ID || 'ParkiPay',

    sandbox: process.env.AT_SANDBOX === 'True',
  },

  // ── Resend Email ──────────────────────────────────────
  resend: {
    apiKey: process.env.RESEND_API_KEY || '',

    emailFrom:
      process.env.EMAIL_FROM || 'noreply@parkipay.go.tz',
  },

  // ── Render ────────────────────────────────────────────
  renderDeployHook:
    process.env.RENDER_DEPLOY_HOOK_URL || '',
};

// ── Production Validation ───────────────────────────────
if (cfg.isProduction) {
  required('SECRET_KEY');
  required('DATABASE_URL');
  required('CORS_ALLOWED_ORIGINS');
  required('AT_API_KEY');
  required('RESEND_API_KEY');
}

module.exports = cfg;

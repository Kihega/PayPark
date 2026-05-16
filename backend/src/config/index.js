// ParkiPay — Central config (mirrors Django settings)
require('dotenv').config();

const cfg = {
  nodeEnv:   process.env.NODE_ENV || 'development',
  port:      parseInt(process.env.PORT || '8000', 10),
  isProduction: process.env.NODE_ENV === 'production',

  jwt: {
    secret:           process.env.JWT_SECRET || 'dev-secret-change-me',
    accessExpiresIn:  process.env.JWT_ACCESS_EXPIRES_IN  || '60m',
    refreshExpiresIn: process.env.JWT_REFRESH_EXPIRES_IN || '7d',
  },

  auth: {
    maxFailedAttempts:   parseInt(process.env.MAX_FAILED_LOGIN_ATTEMPTS || '5', 10),
    lockoutMinutes:      parseInt(process.env.LOCKOUT_DURATION_MINUTES  || '15', 10),
  },

  billing: {
    validityHours: parseInt(process.env.CONTROL_NUMBER_VALIDITY_HOURS || '5', 10),
  },

  africasTalking: {
    username: process.env.AT_USERNAME  || 'sandbox',
    apiKey:   process.env.AT_API_KEY   || '',
    senderId: process.env.AT_SENDER_ID || 'ParkiPay',
  },
};

module.exports = cfg;

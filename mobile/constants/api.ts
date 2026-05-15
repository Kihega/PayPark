/**
 * ParkiPay — API Configuration
 * Base URL is read from the Expo environment.
 */

// In production, override via eas.json or app.config.ts environment variables
const DEV_API_URL = 'http://localhost:8000';
const STAGING_API_URL = 'https://parkipay-api.onrender.com';

export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_URL ?? DEV_API_URL;

export const API_ROUTES = {
  // Auth
  login: '/api/auth/login/',
  refresh: '/api/auth/refresh/',
  logout: '/api/auth/logout/',
  me: '/api/auth/me/',

  // Health
  health: '/api/health/',

  // Vehicles (Sprint 2)
  vehicleLookup: '/api/vehicles/lookup/',
  locations: '/api/vehicles/locations/',

  // Billing (Sprint 3)
  billingGenerate: '/api/billing/generate/',
  billingHistory: '/api/billing/history/',
  billStatus: (cn: string) => `/api/billing/${cn}/status/`,
} as const;

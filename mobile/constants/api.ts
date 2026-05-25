/**
 * ParkiPay — API Configuration
 *
 * URL resolution order (first match wins):
 *   1. EXPO_PUBLIC_API_URL  — set in .env for physical devices or staging
 *   2. Android emulator     — 10.0.2.2 is the host machine inside AVD
 *   3. iOS simulator        — localhost reaches the host machine directly
 *   4. Production fallback  — Render deployment (used in release builds)
 *
 * Quick-start for a physical device (USB or Wi-Fi):
 *   1. Find your PC's LAN IP:
 *        macOS/Linux : ifconfig | grep "inet " | grep -v 127
 *        Windows     : ipconfig | findstr "IPv4"
 *        Termux      : ip addr show | grep "inet " | grep -v 127
 *   2. Copy mobile/.env.example → mobile/.env
 *   3. Set EXPO_PUBLIC_API_URL=http://<YOUR_LAN_IP>:8000
 *   4. Make sure your PC firewall allows inbound on port 8000.
 */

import { Platform } from 'react-native';

// ── Fallback URL for local dev (no .env file present) ────────────────────────

function getLocalDevUrl(): string {
  if (Platform.OS === 'android') {
    // Android emulator special alias: 10.0.2.2 → the host machine's loopback
    return 'http://10.0.2.2:8000';
  }
  // iOS simulator can reach the Mac's localhost directly
  return 'http://localhost:8000';
}

// ── Production URL ────────────────────────────────────────────────────────────

const PRODUCTION_API_URL = 'https://paypark-backend-6kc4.onrender.com';

// ── Resolved base URL ─────────────────────────────────────────────────────────

export const API_BASE_URL: string =
  // Priority 1: explicit override from .env (physical device / staging / prod)
  process.env.EXPO_PUBLIC_API_URL ??
  // Priority 2: auto-detect for simulators/emulators in dev mode
  (__DEV__ ? getLocalDevUrl() : PRODUCTION_API_URL);

// Log the resolved URL in dev so you can verify it immediately
if (__DEV__) {
  console.log(`[ParkiPay] API_BASE_URL → ${API_BASE_URL}`);
}

// ── Routes ────────────────────────────────────────────────────────────────────

export const API_ROUTES = {
  // Auth
  login:   '/api/auth/login/',
  refresh: '/api/auth/refresh/',
  logout:  '/api/auth/logout/',
  me:      '/api/auth/me/',

  // Health
  health: '/api/health/',

  // Vehicles (Sprint 2)
  vehicleLookup: '/api/vehicles/lookup/',
  locations:     '/api/vehicles/locations/',

  // Billing (Sprint 3)
  billingGenerate: '/api/billing/generate/',
  billingHistory:  '/api/billing/history/',
  billStatus: (cn: string) => `/api/billing/${cn}/status/`,
} as const;

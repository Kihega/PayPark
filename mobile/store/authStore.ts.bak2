/**
 * ParkiPay — Auth Store (Zustand)
 * Manages JWT tokens and officer profile.
 * Tokens are persisted in expo-secure-store (hardware-backed on Android).
 */
import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';

// ── Types ─────────────────────────────────────────────────────────────────────

/**
 * Matches the shape returned by the backend's officerProfile() helper:
 *   { id, employeeId, fullName, phone, email, role, locationName, isActive, lastLogin }
 * NOTE: all fields are camelCase — the backend is Node/Express (camelCase convention).
 */
export interface OfficerProfile {
  id: number;
  employeeId: string;
  fullName: string;
  phone: string;
  email: string;
  role: 'FIELD_OFFICER' | 'SUPERVISOR' | 'ADMIN';
  locationName: string | null;
  isActive: boolean;
  lastLogin: string | null;
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  officer: OfficerProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Actions
  setAuth: (accessToken: string, refreshToken: string, officer: OfficerProfile) => Promise<void>;
  setAccessToken: (token: string) => void;
  clearAuth: () => Promise<void>;
  loadStoredAuth: () => Promise<void>;
}

// ── SecureStore keys ──────────────────────────────────────────────────────────
const KEYS = {
  ACCESS_TOKEN:    'parkipay_access_token',
  REFRESH_TOKEN:   'parkipay_refresh_token',
  OFFICER_PROFILE: 'parkipay_officer_profile',
} as const;

// ── Store ─────────────────────────────────────────────────────────────────────

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  refreshToken: null,
  officer: null,
  isAuthenticated: false,
  isLoading: true,

  /**
   * Called after a successful login response.
   * Stores tokens and profile in SecureStore for persistence.
   */
  setAuth: async (accessToken, refreshToken, officer) => {
    await SecureStore.setItemAsync(KEYS.ACCESS_TOKEN, accessToken);
    await SecureStore.setItemAsync(KEYS.REFRESH_TOKEN, refreshToken);
    await SecureStore.setItemAsync(KEYS.OFFICER_PROFILE, JSON.stringify(officer));
    set({ accessToken, refreshToken, officer, isAuthenticated: true });
  },

  /**
   * Called by the Axios interceptor after a silent token refresh.
   */
  setAccessToken: (token) => {
    SecureStore.setItemAsync(KEYS.ACCESS_TOKEN, token);
    set({ accessToken: token });
  },

  /**
   * Called on logout. Clears all stored data.
   */
  clearAuth: async () => {
    await SecureStore.deleteItemAsync(KEYS.ACCESS_TOKEN);
    await SecureStore.deleteItemAsync(KEYS.REFRESH_TOKEN);
    await SecureStore.deleteItemAsync(KEYS.OFFICER_PROFILE);
    set({ accessToken: null, refreshToken: null, officer: null, isAuthenticated: false });
  },

  /**
   * Called on app startup. Restores session from SecureStore if tokens exist.
   */
  loadStoredAuth: async () => {
    try {
      const [accessToken, refreshToken, profileJson] = await Promise.all([
        SecureStore.getItemAsync(KEYS.ACCESS_TOKEN),
        SecureStore.getItemAsync(KEYS.REFRESH_TOKEN),
        SecureStore.getItemAsync(KEYS.OFFICER_PROFILE),
      ]);

      if (accessToken && refreshToken && profileJson) {
        const officer: OfficerProfile = JSON.parse(profileJson);
        // Guard against stale profiles stored with old snake_case keys
        if (!officer.fullName && (officer as unknown as Record<string, unknown>).full_name) {
          // Wipe the stale profile so the user re-authenticates cleanly
          await SecureStore.deleteItemAsync(KEYS.ACCESS_TOKEN);
          await SecureStore.deleteItemAsync(KEYS.REFRESH_TOKEN);
          await SecureStore.deleteItemAsync(KEYS.OFFICER_PROFILE);
          return;
        }
        set({ accessToken, refreshToken, officer, isAuthenticated: true });
      }
    } catch {
      // SecureStore unavailable; start unauthenticated
    } finally {
      set({ isLoading: false });
    }
  },
}));

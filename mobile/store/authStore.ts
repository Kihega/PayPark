/**
 * ParkiPay — Auth Store (Zustand)
 */
import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';

export interface OfficerProfile {
  id: number;
  employeeId: string;
  fullName: string;
  phone: string;
  email: string;
  role: 'ATTENDANT' | 'SUPERVISOR';
  locationId: number | null;
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
  setAuth: (access: string, refresh: string, officer: OfficerProfile) => Promise<void>;
  setAccessToken: (token: string) => void;
  clearAuth: () => Promise<void>;
  loadStoredAuth: () => Promise<void>;
}

const KEYS = {
  ACCESS:  'parkipay_access_token',
  REFRESH: 'parkipay_refresh_token',
  OFFICER: 'parkipay_officer_profile',
} as const;

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null, refreshToken: null, officer: null,
  isAuthenticated: false, isLoading: true,

  setAuth: async (accessToken, refreshToken, officer) => {
    await SecureStore.setItemAsync(KEYS.ACCESS,  accessToken);
    await SecureStore.setItemAsync(KEYS.REFRESH, refreshToken);
    await SecureStore.setItemAsync(KEYS.OFFICER, JSON.stringify(officer));
    set({ accessToken, refreshToken, officer, isAuthenticated: true });
    // Load this officer's personal language/theme preferences
    const { setOfficerKey } = (await import('./settingsStore')).useSettingsStore.getState();
    await setOfficerKey(officer.id);
  },

  setAccessToken: (token) => {
    SecureStore.setItemAsync(KEYS.ACCESS, token);
    set({ accessToken: token });
  },

  clearAuth: async () => {
    await Promise.all([
      SecureStore.deleteItemAsync(KEYS.ACCESS).catch(() => {}),
      SecureStore.deleteItemAsync(KEYS.REFRESH).catch(() => {}),
      SecureStore.deleteItemAsync(KEYS.OFFICER).catch(() => {}),
    ]);
    // Reset settings to defaults so next user starts fresh
    const { clearSettings } = (await import('./settingsStore')).useSettingsStore.getState();
    clearSettings();
    set({ accessToken: null, refreshToken: null, officer: null, isAuthenticated: false });
  },

  loadStoredAuth: async () => {
    try {
      const [access, refresh, profileJson] = await Promise.all([
        SecureStore.getItemAsync(KEYS.ACCESS),
        SecureStore.getItemAsync(KEYS.REFRESH),
        SecureStore.getItemAsync(KEYS.OFFICER),
      ]);

      if (!access || !refresh || !profileJson) {
        // No stored credentials → go to login
        set({ isLoading: false });
        return;
      }

      // Decode access token to check expiry client-side (no network needed)
      let isExpired = true;
      try {
        const payload = JSON.parse(
          Buffer.from(access.split('.')[1], 'base64').toString('utf-8')
        );
        isExpired = (payload.exp ?? 0) * 1000 < Date.now();
      } catch { isExpired = true; }

      if (isExpired) {
        // Access token expired — try a silent refresh via the API interceptor
        // Set credentials first so the interceptor can use the refresh token
        set({ accessToken: access, refreshToken: refresh,
              officer: JSON.parse(profileJson), isAuthenticated: false });

        try {
          // Import lazily to avoid circular dependency
          const { authService } = require('@/services/api');
          await authService.refreshToken(refresh);
          // If refresh succeeded, the interceptor already called setAuth
          // (handled in the API interceptor); just mark loaded
          set({ isLoading: false });
        } catch {
          // Refresh failed → force login
          await Promise.all([
            SecureStore.deleteItemAsync(KEYS.ACCESS).catch(() => {}),
            SecureStore.deleteItemAsync(KEYS.REFRESH).catch(() => {}),
            SecureStore.deleteItemAsync(KEYS.OFFICER).catch(() => {}),
          ]);
          set({ accessToken: null, refreshToken: null, officer: null,
                isAuthenticated: false, isLoading: false });
        }
      } else {
        // Token still valid — restore session immediately
        set({ accessToken: access, refreshToken: refresh,
              officer: JSON.parse(profileJson),
              isAuthenticated: true, isLoading: false });
      }
    } catch {
      set({ isLoading: false });
    }
  },
}));

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
  },

  setAccessToken: (token) => {
    SecureStore.setItemAsync(KEYS.ACCESS, token);
    set({ accessToken: token });
  },

  clearAuth: async () => {
    await SecureStore.deleteItemAsync(KEYS.ACCESS);
    await SecureStore.deleteItemAsync(KEYS.REFRESH);
    await SecureStore.deleteItemAsync(KEYS.OFFICER);
    set({ accessToken: null, refreshToken: null, officer: null, isAuthenticated: false });
  },

  loadStoredAuth: async () => {
    try {
      const [access, refresh, profileJson] = await Promise.all([
        SecureStore.getItemAsync(KEYS.ACCESS),
        SecureStore.getItemAsync(KEYS.REFRESH),
        SecureStore.getItemAsync(KEYS.OFFICER),
      ]);
      if (access && refresh && profileJson) {
        set({ accessToken: access, refreshToken: refresh,
          officer: JSON.parse(profileJson), isAuthenticated: true });
      }
    } catch { /* start unauthenticated */ } finally {
      set({ isLoading: false });
    }
  },
}));

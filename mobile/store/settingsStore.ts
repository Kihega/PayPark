/**
 * ParkiPay — Settings Store
 * Language (en/sw) + Theme (light/dark) persisted in SecureStore
 */
import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';

export type Language = 'en' | 'sw';
export type Theme    = 'light' | 'dark';

interface SettingsState {
  language: Language;
  theme: Theme;
  setLanguage: (l: Language) => Promise<void>;
  setTheme: (t: Theme) => Promise<void>;
  loadSettings: () => Promise<void>;
}

export const useSettingsStore = create<SettingsState>((set) => ({
  language: 'en',
  theme: 'light',

  setLanguage: async (language) => {
    await SecureStore.setItemAsync('parkipay_language', language);
    set({ language });
  },
  setTheme: async (theme) => {
    await SecureStore.setItemAsync('parkipay_theme', theme);
    set({ theme });
  },
  loadSettings: async () => {
    const lang  = await SecureStore.getItemAsync('parkipay_language').catch(() => null);
    const theme = await SecureStore.getItemAsync('parkipay_theme').catch(() => null);
    set({
      language: (lang  as Language) ?? 'en',
      theme:    (theme as Theme)    ?? 'light',
    });
  },
}));

/* ── Theme colour palettes ──────────────────────────────────────────────────── */
export const LIGHT = {
  bg: '#F4F6F4', card: '#FFFFFF', border: '#E5E7EB',
  text: '#1A1A1A', textSub: '#6B7280', textMuted: '#9CA3AF',
  headerBg: '#0D1117', headerText: '#FFFFFF',
  statCard: '#FFFFFF', accent: '#1EB53A', accentYellow: '#FCD116',
  danger: '#D32F2F', dangerSurface: '#FEECEC',
  navBg: '#FFFFFF', navBorder: '#F0F0F0', navActive: '#1EB53A',
  sidebarBg: '#111827', sidebarText: '#F9FAFB',
};
export const DARK = {
  bg: '#0F172A', card: '#1E293B', border: '#334155',
  text: '#F1F5F9', textSub: '#94A3B8', textMuted: '#64748B',
  headerBg: '#020617', headerText: '#F1F5F9',
  statCard: '#1E293B', accent: '#22D35E', accentYellow: '#FCD116',
  danger: '#EF4444', dangerSurface: '#450A0A',
  navBg: '#1E293B', navBorder: '#334155', navActive: '#22D35E',
  sidebarBg: '#020617', sidebarText: '#F1F5F9',
};
export function palette(theme: Theme) { return theme === 'dark' ? DARK : LIGHT; }

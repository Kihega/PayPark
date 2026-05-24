/**
 * ParkiPay — Settings Store  (per-user)
 * Each officer's preferences are stored under their own key so two logged-in
 * officers on different devices get independent language + theme.
 *
 * Storage keys:  parkipay_lang_{officerId}  /  parkipay_theme_{officerId}
 * Falls back to  parkipay_lang_global  when no officer is loaded yet
 * (i.e. on the sign-in screen).
 */
import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';

export type Language = 'en' | 'sw';
export type Theme    = 'light' | 'dark';

interface SettingsState {
  language: Language;
  theme: Theme;
  officerKey: string;                                    // current key prefix
  setOfficerKey: (id: string | number) => Promise<void>; // call on login
  setLanguage:   (l: Language) => Promise<void>;
  setTheme:      (t: Theme)    => Promise<void>;
  loadSettings:  () => Promise<void>;
  clearSettings: () => void;
}

const GLOBAL_KEY = 'global';

function langKey(k: string)  { return `parkipay_lang_${k}`; }
function themeKey(k: string) { return `parkipay_theme_${k}`; }

export const useSettingsStore = create<SettingsState>((set, get) => ({
  language:   'en',
  theme:      'light',
  officerKey: GLOBAL_KEY,

  /** Call this right after a successful login so settings switch to that officer. */
  setOfficerKey: async (id) => {
    const key = String(id);
    const lang  = await SecureStore.getItemAsync(langKey(key)).catch(() => null);
    const theme = await SecureStore.getItemAsync(themeKey(key)).catch(() => null);
    set({
      officerKey: key,
      language:   (lang  as Language) ?? 'en',
      theme:      (theme as Theme)    ?? 'light',
    });
  },

  setLanguage: async (language) => {
    const key = get().officerKey;
    await SecureStore.setItemAsync(langKey(key), language);
    set({ language });
  },

  setTheme: async (theme) => {
    const key = get().officerKey;
    await SecureStore.setItemAsync(themeKey(key), theme);
    set({ theme });
  },

  /** Load settings for whoever is currently keyed (called from app layout). */
  loadSettings: async () => {
    const key  = get().officerKey;
    const lang  = await SecureStore.getItemAsync(langKey(key)).catch(() => null);
    const theme = await SecureStore.getItemAsync(themeKey(key)).catch(() => null);
    set({
      language: (lang  as Language) ?? 'en',
      theme:    (theme as Theme)    ?? 'light',
    });
  },

  /** Reset to defaults on logout (next officer starts fresh). */
  clearSettings: () => set({ language: 'en', theme: 'light', officerKey: GLOBAL_KEY }),
}));

/* ── Theme colour palettes ────────────────────────────────────────────────── */
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

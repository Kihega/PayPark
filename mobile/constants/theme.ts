/**
 * ParkiPay — TATURA Platform Design System
 * Colours and typography aligned with the Tanzanian government
 * TATURA (Tanzania Urban Roads Authority) design language.
 *
 * Sprint accent colours (Tanzania national flag palette):
 *   Green  #1EB53A — primary brand, trust, action
 *   Yellow #FCD116 — accent, warning, highlight
 *   Black  #000000 — text, borders, contrast
 */

// ── Brand / Sprint Colors ─────────────────────────────────────────────────────
export const SprintColors = {
  green: '#1EB53A',
  greenDark: '#158A2A',
  greenLight: '#4DD669',
  yellow: '#FCD116',
  yellowDark: '#C9A800',
  yellowLight: '#FFE55A',
  black: '#000000',
  white: '#FFFFFF',
} as const;

// ── TATURA Primary Palette ────────────────────────────────────────────────────
export const Colors = {
  // Primary — TATURA green
  primary: '#1EB53A',
  primaryDark: '#158A2A',
  primaryLight: '#4DD669',
  primarySurface: '#E8F8EC',

  // Accent — Tanzania gold/yellow
  accent: '#FCD116',
  accentDark: '#C9A800',
  accentLight: '#FFE55A',
  accentSurface: '#FFFBE6',

  // Neutrals
  black: '#000000',
  grey900: '#1A1A1A',
  grey800: '#2D2D2D',
  grey700: '#404040',
  grey600: '#595959',
  grey500: '#737373',
  grey400: '#8C8C8C',
  grey300: '#A6A6A6',
  grey200: '#BFBFBF',
  grey100: '#D9D9D9',
  grey50: '#F2F2F2',
  white: '#FFFFFF',

  // Semantic
  success: '#1EB53A',
  successSurface: '#E8F8EC',
  warning: '#FCD116',
  warningSurface: '#FFFBE6',
  error: '#D32F2F',
  errorSurface: '#FEECEC',
  info: '#1565C0',
  infoSurface: '#E3F0FD',

  // Backgrounds
  background: '#FFFFFF',
  backgroundSecondary: '#F5F7F5',
  backgroundCard: '#FFFFFF',

  // Text
  textPrimary: '#1A1A1A',
  textSecondary: '#595959',
  textDisabled: '#A6A6A6',
  textInverse: '#FFFFFF',
  textOnAccent: '#1A1A1A',   // black text on yellow background

  // Borders
  border: '#E0E0E0',
  borderFocused: '#1EB53A',
  divider: '#F0F0F0',

  // Status pills
  statusActive: '#1EB53A',
  statusActiveText: '#FFFFFF',
  statusExpired: '#8C8C8C',
  statusExpiredText: '#FFFFFF',
  statusPaid: '#1565C0',
  statusPaidText: '#FFFFFF',
} as const;

// ── Typography ─────────────────────────────────────────────────────────────────
// TATURA uses system sans-serif fonts for maximum cross-device compatibility
// on Android government devices.
export const FontFamily = {
  regular: 'System',
  medium: 'System',
  semiBold: 'System',
  bold: 'System',
  // Used on the splash screen wordmark only
  display: 'System',
} as const;

export const FontSize = {
  xs: 11,
  sm: 13,
  base: 15,
  md: 17,
  lg: 20,
  xl: 24,
  '2xl': 28,
  '3xl': 34,
  '4xl': 40,
  display: 52,   // Splash screen wordmark
} as const;

export const FontWeight = {
  regular: '400' as const,
  medium: '500' as const,
  semiBold: '600' as const,
  bold: '700' as const,
  extraBold: '800' as const,
  black: '900' as const,
} as const;

export const LineHeight = {
  tight: 1.15,
  normal: 1.4,
  relaxed: 1.6,
} as const;

export const LetterSpacing = {
  tight: -0.5,
  normal: 0,
  wide: 0.5,
  extraWide: 1.5,   // Used for control numbers
  display: 2,       // Splash screen wordmark
} as const;

// ── Spacing ────────────────────────────────────────────────────────────────────
export const Spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  base: 16,
  lg: 20,
  xl: 24,
  '2xl': 32,
  '3xl': 40,
  '4xl': 48,
  '5xl': 64,
} as const;

// ── Border Radius ──────────────────────────────────────────────────────────────
export const Radius = {
  sm: 6,
  md: 10,
  lg: 14,
  xl: 20,
  full: 9999,
} as const;

// ── Shadows ────────────────────────────────────────────────────────────────────
export const Shadows = {
  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 3,
    elevation: 2,
  },
  md: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.10,
    shadowRadius: 6,
    elevation: 4,
  },
  lg: {
    shadowColor: '#1EB53A',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 8,
  },
  // Glow shadow for the splash wordmark
  glow: {
    shadowColor: '#1EB53A',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.6,
    shadowRadius: 20,
    elevation: 12,
  },
} as const;

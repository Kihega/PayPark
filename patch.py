"""
patch_v2.py — ParkiPay major redesign
======================================
Run from project root:  python patch_v2.py

Changes applied
───────────────
MOBILE
  1. login.tsx            — employee-ID only (no password / biometric)
  2. hooks/useAuth.ts     — remove password param, add role-based routing
  3. store/authStore.ts   — fix OfficerProfile to camelCase (matches backend)
  4. store/settingsStore.ts  [NEW] — language (EN/SW) + theme (light/dark)
  5. constants/i18n.ts       [NEW] — full EN / Swahili translation map
  6. app/(app)/home.tsx   — full dashboard redesign with animated sidebar
  7. app/(app)/admin.tsx  [NEW] — simple admin screen
  8. app/(app)/_layout.tsx — register admin screen
  9. app/_layout.tsx      — theme-aware status bar

BACKEND
 10. src/routes/auth.js  — employee-ID-only login (no bcrypt check)
 11. src/routes/admin.js [NEW] — officer CRUD endpoints
 12. src/app.js          — mount /api/admin/ router

SQL  (paste into Supabase SQL Editor)
 13. patch_v2_supervisor.sql — add supervisor + field officer seed rows
"""

import os, sys, json

ROOT = os.path.dirname(os.path.abspath(__file__))

def p(*parts): return os.path.join(ROOT, *parts)
def read(f):
    with open(f, encoding="utf-8") as fh: return fh.read()
def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh: fh.write(content)
    print(f"  [✓] {path}")
def bak(path):
    b = path + ".bak2"
    if os.path.exists(path) and not os.path.exists(b):
        write(b, read(path))

# ─── 1. login.tsx ─────────────────────────────────────────────────────────────
LOGIN = p("mobile","app","(auth)","login.tsx")

LOGIN_CONTENT = r'''/**
 * ParkiPay — Login  (v3: employee-ID only, role-based routing)
 */
import { useState } from 'react';
import {
  ActivityIndicator, KeyboardAvoidingView, Platform,
  ScrollView, StyleSheet, Text, TextInput,
  TouchableOpacity, View,
} from 'react-native';
import { router } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '@/hooks/useAuth';
import { useSettingsStore } from '@/store/settingsStore';
import { t } from '@/constants/i18n';
import { Colors, SprintColors, FontSize, Spacing, Radius, Shadows } from '@/constants/theme';

export default function LoginScreen() {
  const { loginById, isLoading, error, clearError } = useAuth();
  const { language } = useSettingsStore();
  const tr = (k: string) => t(language, k);

  const [employeeId, setEmployeeId] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);

  const errMsg = localError ?? (error ? tr('invalidId') : null);

  const handleLogin = async () => {
    setLocalError(null); clearError();
    if (!employeeId.trim()) { setLocalError(tr('enterIdError')); return; }
    const result = await loginById(employeeId.trim());
    if (!result.success) return;
    if (result.role === 'SUPERVISOR' || result.role === 'ADMIN') {
      router.replace('/(app)/admin');
    } else {
      router.replace('/(app)/home');
    }
  };

  return (
    <KeyboardAvoidingView style={styles.root} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">

        {/* Header */}
        <View style={styles.header}>
          <LinearGradient colors={[SprintColors.green, SprintColors.yellow]}
            start={{x:0,y:0}} end={{x:1,y:0}} style={styles.accent} />
          <View style={{flexDirection:'row'}}>
            <Text style={[styles.logo,{color:SprintColors.green}]}>Parki</Text>
            <Text style={[styles.logo,{color:SprintColors.yellow}]}>Pay</Text>
          </View>
          <Text style={styles.sub1}>{tr('taglineSw')}</Text>
          <Text style={styles.sub2}>{tr('taglineEn')}</Text>
        </View>

        {/* Card */}
        <View style={styles.card}>
          <Text style={styles.title}>{tr('signIn')}</Text>
          <Text style={styles.subtitle}>{tr('signInSub')}</Text>

          <Text style={styles.label}>{tr('officerId')}</Text>
          <View style={[styles.inputRow, errMsg && styles.inputErr]}>
            <Ionicons name="id-card-outline" size={18} color={errMsg ? Colors.error : '#6B7280'}
              style={{marginLeft:12}} />
            <TextInput
              style={styles.input}
              value={employeeId}
              onChangeText={v => { setLocalError(null); clearError(); setEmployeeId(v); }}
              placeholder="e.g. TZ-8821"
              placeholderTextColor="#9CA3AF"
              autoCapitalize="characters"
              autoCorrect={false}
              returnKeyType="done"
              onSubmitEditing={handleLogin}
              editable={!isLoading}
            />
          </View>

          {errMsg ? (
            <View style={styles.errBox}>
              <Ionicons name="alert-circle-outline" size={15} color={Colors.error} />
              <Text style={styles.errText}>{errMsg}</Text>
            </View>
          ) : null}

          <TouchableOpacity style={[styles.btn, isLoading && {opacity:0.6}]}
            onPress={handleLogin} disabled={isLoading} activeOpacity={0.85}>
            {isLoading
              ? <ActivityIndicator color="#fff" />
              : <>
                  <Ionicons name="log-in-outline" size={20} color="#fff" />
                  <Text style={styles.btnText}>{tr('signInBtn')}</Text>
                </>}
          </TouchableOpacity>
        </View>

        <View style={styles.footer}>
          <LinearGradient colors={[SprintColors.yellow, SprintColors.black]}
            start={{x:0,y:0}} end={{x:1,y:0}} style={styles.footerAccent} />
          <Text style={styles.footerText}>© 2026 Serikali ya Tanzania — ParkiPay v1.0</Text>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  root:{ flex:1, backgroundColor: Colors.backgroundSecondary },
  scroll:{ flexGrow:1, paddingHorizontal:20, paddingBottom:40 },
  header:{ alignItems:'center', paddingTop:60, paddingBottom:28 },
  accent:{ width:180, height:4, borderRadius:2, marginBottom:16 },
  logo:{ fontSize:36, fontWeight:'900', letterSpacing:1 },
  sub1:{ fontSize:13, color:'#404040', marginTop:4 },
  sub2:{ fontSize:13, color:'#737373' },
  card:{ backgroundColor:'#fff', borderRadius:16, padding:24, ...Shadows.md },
  title:{ fontSize:28, fontWeight:'800', textAlign:'center', color:'#1A1A1A', marginBottom:4 },
  subtitle:{ fontSize:13, color:'#595959', textAlign:'center', marginBottom:24, lineHeight:20 },
  label:{ fontSize:13, fontWeight:'700', color:'#1A1A1A', marginBottom:6 },
  inputRow:{ flexDirection:'row', alignItems:'center', height:54, borderWidth:1.5,
    borderColor:'#D1D5DB', borderRadius:12, backgroundColor:'#fff' },
  inputErr:{ borderColor: Colors.error },
  input:{ flex:1, fontSize:15, color:'#1A1A1A', paddingHorizontal:10 },
  errBox:{ flexDirection:'row', alignItems:'center', gap:6,
    backgroundColor: Colors.errorSurface, borderRadius:10, padding:10,
    marginTop:8, borderLeftWidth:3, borderLeftColor: Colors.error },
  errText:{ fontSize:13, color: Colors.error, flex:1 },
  btn:{ flexDirection:'row', alignItems:'center', justifyContent:'center', gap:10,
    height:56, backgroundColor:'#0D1117', borderRadius:12, marginTop:20 },
  btnText:{ color:'#fff', fontSize:15, fontWeight:'700', letterSpacing:0.4 },
  footer:{ alignItems:'center', marginTop:32, gap:8 },
  footerAccent:{ width:80, height:3, borderRadius:2 },
  footerText:{ fontSize:11, color:'#8C8C8C' },
});
'''

# ─── 2. hooks/useAuth.ts ──────────────────────────────────────────────────────
USE_AUTH = p("mobile","hooks","useAuth.ts")

USE_AUTH_CONTENT = r'''/**
 * ParkiPay — useAuth Hook  (v2: ID-only login)
 */
import { useState, useCallback } from 'react';
import { authService } from '@/services/api';
import { useAuthStore, OfficerProfile } from '@/store/authStore';

export interface AuthError {
  code: string;
  message: string;
  remainingAttempts?: number;
  lockedUntil?: string;
}

interface LoginResult {
  success: boolean;
  role?: string;
  error?: AuthError;
}

export function useAuth() {
  const { setAuth, clearAuth, refreshToken, officer, isAuthenticated } = useAuthStore();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<AuthError | null>(null);

  const loginById = useCallback(async (employeeId: string): Promise<LoginResult> => {
    setIsLoading(true);
    setError(null);
    try {
      const { data } = await authService.loginById(employeeId.trim());
      await setAuth(data.access, data.refresh, data.officer as OfficerProfile);
      return { success: true, role: data.officer.role };
    } catch (err: unknown) {
      const d = (err as any)?.response?.data;
      const authError: AuthError = {
        code: d?.error ?? 'network_error',
        message: d?.detail ?? 'Connection failed. Check your network.',
      };
      setError(authError);
      return { success: false, error: authError };
    } finally {
      setIsLoading(false);
    }
  }, [setAuth]);

  const logout = useCallback(async () => {
    setIsLoading(true);
    try {
      if (refreshToken) await authService.logout(refreshToken);
    } catch { /* clear local state regardless */ } finally {
      await clearAuth();
      setIsLoading(false);
    }
  }, [refreshToken, clearAuth]);

  return { officer, isAuthenticated, isLoading, error,
    clearError: () => setError(null), loginById, logout };
}
'''

# ─── 3. store/authStore.ts — fix OfficerProfile to camelCase ─────────────────
AUTH_STORE = p("mobile","store","authStore.ts")

AUTH_STORE_CONTENT = r'''/**
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
'''

# ─── 4. store/settingsStore.ts ────────────────────────────────────────────────
SETTINGS_STORE = p("mobile","store","settingsStore.ts")

SETTINGS_STORE_CONTENT = r'''/**
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
'''

# ─── 5. constants/i18n.ts ────────────────────────────────────────────────────
I18N = p("mobile","constants","i18n.ts")

I18N_CONTENT = r'''/**
 * ParkiPay — Translations (English + Swahili)
 */
export type Language = 'en' | 'sw';

const translations: Record<Language, Record<string,string>> = {
  en: {
    taglineSw: 'Mfumo wa Maegesho wa Serikali',
    taglineEn: 'Government Parking Management System',
    signIn: 'Sign In', signInSub: 'Enter your officer ID to access the system',
    signInBtn: 'Continue', officerId: 'Officer ID',
    enterIdError: 'Please enter your employee ID.',
    invalidId: 'Employee ID not found or account inactive.',
    activeSession: 'Active Session', onDuty: 'ON DUTY', offDuty: 'OFF DUTY',
    zone: 'Zone', totalBills: 'Total Bills Issued', amountCollected: 'Amount Collected',
    newLookup: 'New Vehicle Lookup', recentBills: 'Recent Bills', viewAll: 'View All',
    noBills: 'No bills recorded today', dashboard: 'Dashboard', lookup: 'Lookup',
    history: 'History', alerts: 'Alerts',
    settings: 'Settings', language: 'Language', english: 'English', swahili: 'Swahili',
    theme: 'Theme', lightMode: 'Light', darkMode: 'Dark',
    logout: 'Logout', logoutConfirm: 'Are you sure you want to logout?',
    yes: 'Yes, Logout', no: 'Cancel', paid: 'PAID', pending: 'PENDING',
    adminPanel: 'Admin Panel', officers: 'Officers', addOfficer: 'Add Officer',
    officerName: 'Full Name', location: 'Parking Location', role: 'Role',
    remove: 'Remove', moveLocation: 'Move', save: 'Save', cancel: 'Cancel',
    confirmRemove: 'Remove this officer?', employeeIdLabel: 'Employee ID',
    selectLocation: 'Select Location', fieldOfficer: 'Field Officer',
    supervisor: 'Supervisor', noOfficers: 'No officers found',
    tzs: 'TZS',
  },
  sw: {
    taglineSw: 'Mfumo wa Maegesho wa Serikali',
    taglineEn: 'Mfumo wa Usimamizi wa Maegesho',
    signIn: 'Ingia', signInSub: 'Ingiza nambari yako ya utumishi kufikia mfumo',
    signInBtn: 'Endelea', officerId: 'Nambari ya Utumishi',
    enterIdError: 'Tafadhali ingiza nambari yako ya utumishi.',
    invalidId: 'Nambari ya utumishi haipatikani au akaunti imezimwa.',
    activeSession: 'Kipindi Kinachoendelea', onDuty: 'KAZINI', offDuty: 'LIKIZONI',
    zone: 'Eneo', totalBills: 'Bili Zilizotolewa', amountCollected: 'Kiasi Kilichokusanywa',
    newLookup: 'Tafuta Gari Jipya', recentBills: 'Bili za Hivi Karibuni', viewAll: 'Tazama Zote',
    noBills: 'Hakuna bili zilizorekodiwa leo', dashboard: 'Dashibodi', lookup: 'Tafuta',
    history: 'Historia', alerts: 'Tahadhari',
    settings: 'Mipangilio', language: 'Lugha', english: 'Kiingereza', swahili: 'Kiswahili',
    theme: 'Mandhari', lightMode: 'Mwanga', darkMode: 'Giza',
    logout: 'Toka', logoutConfirm: 'Je, una uhakika unataka kutoka?',
    yes: 'Ndio, Toka', no: 'Hapana', paid: 'IMELIPWA', pending: 'INASUBIRI',
    adminPanel: 'Paneli ya Msimamizi', officers: 'Maafisa', addOfficer: 'Ongeza Afisa',
    officerName: 'Jina Kamili', location: 'Eneo la Maegesho', role: 'Jukumu',
    remove: 'Ondoa', moveLocation: 'Hamisha', save: 'Hifadhi', cancel: 'Ghairi',
    confirmRemove: 'Ondoa afisa huyu?', employeeIdLabel: 'Nambari ya Utumishi',
    selectLocation: 'Chagua Eneo', fieldOfficer: 'Afisa wa Uwanjani',
    supervisor: 'Msimamizi', noOfficers: 'Hakuna maafisa',
    tzs: 'TZS',
  },
};

export function t(lang: Language, key: string): string {
  return translations[lang]?.[key] ?? translations['en']?.[key] ?? key;
}
'''

# ─── 6. app/(app)/home.tsx ────────────────────────────────────────────────────
HOME = p("mobile","app","(app)","home.tsx")

HOME_CONTENT = r'''/**
 * ParkiPay — Officer Dashboard  (v2)
 */
import { useState, useRef, useEffect } from 'react';
import {
  Alert, Animated, Dimensions, SafeAreaView, ScrollView,
  StyleSheet, Text, TouchableOpacity, View, Modal, Pressable,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useAuthStore } from '@/store/authStore';
import { useSettingsStore, palette } from '@/store/settingsStore';
import { t } from '@/constants/i18n';
import { authService } from '@/services/api';
import { SprintColors } from '@/constants/theme';

const { width: W } = Dimensions.get('window');
const SIDEBAR_W = W * 0.72;

/* ── mock recent bills (replace with API in Sprint 2) ──────────────────────── */
const MOCK_BILLS = [
  { id:'1', plate:'T 482 DXG', amount:'1,000', time:'14:22', status:'paid'    },
  { id:'2', plate:'T 109 ASZ', amount:'5,000', time:'13:10', status:'pending' },
  { id:'3', plate:'T 882 KLP', amount:'1,000', time:'12:00', status:'paid'    },
];

export default function HomeScreen() {
  const { officer, clearAuth, refreshToken } = useAuthStore();
  const { language, theme, setLanguage, setTheme } = useSettingsStore();
  const C = palette(theme);
  const tr = (k: string) => t(language, k);

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [onDuty, setOnDuty]           = useState(true);
  const slideX = useRef(new Animated.Value(-SIDEBAR_W)).current;

  const openSidebar = () => {
    setSidebarOpen(true);
    Animated.spring(slideX, { toValue: 0, useNativeDriver: true, bounciness: 0 }).start();
  };
  const closeSidebar = () => {
    Animated.timing(slideX, { toValue: -SIDEBAR_W, duration: 220, useNativeDriver: true }).start(
      () => setSidebarOpen(false)
    );
  };

  const handleLogout = () => {
    closeSidebar();
    Alert.alert(tr('logout'), tr('logoutConfirm'), [
      { text: tr('no'), style: 'cancel' },
      { text: tr('yes'), style: 'destructive', onPress: async () => {
        try { if (refreshToken) await authService.logout(refreshToken); } catch {}
        await clearAuth();
        router.replace('/(auth)/login');
      }},
    ]);
  };

  if (!officer) return null;

  const today = new Date().toLocaleDateString(language === 'sw' ? 'sw-TZ' : 'en-TZ', {
    weekday:'long', month:'long', day:'numeric',
  });

  const dynStyles = makeStyles(C);

  return (
    <SafeAreaView style={[dynStyles.root]}>

      {/* ── Sidebar overlay ────────────────────────────────────────────── */}
      {sidebarOpen && (
        <Modal transparent animationType="none" visible={sidebarOpen}
          onRequestClose={closeSidebar}>
          <Pressable style={dynStyles.overlay} onPress={closeSidebar} />
          <Animated.View style={[dynStyles.sidebar, { transform:[{translateX: slideX}] }]}>
            <View style={dynStyles.sbHeader}>
              <Text style={dynStyles.sbHeaderText}>⚙ {tr('settings')}</Text>
              <TouchableOpacity onPress={closeSidebar}>
                <Ionicons name="close" size={22} color={C.sidebarText} />
              </TouchableOpacity>
            </View>

            {/* Language */}
            <Text style={dynStyles.sbSection}>{tr('language')}</Text>
            <View style={dynStyles.toggleRow}>
              {(['en','sw'] as const).map(lang => (
                <TouchableOpacity key={lang} onPress={() => setLanguage(lang)}
                  style={[dynStyles.toggleBtn, language===lang && dynStyles.toggleActive]}>
                  <Text style={[dynStyles.toggleText, language===lang && dynStyles.toggleActiveText]}>
                    {lang==='en' ? tr('english') : tr('swahili')}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            {/* Theme */}
            <Text style={dynStyles.sbSection}>{tr('theme')}</Text>
            <View style={dynStyles.toggleRow}>
              {(['light','dark'] as const).map(th => (
                <TouchableOpacity key={th} onPress={() => setTheme(th)}
                  style={[dynStyles.toggleBtn, theme===th && dynStyles.toggleActive]}>
                  <Ionicons name={th==='light' ? 'sunny-outline' : 'moon-outline'}
                    size={14} color={theme===th ? '#fff' : C.sidebarText} />
                  <Text style={[dynStyles.toggleText, theme===th && dynStyles.toggleActiveText]}>
                    {th==='light' ? tr('lightMode') : tr('darkMode')}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <View style={dynStyles.sbDivider} />

            <TouchableOpacity style={dynStyles.logoutBtn} onPress={handleLogout}>
              <Ionicons name="log-out-outline" size={18} color="#EF4444" />
              <Text style={dynStyles.logoutText}>{tr('logout')}</Text>
            </TouchableOpacity>
          </Animated.View>
        </Modal>
      )}

      {/* ── Top bar ────────────────────────────────────────────────────── */}
      <View style={[dynStyles.topBar, {backgroundColor: C.headerBg}]}>
        <TouchableOpacity onPress={openSidebar} style={dynStyles.iconBtn}>
          <Ionicons name="menu" size={24} color={C.headerText} />
        </TouchableOpacity>
        <View style={{flexDirection:'row'}}>
          <Text style={[dynStyles.topLogo,{color:SprintColors.green}]}>Parki</Text>
          <Text style={[dynStyles.topLogo,{color:SprintColors.yellow}]}>Pay</Text>
        </View>
        <TouchableOpacity style={dynStyles.iconBtn}>
          <Ionicons name="notifications-outline" size={22} color={C.headerText} />
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={[dynStyles.body,{backgroundColor:C.bg}]}
        showsVerticalScrollIndicator={false}>

        {/* ── Active Session card ────────────────────────────────────── */}
        <LinearGradient colors={['#1EB53A','#158A2A']}
          start={{x:0,y:0}} end={{x:1,y:1}} style={dynStyles.sessionCard}>
          <View style={dynStyles.sessionTop}>
            <View>
              <Text style={dynStyles.sessionLabel}>{tr('activeSession')}</Text>
              <Text style={dynStyles.sessionName}>{officer.fullName}</Text>
              <Text style={dynStyles.sessionZone}>
                <Ionicons name="location-outline" size={13} color="#cfffdf" />
                {'  '}{officer.locationName ?? 'Unassigned'}
              </Text>
            </View>
            <TouchableOpacity onPress={() => setOnDuty(v=>!v)}
              style={[dynStyles.dutyBadge, !onDuty && dynStyles.dutyBadgeOff]}>
              <View style={[dynStyles.dutyDot, !onDuty && {backgroundColor:'#9CA3AF'}]} />
              <Text style={dynStyles.dutyText}>{onDuty ? tr('onDuty') : tr('offDuty')}</Text>
            </TouchableOpacity>
          </View>
          <Text style={dynStyles.sessionDate}>{today}</Text>
        </LinearGradient>

        {/* ── Stats row ─────────────────────────────────────────────── */}
        <View style={dynStyles.statsRow}>
          <View style={[dynStyles.statCard, {backgroundColor: C.statCard}]}>
            <MaterialCommunityIcons name="file-document-outline" size={22} color={C.accent} />
            <Text style={[dynStyles.statVal, {color: C.text}]}>24</Text>
            <Text style={[dynStyles.statLabel, {color: C.textSub}]}>{tr('totalBills')}</Text>
          </View>
          <View style={[dynStyles.statCard, {backgroundColor: C.statCard}]}>
            <MaterialCommunityIcons name="cash-multiple" size={22} color={C.accent} />
            <Text style={[dynStyles.statVal, {color: C.text}]}>48k</Text>
            <Text style={[dynStyles.statLabel, {color: C.textSub}]}>{tr('amountCollected')}</Text>
          </View>
        </View>

        {/* ── CTA ───────────────────────────────────────────────────── */}
        <TouchableOpacity style={dynStyles.ctaBtn} activeOpacity={0.85}>
          <Ionicons name="search" size={20} color="#1A1A1A" />
          <Text style={dynStyles.ctaText}>{tr('newLookup')}</Text>
        </TouchableOpacity>

        {/* ── Recent Bills ──────────────────────────────────────────── */}
        <View style={dynStyles.sectionHeader}>
          <Text style={[dynStyles.sectionTitle, {color: C.text}]}>{tr('recentBills')}</Text>
          <TouchableOpacity>
            <Text style={[dynStyles.viewAll, {color: C.accent}]}>{tr('viewAll')}</Text>
          </TouchableOpacity>
        </View>

        {MOCK_BILLS.length === 0
          ? <View style={[dynStyles.emptyCard, {backgroundColor: C.card}]}>
              <MaterialCommunityIcons name="car-off" size={36} color={C.textMuted} />
              <Text style={[dynStyles.emptyText, {color: C.textMuted}]}>{tr('noBills')}</Text>
            </View>
          : MOCK_BILLS.map(bill => (
            <View key={bill.id} style={[dynStyles.billCard, {backgroundColor: C.card}]}>
              <View style={dynStyles.billIcon}>
                <MaterialCommunityIcons name="car-outline" size={22} color={C.accent} />
              </View>
              <View style={{flex:1}}>
                <Text style={[dynStyles.billPlate, {color: C.text}]}>{bill.plate}</Text>
                <Text style={[dynStyles.billMeta, {color: C.textSub}]}>
                  {bill.amount} {tr('tzs')} · {bill.time}
                </Text>
              </View>
              <View style={[dynStyles.statusBadge,
                bill.status==='paid' ? dynStyles.badgePaid : dynStyles.badgePending]}>
                <Text style={dynStyles.statusText}>
                  {bill.status==='paid' ? tr('paid') : tr('pending')}
                </Text>
              </View>
            </View>
          ))
        }

        <View style={{height: 24}} />
      </ScrollView>

      {/* ── Bottom Tab Bar ────────────────────────────────────────────── */}
      <View style={[dynStyles.tabBar, {backgroundColor: C.navBg, borderTopColor: C.navBorder}]}>
        {[
          { icon:'grid-outline',    label: tr('dashboard'), active: true  },
          { icon:'search-outline',  label: tr('lookup'),    active: false },
          { icon:'time-outline',    label: tr('history'),   active: false },
          { icon:'alert-circle-outline', label: tr('alerts'), active: false },
        ].map((tab,i) => (
          <TouchableOpacity key={i} style={dynStyles.tabItem}>
            <Ionicons name={tab.icon as any} size={22}
              color={tab.active ? C.navActive : C.textMuted} />
            <Text style={[dynStyles.tabLabel,
              {color: tab.active ? C.navActive : C.textMuted}]}>{tab.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </SafeAreaView>
  );
}

function makeStyles(C: ReturnType<typeof palette>) {
  return StyleSheet.create({
    root:{ flex:1 },
    overlay:{ ...StyleSheet.absoluteFillObject, backgroundColor:'rgba(0,0,0,0.5)' },
    sidebar:{
      position:'absolute', left:0, top:0, bottom:0, width:SIDEBAR_W,
      backgroundColor: C.sidebarBg, paddingTop:56, paddingHorizontal:20, zIndex:99,
    },
    sbHeader:{ flexDirection:'row', justifyContent:'space-between',
      alignItems:'center', marginBottom:28 },
    sbHeaderText:{ fontSize:17, fontWeight:'700', color: C.sidebarText },
    sbSection:{ fontSize:11, fontWeight:'700', color:'#6B7280',
      letterSpacing:1.2, textTransform:'uppercase', marginBottom:10, marginTop:4 },
    toggleRow:{ flexDirection:'row', gap:8, marginBottom:20 },
    toggleBtn:{ flex:1, paddingVertical:9, borderRadius:8, alignItems:'center',
      justifyContent:'center', flexDirection:'row', gap:5,
      backgroundColor:'rgba(255,255,255,0.08)' },
    toggleActive:{ backgroundColor: SprintColors.green },
    toggleText:{ fontSize:13, color: C.sidebarText, fontWeight:'600' },
    toggleActiveText:{ color:'#fff' },
    sbDivider:{ height:1, backgroundColor:'rgba(255,255,255,0.1)', marginVertical:16 },
    logoutBtn:{ flexDirection:'row', alignItems:'center', gap:10,
      paddingVertical:12, paddingHorizontal:14, borderRadius:10,
      backgroundColor:'rgba(239,68,68,0.12)' },
    logoutText:{ color:'#EF4444', fontWeight:'700', fontSize:15 },

    topBar:{ flexDirection:'row', alignItems:'center', justifyContent:'space-between',
      paddingHorizontal:16, paddingVertical:12 },
    topLogo:{ fontSize:22, fontWeight:'900', letterSpacing:0.5 },
    iconBtn:{ padding:4 },

    body:{ padding:16 },

    sessionCard:{ borderRadius:16, padding:18, marginBottom:14 },
    sessionTop:{ flexDirection:'row', justifyContent:'space-between', alignItems:'flex-start' },
    sessionLabel:{ fontSize:11, color:'#cfffdf', fontWeight:'600',
      textTransform:'uppercase', letterSpacing:1, marginBottom:4 },
    sessionName:{ fontSize:18, fontWeight:'800', color:'#fff', marginBottom:2 },
    sessionZone:{ fontSize:13, color:'#cfffdf' },
    sessionDate:{ fontSize:12, color:'rgba(255,255,255,0.6)', marginTop:12 },
    dutyBadge:{ flexDirection:'row', alignItems:'center', gap:5,
      backgroundColor:'rgba(255,255,255,0.2)', paddingHorizontal:10,
      paddingVertical:6, borderRadius:20 },
    dutyBadgeOff:{ backgroundColor:'rgba(0,0,0,0.2)' },
    dutyDot:{ width:7, height:7, borderRadius:4, backgroundColor:'#86efac' },
    dutyText:{ color:'#fff', fontSize:11, fontWeight:'800', letterSpacing:0.5 },

    statsRow:{ flexDirection:'row', gap:12, marginBottom:14 },
    statCard:{ flex:1, borderRadius:14, padding:16, alignItems:'center', gap:6,
      shadowColor:'#000', shadowOffset:{width:0,height:2},
      shadowOpacity:0.06, shadowRadius:6, elevation:3 },
    statVal:{ fontSize:24, fontWeight:'800' },
    statLabel:{ fontSize:11, textAlign:'center', fontWeight:'600' },

    ctaBtn:{ flexDirection:'row', alignItems:'center', justifyContent:'center',
      gap:10, height:52, backgroundColor: SprintColors.yellow,
      borderRadius:14, marginBottom:20 },
    ctaText:{ fontSize:15, fontWeight:'800', color:'#1A1A1A', letterSpacing:0.3 },

    sectionHeader:{ flexDirection:'row', justifyContent:'space-between',
      alignItems:'center', marginBottom:10 },
    sectionTitle:{ fontSize:16, fontWeight:'800' },
    viewAll:{ fontSize:13, fontWeight:'600' },

    emptyCard:{ alignItems:'center', padding:32, borderRadius:14, gap:8 },
    emptyText:{ fontSize:14 },

    billCard:{ flexDirection:'row', alignItems:'center', gap:12,
      borderRadius:14, padding:14, marginBottom:8,
      shadowColor:'#000', shadowOffset:{width:0,height:1},
      shadowOpacity:0.05, shadowRadius:4, elevation:2 },
    billIcon:{ width:40, height:40, borderRadius:10,
      backgroundColor:'rgba(30,181,58,0.1)', alignItems:'center', justifyContent:'center' },
    billPlate:{ fontSize:15, fontWeight:'700' },
    billMeta:{ fontSize:12, marginTop:2 },
    statusBadge:{ paddingHorizontal:10, paddingVertical:4, borderRadius:20 },
    badgePaid:{ backgroundColor:'rgba(30,181,58,0.12)' },
    badgePending:{ backgroundColor:'rgba(252,209,22,0.2)' },
    statusText:{ fontSize:10, fontWeight:'800', letterSpacing:0.5, color:'#1A1A1A' },

    tabBar:{ flexDirection:'row', borderTopWidth:1, paddingBottom:6, paddingTop:8 },
    tabItem:{ flex:1, alignItems:'center', gap:3 },
    tabLabel:{ fontSize:10, fontWeight:'600' },
  });
}
'''

# ─── 7. app/(app)/admin.tsx ───────────────────────────────────────────────────
ADMIN = p("mobile","app","(app)","admin.tsx")

ADMIN_CONTENT = r'''/**
 * ParkiPay — Admin Screen (simple officer management)
 */
import { useState, useEffect, useCallback } from 'react';
import {
  ActivityIndicator, Alert, FlatList, Modal, Pressable,
  SafeAreaView, StyleSheet, Text, TextInput,
  TouchableOpacity, View,
} from 'react-native';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useAuthStore } from '@/store/authStore';
import { useSettingsStore, palette } from '@/store/settingsStore';
import { t } from '@/constants/i18n';
import { adminService } from '@/services/api';
import { SprintColors } from '@/constants/theme';

interface Officer { id:number; employeeId:string; fullName:string; locationName:string|null; role:string; }
interface Location { id:number; name:string; region:string; }

const ROLE_COLORS: Record<string,string> = {
  FIELD_OFFICER: SprintColors.green, SUPERVISOR: '#1565C0', ADMIN: '#6A1B9A',
};

export default function AdminScreen() {
  const { clearAuth, refreshToken, officer: me } = useAuthStore();
  const { language, theme } = useSettingsStore();
  const C = palette(theme);
  const tr = (k:string) => t(language, k);

  const [officers,   setOfficers]   = useState<Officer[]>([]);
  const [locations,  setLocations]  = useState<Location[]>([]);
  const [loading,    setLoading]    = useState(true);
  const [showAdd,    setShowAdd]    = useState(false);
  const [showMove,   setShowMove]   = useState<Officer|null>(null);
  const [newName,    setNewName]    = useState('');
  const [newEmpId,   setNewEmpId]   = useState('');
  const [newLocId,   setNewLocId]   = useState<number|null>(null);
  const [saving,     setSaving]     = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [oRes, lRes] = await Promise.all([
        adminService.listOfficers(),
        adminService.listLocations(),
      ]);
      setOfficers(oRes.data);
      setLocations(lRes.data);
    } catch { Alert.alert('Error','Failed to load data'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleAdd = async () => {
    if (!newName.trim() || !newEmpId.trim()) {
      Alert.alert('', 'Name and Employee ID are required'); return;
    }
    setSaving(true);
    try {
      await adminService.createOfficer({ fullName:newName.trim(),
        employeeId:newEmpId.trim().toUpperCase(), locationId:newLocId });
      setShowAdd(false); setNewName(''); setNewEmpId(''); setNewLocId(null);
      load();
    } catch (e:any) {
      Alert.alert('Error', e?.response?.data?.detail ?? 'Failed to create officer');
    } finally { setSaving(false); }
  };

  const handleRemove = (o:Officer) => {
    Alert.alert(tr('confirmRemove'), o.fullName, [
      { text: tr('cancel'), style:'cancel' },
      { text: tr('remove'), style:'destructive', onPress: async () => {
        try { await adminService.removeOfficer(o.id); load(); }
        catch { Alert.alert('Error','Failed to remove officer'); }
      }},
    ]);
  };

  const handleMove = async (locationId: number) => {
    if (!showMove) return;
    try {
      await adminService.moveOfficer(showMove.id, locationId);
      setShowMove(null); load();
    } catch { Alert.alert('Error','Failed to move officer'); }
  };

  const handleLogout = async () => {
    try { if (refreshToken) await (await import('@/services/api')).authService.logout(refreshToken); }
    catch {}
    await clearAuth(); router.replace('/(auth)/login');
  };

  return (
    <SafeAreaView style={[styles.root, {backgroundColor: C.bg}]}>
      {/* Header */}
      <View style={[styles.header, {backgroundColor: C.headerBg}]}>
        <Text style={[styles.headerTitle, {color: C.headerText}]}>{tr('adminPanel')}</Text>
        <TouchableOpacity onPress={handleLogout} style={styles.logoutBtn}>
          <Ionicons name="log-out-outline" size={20} color="#EF4444" />
        </TouchableOpacity>
      </View>

      {/* Officers list */}
      {loading
        ? <ActivityIndicator style={{flex:1}} color={SprintColors.green} size="large" />
        : <FlatList
            data={officers}
            keyExtractor={o => String(o.id)}
            contentContainerStyle={{padding:16, paddingBottom:100}}
            ListEmptyComponent={
              <View style={styles.emptyWrap}>
                <MaterialCommunityIcons name="account-off-outline" size={48} color={C.textMuted}/>
                <Text style={[styles.emptyText,{color:C.textMuted}]}>{tr('noOfficers')}</Text>
              </View>
            }
            renderItem={({item:o}) => (
              <View style={[styles.card, {backgroundColor: C.card}]}>
                <View style={{flex:1}}>
                  <View style={{flexDirection:'row', alignItems:'center', gap:8, marginBottom:4}}>
                    <View style={[styles.roleChip,{backgroundColor:ROLE_COLORS[o.role]??SprintColors.green}]}>
                      <Text style={styles.roleText}>
                        {o.role==='FIELD_OFFICER' ? tr('fieldOfficer') : tr('supervisor')}
                      </Text>
                    </View>
                  </View>
                  <Text style={[styles.name,{color:C.text}]}>{o.fullName}</Text>
                  <Text style={[styles.meta,{color:C.textSub}]}>ID: {o.employeeId}</Text>
                  {o.locationName
                    ? <Text style={[styles.meta,{color:C.textSub}]}>
                        <Ionicons name="location-outline" size={12}/> {o.locationName}
                      </Text>
                    : <Text style={[styles.meta,{color:C.textMuted}]}>Unassigned</Text>}
                </View>
                <View style={styles.actions}>
                  <TouchableOpacity style={styles.actionBtn} onPress={()=>setShowMove(o)}>
                    <Ionicons name="swap-horizontal-outline" size={18} color={SprintColors.green}/>
                  </TouchableOpacity>
                  <TouchableOpacity style={[styles.actionBtn,{backgroundColor:'rgba(239,68,68,0.08)'}]}
                    onPress={()=>handleRemove(o)}>
                    <Ionicons name="trash-outline" size={18} color="#EF4444"/>
                  </TouchableOpacity>
                </View>
              </View>
            )}
          />
      }

      {/* FAB */}
      <TouchableOpacity style={styles.fab} onPress={()=>setShowAdd(true)}>
        <Ionicons name="person-add-outline" size={22} color="#fff"/>
        <Text style={styles.fabText}>{tr('addOfficer')}</Text>
      </TouchableOpacity>

      {/* ── Add Officer Modal ──────────────────────────────────────────── */}
      <Modal visible={showAdd} transparent animationType="slide" onRequestClose={()=>setShowAdd(false)}>
        <Pressable style={styles.backdrop} onPress={()=>setShowAdd(false)}/>
        <View style={[styles.sheet, {backgroundColor: C.card}]}>
          <Text style={[styles.sheetTitle,{color:C.text}]}>{tr('addOfficer')}</Text>

          <Text style={[styles.inputLabel,{color:C.textSub}]}>{tr('officerName')}</Text>
          <TextInput style={[styles.input,{color:C.text,borderColor:C.border,backgroundColor:C.bg}]}
            value={newName} onChangeText={setNewName} placeholder="e.g. Juma Ally"
            placeholderTextColor={C.textMuted}/>

          <Text style={[styles.inputLabel,{color:C.textSub}]}>{tr('employeeIdLabel')}</Text>
          <TextInput style={[styles.input,{color:C.text,borderColor:C.border,backgroundColor:C.bg}]}
            value={newEmpId} onChangeText={setNewEmpId} placeholder="e.g. TZ-1234"
            autoCapitalize="characters" placeholderTextColor={C.textMuted}/>

          <Text style={[styles.inputLabel,{color:C.textSub}]}>{tr('selectLocation')}</Text>
          <View style={styles.locGrid}>
            {locations.map(loc => (
              <TouchableOpacity key={loc.id}
                style={[styles.locChip, newLocId===loc.id && styles.locChipActive]}
                onPress={()=>setNewLocId(loc.id)}>
                <Text style={[styles.locChipText, newLocId===loc.id && {color:'#fff'}]}>
                  {loc.name}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <TouchableOpacity style={[styles.saveBtn, saving && {opacity:0.6}]}
            onPress={handleAdd} disabled={saving}>
            {saving ? <ActivityIndicator color="#fff"/> :
              <Text style={styles.saveBtnText}>{tr('save')}</Text>}
          </TouchableOpacity>
        </View>
      </Modal>

      {/* ── Move Location Modal ────────────────────────────────────────── */}
      <Modal visible={!!showMove} transparent animationType="slide" onRequestClose={()=>setShowMove(null)}>
        <Pressable style={styles.backdrop} onPress={()=>setShowMove(null)}/>
        <View style={[styles.sheet,{backgroundColor:C.card}]}>
          <Text style={[styles.sheetTitle,{color:C.text}]}>{tr('moveLocation')}: {showMove?.fullName}</Text>
          <View style={styles.locGrid}>
            {locations.map(loc => (
              <TouchableOpacity key={loc.id} style={styles.locChip} onPress={()=>handleMove(loc.id)}>
                <Text style={styles.locChipText}>{loc.name}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root:{ flex:1 },
  header:{ flexDirection:'row', alignItems:'center', justifyContent:'space-between',
    paddingHorizontal:16, paddingVertical:14 },
  headerTitle:{ fontSize:18, fontWeight:'800' },
  logoutBtn:{ padding:6 },
  emptyWrap:{ alignItems:'center', marginTop:60, gap:12 },
  emptyText:{ fontSize:15 },
  card:{ borderRadius:14, padding:16, marginBottom:10, flexDirection:'row',
    alignItems:'center', shadowColor:'#000', shadowOffset:{width:0,height:2},
    shadowOpacity:0.06, shadowRadius:5, elevation:3 },
  roleChip:{ paddingHorizontal:8, paddingVertical:3, borderRadius:20 },
  roleText:{ fontSize:10, color:'#fff', fontWeight:'700' },
  name:{ fontSize:15, fontWeight:'700', marginBottom:2 },
  meta:{ fontSize:12, marginTop:1 },
  actions:{ flexDirection:'row', gap:8 },
  actionBtn:{ width:36, height:36, borderRadius:10, alignItems:'center',
    justifyContent:'center', backgroundColor:'rgba(30,181,58,0.08)' },
  fab:{ position:'absolute', bottom:24, right:20, flexDirection:'row',
    alignItems:'center', gap:8, backgroundColor: SprintColors.green,
    paddingHorizontal:18, paddingVertical:14, borderRadius:30,
    shadowColor:SprintColors.green, shadowOffset:{width:0,height:4},
    shadowOpacity:0.4, shadowRadius:8, elevation:8 },
  fabText:{ color:'#fff', fontWeight:'800', fontSize:14 },
  backdrop:{ flex:1, backgroundColor:'rgba(0,0,0,0.5)' },
  sheet:{ borderTopLeftRadius:20, borderTopRightRadius:20, padding:24, paddingBottom:40 },
  sheetTitle:{ fontSize:18, fontWeight:'800', marginBottom:16 },
  inputLabel:{ fontSize:13, fontWeight:'600', marginBottom:6 },
  input:{ height:48, borderWidth:1.5, borderRadius:10, paddingHorizontal:14,
    fontSize:15, marginBottom:14 },
  locGrid:{ flexDirection:'row', flexWrap:'wrap', gap:8, marginBottom:20 },
  locChip:{ paddingHorizontal:12, paddingVertical:7, borderRadius:20,
    backgroundColor:'rgba(30,181,58,0.08)', borderWidth:1.5,
    borderColor: SprintColors.green },
  locChipActive:{ backgroundColor: SprintColors.green },
  locChipText:{ fontSize:12, fontWeight:'600', color: SprintColors.green },
  saveBtn:{ height:52, backgroundColor: SprintColors.green, borderRadius:12,
    alignItems:'center', justifyContent:'center' },
  saveBtnText:{ color:'#fff', fontSize:15, fontWeight:'800' },
});
'''

# ─── 8. app/(app)/_layout.tsx ────────────────────────────────────────────────
APP_LAYOUT = p("mobile","app","(app)","_layout.tsx")

APP_LAYOUT_CONTENT = r'''/** ParkiPay — App Stack Layout */
import { useEffect } from 'react';
import { Stack, router } from 'expo-router';
import { useAuthStore } from '@/store/authStore';
import { useSettingsStore } from '@/store/settingsStore';

export default function AppLayout() {
  const { isAuthenticated } = useAuthStore();
  const { loadSettings }    = useSettingsStore();

  useEffect(() => { loadSettings(); }, []);
  useEffect(() => {
    if (!isAuthenticated) router.replace('/(auth)/login');
  }, [isAuthenticated]);

  return (
    <Stack screenOptions={{ headerShown: false, animation: 'slide_from_right' }}>
      <Stack.Screen name="home"  />
      <Stack.Screen name="admin" />
    </Stack>
  );
}
'''

# ─── 9. services/api.ts additions ────────────────────────────────────────────
API_SERVICE = p("mobile","services","api.ts")

API_ADDITIONS = '''
// ── Auth: ID-only login ───────────────────────────────────────────────────────
export const authService = {
  loginById: (employee_id: string) =>
    apiClient.post('/api/auth/login/', { employee_id }),
  logout: (refresh: string) =>
    apiClient.post('/api/auth/logout/', { refresh }),
  me: () => apiClient.get('/api/auth/me/'),
};

// ── Admin service ─────────────────────────────────────────────────────────────
export const adminService = {
  listOfficers:  ()                    => apiClient.get('/api/admin/officers/'),
  listLocations: ()                    => apiClient.get('/api/admin/locations/'),
  createOfficer: (body: object)        => apiClient.post('/api/admin/officers/', body),
  removeOfficer: (id: number)          => apiClient.delete(`/api/admin/officers/${id}/`),
  moveOfficer:   (id: number, locId: number) =>
    apiClient.patch(`/api/admin/officers/${id}/location/`, { locationId: locId }),
};
'''

# ─── 10. backend/src/routes/auth.js — ID-only login ─────────────────────────
BACKEND_AUTH = p("backend","src","routes","auth.js")

BACKEND_AUTH_CONTENT = r"""/**
 * ParkiPay — Auth routes  (v2: employee-ID only, no password)
 *
 * POST /api/auth/login/    — { employee_id } → { access, refresh, officer }
 * POST /api/auth/refresh/  — { refresh }
 * POST /api/auth/logout/   — 200 OK
 * GET  /api/auth/me/       — officer profile
 */
const { Router }       = require('express');
const { z }            = require('zod');
const cfg              = require('../config');
const prisma           = require('../lib/prisma');
const jwtLib           = require('../lib/jwt');
const logAction        = require('../lib/audit');
const { authenticate } = require('../middleware/auth');

const router = Router();

function officerProfile(o) {
  return {
    id:           o.id,
    employeeId:   o.employeeId,
    fullName:     o.fullName,
    phone:        o.phone,
    email:        o.email,
    role:         o.role,
    locationName: o.location ? `${o.location.name}, ${o.location.region}` : null,
    isActive:     o.isActive,
    lastLogin:    o.lastLogin,
  };
}

// ── POST /api/auth/login/ ─────────────────────────────────────────────────────

const LoginSchema = z.object({
  employee_id: z.string().min(1, 'employee_id is required'),
});

router.post('/login/', async (req, res, next) => {
  try {
    const parsed = LoginSchema.safeParse(req.body);
    if (!parsed.success) {
      return res.status(400).json({ error: 'validation_error', detail: parsed.error.flatten() });
    }

    const { employee_id: employeeId } = parsed.data;

    const officer = await prisma.officer.findUnique({
      where:   { employeeId },
      include: { location: true },
    });

    if (!officer || !officer.isActive) {
      await logAction(null, 'LOGIN_FAILURE', { result: 'not_found', req });
      return res.status(401).json({
        error:  'invalid_credentials',
        detail: 'Employee ID not found or account is inactive.',
      });
    }

    // Update last login
    await prisma.officer.update({
      where: { id: officer.id },
      data:  { lastLogin: new Date(), failedLoginAttempts: 0 },
    });

    const access             = jwtLib.signAccess(officer);
    const { token: refresh } = jwtLib.signRefresh(officer);

    await logAction(officer, 'LOGIN_SUCCESS', { result: 'success', req });
    return res.json({ access, refresh, officer: officerProfile(officer) });
  } catch (err) { next(err); }
});

// ── POST /api/auth/refresh/ ───────────────────────────────────────────────────

router.post('/refresh/', async (req, res, next) => {
  try {
    const { refresh } = req.body;
    if (!refresh) return res.status(400).json({ error: 'refresh_required' });

    let payload;
    try { payload = jwtLib.verify(refresh); }
    catch { return res.status(401).json({ error: 'invalid_token' }); }

    if (await jwtLib.isBlacklisted(payload.jti))
      return res.status(401).json({ error: 'token_blacklisted' });

    await jwtLib.blacklist(payload.jti, payload.exp);

    const officer = await prisma.officer.findUnique({ where: { id: parseInt(payload.sub, 10) } });
    if (!officer || !officer.isActive)
      return res.status(401).json({ error: 'unauthorized' });

    const access              = jwtLib.signAccess(officer);
    const { token: newRefresh } = jwtLib.signRefresh(officer);
    return res.json({ access, refresh: newRefresh });
  } catch (err) { next(err); }
});

// ── POST /api/auth/logout/ ────────────────────────────────────────────────────

router.post('/logout/', async (req, res, next) => {
  try {
    const { refresh } = req.body;
    if (!refresh) return res.status(400).json({ error: 'refresh_required' });
    let payload;
    try { payload = jwtLib.verify(refresh); } catch { return res.json({ detail: 'Logged out.' }); }
    if (!(await jwtLib.isBlacklisted(payload.jti))) await jwtLib.blacklist(payload.jti, payload.exp);
    return res.json({ detail: 'Logged out successfully.' });
  } catch (err) { next(err); }
});

// ── GET /api/auth/me/ ─────────────────────────────────────────────────────────

router.get('/me/', authenticate, (req, res) => res.json(officerProfile(req.officer)));

module.exports = router;
"""

# ─── 11. backend/src/routes/admin.js ─────────────────────────────────────────
ADMIN_ROUTE = p("backend","src","routes","admin.js")

ADMIN_ROUTE_CONTENT = r"""/**
 * ParkiPay — Admin routes  (simple officer management)
 *
 * All routes require a valid JWT with role SUPERVISOR or ADMIN.
 *
 * GET    /api/admin/officers/              — list all officers
 * POST   /api/admin/officers/              — create officer
 * DELETE /api/admin/officers/:id/          — remove officer
 * PATCH  /api/admin/officers/:id/location/ — move officer to location
 * GET    /api/admin/locations/             — list parking locations
 */
const { Router } = require('express');
const { z }      = require('zod');
const prisma     = require('../lib/prisma');
const { authenticate } = require('../middleware/auth');

const router = Router();

// ── Middleware: admin/supervisor only ─────────────────────────────────────────
function adminOnly(req, res, next) {
  const role = req.officer?.role;
  if (role !== 'SUPERVISOR' && role !== 'ADMIN') {
    return res.status(403).json({ error: 'forbidden', detail: 'Supervisor or Admin role required.' });
  }
  next();
}

router.use(authenticate, adminOnly);

// ── GET /api/admin/officers/ ──────────────────────────────────────────────────
router.get('/officers/', async (req, res, next) => {
  try {
    const officers = await prisma.officer.findMany({
      include: { location: true },
      orderBy: { createdAt: 'asc' },
    });
    res.json(officers.map(o => ({
      id:           o.id,
      employeeId:   o.employeeId,
      fullName:     o.fullName,
      role:         o.role,
      isActive:     o.isActive,
      locationName: o.location ? `${o.location.name}` : null,
      locationId:   o.locationId,
    })));
  } catch (err) { next(err); }
});

// ── POST /api/admin/officers/ ─────────────────────────────────────────────────
const CreateSchema = z.object({
  employeeId: z.string().min(2).max(20),
  fullName:   z.string().min(2),
  locationId: z.number().int().positive().nullable().optional(),
  role:       z.enum(['FIELD_OFFICER','SUPERVISOR']).default('FIELD_OFFICER'),
});

router.post('/officers/', async (req, res, next) => {
  try {
    const parsed = CreateSchema.safeParse(req.body);
    if (!parsed.success)
      return res.status(400).json({ error: 'validation_error', detail: parsed.error.flatten() });

    const { employeeId, fullName, locationId, role } = parsed.data;
    const exists = await prisma.officer.findUnique({ where: { employeeId } });
    if (exists)
      return res.status(409).json({ error: 'duplicate', detail: 'Employee ID already exists.' });

    const officer = await prisma.officer.create({
      data: { employeeId, fullName, role,
        passwordHash: '', // no password — ID-only auth
        locationId:   locationId ?? null },
      include: { location: true },
    });

    res.status(201).json({
      id: officer.id, employeeId: officer.employeeId,
      fullName: officer.fullName, role: officer.role,
      locationName: officer.location?.name ?? null,
    });
  } catch (err) { next(err); }
});

// ── DELETE /api/admin/officers/:id/ ──────────────────────────────────────────
router.delete('/officers/:id/', async (req, res, next) => {
  try {
    const id = parseInt(req.params.id, 10);
    await prisma.officer.delete({ where: { id } });
    res.json({ detail: 'Officer removed.' });
  } catch (err) { next(err); }
});

// ── PATCH /api/admin/officers/:id/location/ ───────────────────────────────────
router.patch('/officers/:id/location/', async (req, res, next) => {
  try {
    const id         = parseInt(req.params.id, 10);
    const locationId = parseInt(req.body.locationId, 10);
    const officer = await prisma.officer.update({
      where: { id },
      data:  { locationId },
      include: { location: true },
    });
    res.json({ id: officer.id, locationName: officer.location?.name ?? null });
  } catch (err) { next(err); }
});

// ── GET /api/admin/locations/ ─────────────────────────────────────────────────
router.get('/locations/', async (req, res, next) => {
  try {
    const locs = await prisma.parkingLocation.findMany({
      where:   { isActive: true },
      orderBy: { name: 'asc' },
      select:  { id:true, name:true, region:true },
    });
    res.json(locs);
  } catch (err) { next(err); }
});

module.exports = router;
"""

# ─── 12. backend/src/app.js — add admin route ────────────────────────────────
BACKEND_APP = p("backend","src","app.js")

# ─── 13. SQL patch ────────────────────────────────────────────────────────────
SQL_PATCH = p("patch_v2_supervisor.sql")

SQL_CONTENT = """-- ParkiPay v2 — Add supervisor officer for admin screen access
-- Run in Supabase SQL Editor

-- Add a supervisor (can access admin panel)
INSERT INTO officers (employee_id, full_name, phone, email, role, password_hash, location_id, is_active, updated_at)
VALUES (
  'SUP-001', 'Supervisor Admin', '+255700000099', 'supervisor@parkipay.go.tz',
  'SUPERVISOR', '', 1, TRUE, NOW()
)
ON CONFLICT (employee_id) DO NOTHING;

-- Make existing officers have empty password_hash (ID-only auth)
UPDATE officers SET password_hash = '', updated_at = NOW()
WHERE password_hash != '' AND role != 'ADMIN';

-- Verify
SELECT employee_id, full_name, role, is_active FROM officers ORDER BY id;
"""

# ═════════════════════════════════════════════════════════════════════════════
# Apply all patches
# ═════════════════════════════════════════════════════════════════════════════
def main():
    print("\n── ParkiPay v2 patch ────────────────────────────────────────────────\n")

    print("[1]  login.tsx — ID-only form")
    bak(LOGIN); write(LOGIN, LOGIN_CONTENT)

    print("[2]  hooks/useAuth.ts — loginById, no password")
    bak(USE_AUTH); write(USE_AUTH, USE_AUTH_CONTENT)

    print("[3]  store/authStore.ts — camelCase OfficerProfile")
    bak(AUTH_STORE); write(AUTH_STORE, AUTH_STORE_CONTENT)

    print("[4]  store/settingsStore.ts — language + theme")
    write(SETTINGS_STORE, SETTINGS_STORE_CONTENT)

    print("[5]  constants/i18n.ts — EN/SW translations")
    write(I18N, I18N_CONTENT)

    print("[6]  app/(app)/home.tsx — dashboard redesign")
    bak(HOME); write(HOME, HOME_CONTENT)

    print("[7]  app/(app)/admin.tsx — admin screen")
    write(ADMIN, ADMIN_CONTENT)

    print("[8]  app/(app)/_layout.tsx — register admin screen")
    bak(APP_LAYOUT); write(APP_LAYOUT, APP_LAYOUT_CONTENT)

    print("[9]  services/api.ts — loginById + adminService")
    bak(API_SERVICE)
    api = read(API_SERVICE)
    # Remove old authService / biometricService blocks and append clean ones
    # Find the last export statement and append after
    if "export const authService" not in api or "adminService" not in api:
        # Remove old authService if present
        import re
        api = re.sub(r'export const authService[\s\S]*?};', '', api)
        api = re.sub(r'// ── Biometric Auth Service[\s\S]*', '', api)
        write(API_SERVICE, api.rstrip() + "\n" + API_ADDITIONS)
    else:
        print("   [–] already patched, skipped")

    print("[10] backend/src/routes/auth.js — ID-only login")
    bak(BACKEND_AUTH); write(BACKEND_AUTH, BACKEND_AUTH_CONTENT)

    print("[11] backend/src/routes/admin.js — officer CRUD")
    write(ADMIN_ROUTE, ADMIN_ROUTE_CONTENT)

    print("[12] backend/src/app.js — mount /api/admin/")
    bak(BACKEND_APP)
    app_js = read(BACKEND_APP)
    if "/api/admin/" not in app_js:
        app_js = app_js.replace(
            "app.use('/api/billing/',  require('./routes/billing'));",
            "app.use('/api/billing/',  require('./routes/billing'));\napp.use('/api/admin/',    require('./routes/admin'));"
        )
        write(BACKEND_APP, app_js)
    else:
        print("   [–] admin route already mounted")

    print("[13] patch_v2_supervisor.sql — supervisor seed")
    write(SQL_PATCH, SQL_CONTENT)

    print("""
── Done ────────────────────────────────────────────────────────────────────

 BACKEND — deploy / restart:
   cd PayPark-main/backend
   git add -A && git commit -m "v2: ID-only auth, admin routes" && git push
   (Render redeploys automatically on push)

 SQL — run in Supabase SQL Editor:
   PayPark-main/patch_v2_supervisor.sql

 LOGIN CREDENTIALS (no password):
   Field Officer : TZ-8821   → Officer dashboard
   Supervisor    : SUP-001   → Admin panel

 MOBILE — restart Expo:
   cd PayPark-main/mobile && npx expo start --clear
""")

if __name__ == "__main__":
    main()

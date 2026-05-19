"""
patch_biometric.py
==================
Applies all biometric + UI improvements to the PayPark project:

  1. mobile/app/(auth)/login.tsx
       • Centered, bold "Sign In" heading (full card width)
       • @expo/vector-icons (Ionicons) everywhere – no more emoji
       • Biometric button triggers device fingerprint/face sensor
       • After normal login, prompts user to enrol biometrics
  2. mobile/hooks/useBiometric.ts          (new file)
       • checkAvailability, registerBiometric, loginWithBiometric
  3. mobile/services/api.ts
       • biometricService.register() / .loginWithToken()
  4. mobile/package.json
       • adds expo-local-authentication dependency
  5. backend/src/routes/auth.js
       • POST /api/auth/biometric/register/
       • POST /api/auth/biometric/login/
  6. backend/prisma/schema.prisma
       • OfficerBiometric model (CREATE TABLE IF NOT EXISTS equivalent)
  7. backend/prisma/migrations/biometric/migration.sql  (new file)
       • Raw SQL that safely creates the table and seeds a test row
  8. backend/prisma/migrations/biometric/seed_biometrics.js (new file)
       • Node seed script you can run manually: node seed_biometrics.js

Usage (from project root):
    python patch_biometric.py
"""

import os, sys, json, re

ROOT = os.path.dirname(os.path.abspath(__file__))

def path(*parts):
    return os.path.join(ROOT, *parts)

def read(p):
    with open(p, "r", encoding="utf-8") as f:
        return f.read()

def write(p, content):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [✓] Written  {p}")

def backup(p):
    bak = p + ".bak"
    if os.path.exists(p) and not os.path.exists(bak):
        write(bak, read(p))
        print(f"  [✓] Backup   {bak}")

def patch_json(p, updater):
    data = json.loads(read(p))
    updater(data)
    write(p, json.dumps(data, indent=2) + "\n")

# ─────────────────────────────────────────────────────────────────────────────
# 1. login.tsx
# ─────────────────────────────────────────────────────────────────────────────
LOGIN_TSX = path( "mobile", "app", "(auth)", "login.tsx")

LOGIN_CONTENT = r"""/**
 * ParkiPay — Login Screen  (v2 — biometric + Ionicons)
 * Officer login via employee_id + password, or registered fingerprint/face.
 * After a successful password login the user is offered biometric enrolment.
 */
import { useState, useEffect } from 'react';
import {
  Alert,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
  ActivityIndicator,
} from 'react-native';
import { router } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';

import { useAuth }      from '@/hooks/useAuth';
import { useBiometric } from '@/hooks/useBiometric';
import {
  Colors, SprintColors,
  FontSize, FontWeight,
  Spacing, Radius, Shadows, LetterSpacing,
} from '@/constants/theme';

const NAV_DARK   = '#0D1117';
const BORDER_CLR = '#D1D5DB';
const ICON_CLR   = '#6B7280';

export default function LoginScreen() {
  const { login, isLoading, error, clearError } = useAuth();
  const {
    isAvailable: biometricAvailable,
    hasSavedCredential,
    loginWithBiometric,
    registerBiometric,
    isLoading: bioLoading,
  } = useBiometric();

  const [employeeId, setEmployeeId]     = useState('');
  const [password, setPassword]         = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [localError, setLocalError]     = useState<string | null>(null);

  /* bilingual error */
  const errorMessage: string | null = localError ?? (
    error
      ? error.code === 'account_locked'
        ? `Akaunti yako imefungwa kwa muda.\n(Your account is temporarily locked.)${
            error.lockedUntil
              ? `\nUntil: ${new Date(error.lockedUntil).toLocaleTimeString()}`
              : ''
          }`
        : error.code === 'invalid_credentials'
        ? `Nambari ya utumishi au nenosiri si sahihi.\n(Invalid employee ID or password.)${
            error.remainingAttempts !== undefined
              ? `\nMajaribio yaliyobaki: ${error.remainingAttempts}`
              : ''
          }`
        : 'Hitilafu ya muunganisho. Jaribu tena.\n(Connection error. Please try again.)'
      : null
  );

  const clearErrors = () => { setLocalError(null); clearError(); };

  /* ── password login ────────────────────────────────────────────────────── */
  const handleLogin = async () => {
    clearErrors();
    if (!employeeId.trim()) {
      setLocalError('Tafadhali ingiza nambari yako ya utumishi.\n(Please enter your employee ID.)');
      return;
    }
    if (!password) {
      setLocalError('Tafadhali ingiza nenosiri lako.\n(Please enter your password.)');
      return;
    }

    const result = await login(employeeId.trim(), password);
    if (!result.success) return;

    /* offer biometric enrolment on first successful login */
    if (biometricAvailable && !hasSavedCredential) {
      Alert.alert(
        'Enable Biometric Login',
        'Would you like to use your fingerprint or face to sign in next time?',
        [
          { text: 'Not now', style: 'cancel', onPress: () => router.replace('/(app)/home') },
          {
            text: 'Enable',
            onPress: async () => {
              await registerBiometric(employeeId.trim());
              router.replace('/(app)/home');
            },
          },
        ],
        { cancelable: true },
      );
    } else {
      router.replace('/(app)/home');
    }
  };

  /* ── biometric login ───────────────────────────────────────────────────── */
  const handleBiometric = async () => {
    clearErrors();
    const result = await loginWithBiometric();
    if (result.success) {
      router.replace('/(app)/home');
    } else if (result.error) {
      setLocalError(result.error.message ?? 'Biometric login failed. Please try your password.');
    }
  };

  const busy = isLoading || bioLoading;

  return (
    <KeyboardAvoidingView
      style={styles.root}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        {/* ── Branding ─────────────────────────────────────────────────── */}
        <View style={styles.headerBlock}>
          <LinearGradient
            colors={[SprintColors.green, SprintColors.yellow]}
            start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
            style={styles.headerAccent}
          />
          <View style={styles.wordmarkRow}>
            <Text style={[styles.wordmarkText, { color: SprintColors.green }]}>Parki</Text>
            <Text style={[styles.wordmarkText, { color: SprintColors.yellow }]}>Pay</Text>
          </View>
          <Text style={styles.subtitle}>Mfumo wa Maegesho wa Serikali</Text>
          <Text style={styles.subtitleEn}>Government Parking Management System</Text>
        </View>

        {/* ── Card ─────────────────────────────────────────────────────── */}
        <View style={styles.card}>

          {/* ── "Sign In" heading — centred, bold, full card width ─────── */}
          <Text style={styles.cardTitle}>Sign In</Text>
          <Text style={styles.cardSubtitle}>
            Use your government officer credentials to access the system
          </Text>

          {/* ── Officer ID ───────────────────────────────────────────── */}
          <View style={styles.fieldGroup}>
            <Text style={styles.label}>Officer ID</Text>
            <View style={[styles.inputRow, errorMessage ? styles.inputRowError : null]}>
              <View style={styles.inputIconLeft}>
                <Ionicons name="id-card-outline" size={18} color={errorMessage ? Colors.error : ICON_CLR} />
              </View>
              <TextInput
                style={styles.inputInner}
                value={employeeId}
                onChangeText={(t) => { clearErrors(); setEmployeeId(t); }}
                placeholder="e.g. TZ-8821"
                placeholderTextColor="#9CA3AF"
                autoCapitalize="characters"
                autoCorrect={false}
                returnKeyType="next"
                editable={!busy}
              />
            </View>
          </View>

          {/* ── Secure Password ──────────────────────────────────────── */}
          <View style={styles.fieldGroup}>
            <Text style={styles.label}>Secure Password</Text>
            <View style={[styles.inputRow, errorMessage ? styles.inputRowError : null]}>
              <View style={styles.inputIconLeft}>
                <Ionicons name="lock-closed-outline" size={18} color={errorMessage ? Colors.error : ICON_CLR} />
              </View>
              <TextInput
                style={[styles.inputInner, { paddingRight: 44 }]}
                value={password}
                onChangeText={(t) => { clearErrors(); setPassword(t); }}
                placeholder="••••••••"
                placeholderTextColor="#9CA3AF"
                secureTextEntry={!showPassword}
                autoCorrect={false}
                returnKeyType="done"
                onSubmitEditing={handleLogin}
                editable={!busy}
              />
              <TouchableOpacity
                style={styles.inputIconRight}
                onPress={() => setShowPassword(v => !v)}
                hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
              >
                <Ionicons
                  name={showPassword ? 'eye-off-outline' : 'eye-outline'}
                  size={18}
                  color={ICON_CLR}
                />
              </TouchableOpacity>
            </View>
          </View>

          {/* ── Error banner ─────────────────────────────────────────── */}
          {errorMessage ? (
            <View style={styles.errorBox}>
              <Ionicons name="alert-circle-outline" size={16} color={Colors.error} style={{ marginRight: 6 }} />
              <Text style={[styles.errorText, { flex: 1 }]}>{errorMessage}</Text>
            </View>
          ) : null}

          {/* ── Secure Login button ───────────────────────────────────── */}
          <TouchableOpacity
            style={[styles.loginBtn, busy && styles.loginBtnDisabled]}
            onPress={handleLogin}
            disabled={busy}
            activeOpacity={0.85}
          >
            {isLoading ? (
              <ActivityIndicator color="#fff" size="small" />
            ) : (
              <>
                <Ionicons name="log-in-outline" size={20} color="#fff" />
                <Text style={styles.loginBtnText}>Secure Login</Text>
              </>
            )}
          </TouchableOpacity>

          {/* ── OR divider ───────────────────────────────────────────── */}
          {biometricAvailable && (
            <>
              <View style={styles.orRow}>
                <View style={styles.orLine} />
                <Text style={styles.orText}>OR</Text>
                <View style={styles.orLine} />
              </View>

              {/* ── Biometric button ─────────────────────────────────── */}
              <TouchableOpacity
                style={[styles.biometricBtn, busy && styles.loginBtnDisabled]}
                onPress={handleBiometric}
                disabled={busy}
                activeOpacity={0.8}
              >
                {bioLoading ? (
                  <ActivityIndicator color={NAV_DARK} size="small" />
                ) : (
                  <>
                    <MaterialCommunityIcons name="fingerprint" size={24} color={NAV_DARK} />
                    <Text style={styles.biometricBtnText}>
                      {hasSavedCredential ? 'Biometric Authentication' : 'Set Up Biometrics'}
                    </Text>
                  </>
                )}
              </TouchableOpacity>
            </>
          )}

          {/* ── Forgot password ──────────────────────────────────────── */}
          <Pressable style={styles.forgotRow}>
            <Text style={styles.forgotText}>
              Umesahau nenosiri?{' '}
              <Text style={styles.forgotLink}>Wasiliana na Msimamizi</Text>
            </Text>
          </Pressable>
        </View>

        {/* ── Footer ───────────────────────────────────────────────────── */}
        <View style={styles.footer}>
          <LinearGradient
            colors={[SprintColors.yellow, SprintColors.black]}
            start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
            style={styles.footerAccent}
          />
          <Text style={styles.footerText}>
            © 2026 Serikali ya Tanzania — ParkiPay v1.0
          </Text>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: Colors.backgroundSecondary },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: Spacing.base,
    paddingBottom: Spacing['3xl'],
  },

  /* Header */
  headerBlock: { alignItems: 'center', paddingTop: Spacing['4xl'], paddingBottom: Spacing.xl },
  headerAccent: { width: 180, height: 4, borderRadius: 2, marginBottom: Spacing.lg },
  wordmarkRow: { flexDirection: 'row', alignItems: 'baseline', marginBottom: Spacing.sm },
  wordmarkText: {
    fontSize: FontSize['3xl'],
    fontWeight: FontWeight.black,
    letterSpacing: LetterSpacing.display,
  },
  subtitle: {
    fontSize: FontSize.sm,
    fontWeight: FontWeight.medium,
    color: Colors.grey700,
    textAlign: 'center',
  },
  subtitleEn: { fontSize: FontSize.sm, color: Colors.grey500, textAlign: 'center', marginTop: 2 },

  /* Card */
  card: {
    backgroundColor: Colors.white,
    borderRadius: Radius.lg,
    padding: Spacing.xl,
    ...Shadows.md,
  },

  /* "Sign In" — centred, wide, bold */
  cardTitle: {
    fontSize: 28,
    fontWeight: '800',           // extra-bold
    color: Colors.textPrimary,
    textAlign: 'center',         // centred inside card
    letterSpacing: 0.4,
    marginBottom: Spacing.xs,
    alignSelf: 'stretch',        // full card width
  },
  cardSubtitle: {
    fontSize: FontSize.sm,
    color: Colors.textSecondary,
    lineHeight: 20,
    textAlign: 'center',
    marginBottom: Spacing.xl,
    letterSpacing: 0.1,
  },

  /* Fields */
  fieldGroup: { marginBottom: Spacing.md },
  label: {
    fontSize: FontSize.sm,
    fontWeight: '700',
    color: Colors.textPrimary,
    marginBottom: 6,
    letterSpacing: 0.15,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    height: 54,
    borderWidth: 1.5,
    borderColor: BORDER_CLR,
    borderRadius: Radius.md,
    backgroundColor: Colors.white,
    overflow: 'hidden',
  },
  inputRowError: { borderColor: Colors.error },
  inputIconLeft: { width: 44, alignItems: 'center', justifyContent: 'center' },
  inputIconRight: {
    width: 44,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'absolute',
    right: 0, top: 0, bottom: 0,
  },
  inputInner: {
    flex: 1,
    fontSize: FontSize.base,
    color: Colors.textPrimary,
    paddingVertical: 0,
    letterSpacing: 0.2,
  },

  /* Error */
  errorBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: Colors.errorSurface,
    borderRadius: Radius.md,
    padding: Spacing.md,
    marginBottom: Spacing.base,
    borderLeftWidth: 3,
    borderLeftColor: Colors.error,
  },
  errorText: { fontSize: FontSize.sm, color: Colors.error, lineHeight: 18 },

  /* Secure Login */
  loginBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    height: 56,
    backgroundColor: NAV_DARK,
    borderRadius: Radius.md,
    marginTop: Spacing.sm,
  },
  loginBtnDisabled: { opacity: 0.55 },
  loginBtnText: {
    color: '#fff',
    fontSize: FontSize.base,
    fontWeight: '700',
    letterSpacing: 0.5,
  },

  /* OR divider */
  orRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: Spacing.lg,
    gap: Spacing.sm,
  },
  orLine: { flex: 1, height: 1, backgroundColor: BORDER_CLR },
  orText: {
    fontSize: FontSize.xs,
    fontWeight: '700',
    color: '#9CA3AF',
    letterSpacing: 1.5,
  },

  /* Biometric */
  biometricBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    height: 56,
    borderWidth: 1.5,
    borderColor: '#1F2937',
    borderRadius: Radius.md,
    backgroundColor: Colors.white,
  },
  biometricBtnText: {
    color: '#1F2937',
    fontSize: FontSize.base,
    fontWeight: '600',
    letterSpacing: 0.3,
  },

  /* Forgot */
  forgotRow: { marginTop: Spacing.base, alignItems: 'center' },
  forgotText: { fontSize: FontSize.sm, color: Colors.textSecondary, textAlign: 'center' },
  forgotLink: { color: SprintColors.green, fontWeight: '600' },

  /* Footer */
  footer: { alignItems: 'center', marginTop: Spacing['2xl'], gap: Spacing.sm },
  footerAccent: { width: 80, height: 3, borderRadius: 2 },
  footerText: {
    fontSize: FontSize.xs,
    color: Colors.grey400,
    textAlign: 'center',
    letterSpacing: 0.3,
  },
});
"""

# ─────────────────────────────────────────────────────────────────────────────
# 2. useBiometric.ts
# ─────────────────────────────────────────────────────────────────────────────
BIOMETRIC_HOOK = path( "mobile", "hooks", "useBiometric.ts")

BIOMETRIC_HOOK_CONTENT = r"""/**
 * ParkiPay — useBiometric Hook
 *
 * Wraps expo-local-authentication for fingerprint / face login.
 *
 * Flow:
 *   ENROLMENT  — after password login, call registerBiometric(employeeId)
 *                → generates a random token → stores in SecureStore
 *                → sends token + employeeId to POST /api/auth/biometric/register/
 *
 *   LOGIN      — call loginWithBiometric()
 *                → reads token from SecureStore
 *                → triggers device biometric prompt
 *                → if passes, sends token to POST /api/auth/biometric/login/
 *                → backend returns JWT pair same as password login
 */
import { useState, useEffect, useCallback } from 'react';
import * as LocalAuth from 'expo-local-authentication';
import * as SecureStore from 'expo-secure-store';
import * as Crypto from 'expo-crypto';
import { useAuthStore, OfficerProfile } from '@/store/authStore';
import { biometricService } from '@/services/api';
import { AuthError } from './useAuth';

const SECURE_KEY = 'parkipay_biometric_token';

interface BiometricLoginResult {
  success: boolean;
  error?: AuthError;
}

export function useBiometric() {
  const { setAuth } = useAuthStore();
  const [isAvailable, setIsAvailable]           = useState(false);
  const [hasSavedCredential, setHasSavedCred]   = useState(false);
  const [isLoading, setIsLoading]               = useState(false);

  /* check device capability + existing enrolment on mount */
  useEffect(() => {
    (async () => {
      const compatible = await LocalAuth.hasHardwareAsync();
      const enrolled   = await LocalAuth.isEnrolledAsync();
      setIsAvailable(compatible && enrolled);

      const stored = await SecureStore.getItemAsync(SECURE_KEY).catch(() => null);
      setHasSavedCred(!!stored);
    })();
  }, []);

  /**
   * Register biometrics after a successful password login.
   * Generates a random token, persists it locally and remotely.
   */
  const registerBiometric = useCallback(async (employeeId: string): Promise<boolean> => {
    try {
      setIsLoading(true);

      /* 1. Confirm with the device sensor before storing */
      const auth = await LocalAuth.authenticateAsync({
        promptMessage: 'Confirm your identity to enable biometric login',
        fallbackLabel: 'Use passcode',
        cancelLabel: 'Cancel',
      });
      if (!auth.success) return false;

      /* 2. Generate a secure random token (32 hex bytes) */
      const random = await Crypto.getRandomBytesAsync(32);
      const token  = Array.from(random).map(b => b.toString(16).padStart(2, '0')).join('');

      /* 3. Save token locally (hardware-backed keystore) */
      await SecureStore.setItemAsync(SECURE_KEY, token);

      /* 4. Register token with backend (maps token → officer) */
      await biometricService.register(employeeId, token);

      setHasSavedCred(true);
      return true;
    } catch {
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Login with biometric.
   * Reads stored token, prompts device auth, exchanges token for JWTs.
   */
  const loginWithBiometric = useCallback(async (): Promise<BiometricLoginResult> => {
    try {
      setIsLoading(true);

      /* 1. Retrieve the stored token */
      const token = await SecureStore.getItemAsync(SECURE_KEY).catch(() => null);
      if (!token) {
        return {
          success: false,
          error: { code: 'no_credential', message: 'No biometric credential found. Please log in with your password first.' },
        };
      }

      /* 2. Trigger device sensor */
      const auth = await LocalAuth.authenticateAsync({
        promptMessage: 'Sign in to ParkiPay',
        fallbackLabel: 'Use password',
        cancelLabel: 'Cancel',
        disableDeviceFallback: false,
      });
      if (!auth.success) {
        return {
          success: false,
          error: { code: 'biometric_failed', message: auth.error ?? 'Biometric authentication cancelled.' },
        };
      }

      /* 3. Exchange token for JWTs */
      const { data } = await biometricService.loginWithToken(token);
      await setAuth(data.access, data.refresh, data.officer as OfficerProfile);
      return { success: true };

    } catch (err: unknown) {
      const apiErr = err as { response?: { data?: { error?: string; detail?: string } } };
      const d = apiErr?.response?.data;
      return {
        success: false,
        error: {
          code: d?.error ?? 'network_error',
          message: d?.detail ?? 'Biometric login failed. Please try your password.',
        },
      };
    } finally {
      setIsLoading(false);
    }
  }, [setAuth]);

  /** Remove saved credential (e.g. on logout) */
  const clearBiometric = useCallback(async () => {
    await SecureStore.deleteItemAsync(SECURE_KEY).catch(() => {});
    setHasSavedCred(false);
  }, []);

  return {
    isAvailable,
    hasSavedCredential,
    isLoading,
    registerBiometric,
    loginWithBiometric,
    clearBiometric,
  };
}
"""

# ─────────────────────────────────────────────────────────────────────────────
# 3. services/api.ts — append biometricService
# ─────────────────────────────────────────────────────────────────────────────
API_SERVICE = path( "mobile", "services", "api.ts")

BIOMETRIC_SERVICE_SNIPPET = """
// ── Biometric Auth Service ────────────────────────────────────────────────────

export const biometricService = {
  /**
   * Register a biometric token for an officer after normal login.
   * The token is a device-generated random string; actual biometric data
   * never leaves the device — the OS validates it locally.
   */
  register: (employee_id: string, token: string) =>
    apiClient.post('/api/auth/biometric/register/', { employee_id, token }),

  /**
   * Exchange a biometric token for a JWT pair.
   * Only called after the OS has confirmed the user's fingerprint/face.
   */
  loginWithToken: (token: string) =>
    apiClient.post('/api/auth/biometric/login/', { token }),

  /** Revoke a biometric token (called on logout or when user disables biometrics). */
  revoke: (token: string) =>
    apiClient.post('/api/auth/biometric/revoke/', { token }),
};
"""

# ─────────────────────────────────────────────────────────────────────────────
# 4. package.json — add expo-local-authentication + expo-crypto
# ─────────────────────────────────────────────────────────────────────────────
PACKAGE_JSON = path( "mobile", "package.json")

def add_deps(pkg):
    pkg.setdefault("dependencies", {})
    pkg["dependencies"]["expo-local-authentication"] = "~16.0.4"
    pkg["dependencies"]["expo-crypto"]               = "~14.0.4"

# ─────────────────────────────────────────────────────────────────────────────
# 5. backend/src/routes/auth.js — append biometric routes
# ─────────────────────────────────────────────────────────────────────────────
BACKEND_AUTH = path( "backend", "src", "routes", "auth.js")

BIOMETRIC_ROUTES = """
// ── POST /api/auth/biometric/register/ ───────────────────────────────────────
// Stores a device-generated token linked to an officer.
// Called after a successful password login + device biometric confirmation.

const BiometricRegisterSchema = z.object({
  employee_id: z.string().min(1),
  token:       z.string().min(32).max(128),
});

router.post('/biometric/register/', authenticate, async (req, res, next) => {
  try {
    const parsed = BiometricRegisterSchema.safeParse(req.body);
    if (!parsed.success) {
      return res.status(400).json({ error: 'validation_error', detail: parsed.error.flatten() });
    }
    const { employee_id: employeeId, token } = parsed.data;

    // Verify the authenticated officer owns this employeeId
    if (req.officer.employeeId !== employeeId) {
      return res.status(403).json({
        error:  'forbidden',
        detail: 'You may only register biometrics for your own account.',
      });
    }

    // Upsert: one active token per officer (replace if re-enrolling)
    await prisma.$executeRaw`
      INSERT INTO officer_biometrics (officer_id, token, device_hint, is_active, created_at, updated_at)
      VALUES (
        ${req.officer.id},
        ${token},
        ${'device'},
        true,
        NOW(),
        NOW()
      )
      ON CONFLICT (officer_id)
      DO UPDATE SET
        token      = EXCLUDED.token,
        is_active  = true,
        updated_at = NOW()
    `;

    await logAction(req.officer, 'BIOMETRIC_REGISTER', { result: 'success', req });
    return res.json({ detail: 'Biometric credential registered successfully.' });
  } catch (err) {
    next(err);
  }
});

// ── POST /api/auth/biometric/login/ ──────────────────────────────────────────
// Exchanges a verified biometric token for a JWT pair.
// The device has already confirmed the fingerprint/face before this call.

const BiometricLoginSchema = z.object({
  token: z.string().min(32).max(128),
});

router.post('/biometric/login/', async (req, res, next) => {
  try {
    const parsed = BiometricLoginSchema.safeParse(req.body);
    if (!parsed.success) {
      return res.status(400).json({ error: 'validation_error', detail: parsed.error.flatten() });
    }
    const { token } = parsed.data;

    // Look up the token
    const rows = await prisma.$queryRaw`
      SELECT ob.officer_id, ob.is_active
      FROM   officer_biometrics ob
      WHERE  ob.token = ${token}
      LIMIT  1
    `;

    if (!rows.length || !rows[0].is_active) {
      return res.status(401).json({
        error:  'invalid_biometric_token',
        detail: 'Biometric credential not found or disabled. Please log in with your password.',
      });
    }

    const officer = await prisma.officer.findUnique({
      where:   { id: rows[0].officer_id },
      include: { location: true },
    });

    if (!officer || !officer.isActive) {
      return res.status(401).json({
        error:  'account_inactive',
        detail: 'Your account is inactive. Contact your supervisor.',
      });
    }

    // Issue JWT pair exactly like password login
    const access              = jwtLib.signAccess(officer);
    const { token: refresh }  = jwtLib.signRefresh(officer);

    await prisma.officer.update({
      where: { id: officer.id },
      data:  { lastLogin: new Date() },
    });
    await logAction(officer, 'BIOMETRIC_LOGIN', { result: 'success', req });

    return res.json({ access, refresh, officer: officerProfile(officer) });
  } catch (err) {
    next(err);
  }
});

// ── POST /api/auth/biometric/revoke/ ─────────────────────────────────────────

router.post('/biometric/revoke/', authenticate, async (req, res, next) => {
  try {
    const { token } = req.body;
    if (!token) {
      return res.status(400).json({ error: 'token_required', detail: 'token is required.' });
    }
    await prisma.$executeRaw`
      UPDATE officer_biometrics
      SET    is_active = false, updated_at = NOW()
      WHERE  officer_id = ${req.officer.id}
        AND  token      = ${token}
    `;
    await logAction(req.officer, 'BIOMETRIC_REVOKE', { result: 'success', req });
    return res.json({ detail: 'Biometric credential revoked.' });
  } catch (err) {
    next(err);
  }
});
"""

# ─────────────────────────────────────────────────────────────────────────────
# 6. backend/prisma/schema.prisma — add OfficerBiometric model
# ─────────────────────────────────────────────────────────────────────────────
SCHEMA_PRISMA = path( "backend", "prisma", "schema.prisma")

PRISMA_MODEL = """
// ── OfficerBiometric ──────────────────────────────────────────────────────────
// One row per officer. Stores the device-generated random token that is
// exchanged for a JWT after local biometric verification passes on-device.
// Real biometric templates never leave the device.

model OfficerBiometric {
  id          Int      @id @default(autoincrement())
  officerId   Int      @unique  @map("officer_id")
  officer     Officer  @relation(fields: [officerId], references: [id], onDelete: Cascade)
  token       String   @unique  // 64-char hex random
  deviceHint  String   @default("device") @map("device_hint")
  isActive    Boolean  @default(true)     @map("is_active")
  createdAt   DateTime @default(now())    @map("created_at")
  updatedAt   DateTime @updatedAt         @map("updated_at")

  @@map("officer_biometrics")
}
"""

OFFICER_RELATION = '  auditLogs AuditLog[]'  # insert biometric relation just before this

# ─────────────────────────────────────────────────────────────────────────────
# 7. SQL migration
# ─────────────────────────────────────────────────────────────────────────────
MIGRATION_DIR = path( "backend", "prisma", "migrations", "biometric")
MIGRATION_SQL = os.path.join(MIGRATION_DIR, "migration.sql")

MIGRATION_SQL_CONTENT = """-- ParkiPay biometric migration
-- Safe to run multiple times (CREATE TABLE IF NOT EXISTS + INSERT ... ON CONFLICT DO NOTHING)

CREATE TABLE IF NOT EXISTS officer_biometrics (
  id           SERIAL       PRIMARY KEY,
  officer_id   INTEGER      NOT NULL UNIQUE REFERENCES officers(id) ON DELETE CASCADE,
  token        VARCHAR(128) NOT NULL UNIQUE,
  device_hint  VARCHAR(64)  NOT NULL DEFAULT 'device',
  is_active    BOOLEAN      NOT NULL DEFAULT TRUE,
  created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_officer_biometrics_token
  ON officer_biometrics(token) WHERE is_active = TRUE;

-- ── Seed: insert a test biometric row for the first officer (idempotent) ──────
-- The token below is a placeholder; the real flow generates it on the device.
-- Remove this block (or replace token) before deploying to production.
INSERT INTO officer_biometrics (officer_id, token, device_hint, is_active)
SELECT
  o.id,
  'seed_token_replace_me_64chars_aabbccddeeff00112233445566778899aabb',
  'seed_device',
  FALSE          -- disabled by default so it cannot be used until device enrols
FROM officers o
ORDER BY o.id
LIMIT 1
ON CONFLICT (officer_id) DO NOTHING;
"""

# ─────────────────────────────────────────────────────────────────────────────
# 8. Seed script
# ─────────────────────────────────────────────────────────────────────────────
SEED_JS = os.path.join(MIGRATION_DIR, "seed_biometrics.js")

SEED_JS_CONTENT = """/**
 * seed_biometrics.js
 * Seed the officer_biometrics table with test rows for local development.
 * Run from backend/:   node prisma/migrations/biometric/seed_biometrics.js
 */
const { PrismaClient } = require('@prisma/client');
const crypto           = require('crypto');

const prisma = new PrismaClient();

async function main() {
  const officers = await prisma.officer.findMany({ where: { isActive: true } });
  console.log(`Seeding biometrics for ${officers.length} officer(s)…`);

  for (const officer of officers) {
    // Generate a random token (same length as the device would)
    const token = crypto.randomBytes(32).toString('hex');

    await prisma.$executeRaw`
      INSERT INTO officer_biometrics (officer_id, token, device_hint, is_active, created_at, updated_at)
      VALUES (
        ${officer.id},
        ${token},
        ${'seed_device'},
        false,
        NOW(),
        NOW()
      )
      ON CONFLICT (officer_id) DO NOTHING
    `;
    console.log(`  officer ${officer.employeeId} → token seeded (is_active=false)`);
  }
  console.log('Done. Tokens are inactive until the officer enrols from the app.');
}

main().catch(console.error).finally(() => prisma.$disconnect());
"""

# ─────────────────────────────────────────────────────────────────────────────
# Apply all patches
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("\n── PayPark biometric patch ─────────────────────────────────────────\n")

    # 1. login.tsx
    print("[1] login.tsx — Sign In heading + Ionicons + biometric button")
    backup(LOGIN_TSX)
    write(LOGIN_TSX, LOGIN_CONTENT)

    # 2. useBiometric.ts (new)
    print("[2] useBiometric.ts — new biometric hook")
    write(BIOMETRIC_HOOK, BIOMETRIC_HOOK_CONTENT)

    # 2b. Update hooks/index.ts to export useBiometric
    hooks_index = path("PayPark-main", "mobile", "hooks", "index.ts")
    if os.path.exists(hooks_index):
        existing = read(hooks_index)
        if "useBiometric" not in existing:
            write(hooks_index, existing.rstrip() + "\nexport { useBiometric } from './useBiometric';\n")
            print("  [✓] hooks/index.ts updated")

    # 3. services/api.ts — append biometricService
    print("[3] services/api.ts — append biometricService")
    backup(API_SERVICE)
    api_content = read(API_SERVICE)
    if "biometricService" not in api_content:
        write(API_SERVICE, api_content.rstrip() + "\n" + BIOMETRIC_SERVICE_SNIPPET)
    else:
        print("  [–] biometricService already present, skipped")

    # 4. package.json
    print("[4] package.json — add expo-local-authentication + expo-crypto")
    backup(PACKAGE_JSON)
    patch_json(PACKAGE_JSON, add_deps)

    # 5. backend auth routes
    print("[5] backend/src/routes/auth.js — biometric routes")
    backup(BACKEND_AUTH)
    auth_content = read(BACKEND_AUTH)
    if "biometric/register" not in auth_content:
        # Insert before module.exports
        auth_content = auth_content.replace(
            "module.exports = router;",
            BIOMETRIC_ROUTES + "\nmodule.exports = router;"
        )
        write(BACKEND_AUTH, auth_content)
    else:
        print("  [–] biometric routes already present, skipped")

    # 6. prisma schema
    print("[6] prisma/schema.prisma — OfficerBiometric model")
    backup(SCHEMA_PRISMA)
    schema = read(SCHEMA_PRISMA)
    if "OfficerBiometric" not in schema:
        # Add biometric relation to Officer model before auditLogs
        schema = schema.replace(
            OFFICER_RELATION,
            "  biometric   OfficerBiometric?\n  " + OFFICER_RELATION.lstrip()
        )
        schema += "\n" + PRISMA_MODEL
        write(SCHEMA_PRISMA, schema)
    else:
        print("  [–] OfficerBiometric already in schema, skipped")

    # 7. SQL migration
    print("[7] migrations/biometric/migration.sql — CREATE TABLE IF NOT EXISTS + seed")
    write(MIGRATION_SQL, MIGRATION_SQL_CONTENT)

    # 8. Seed script
    print("[8] migrations/biometric/seed_biometrics.js — seed script")
    write(SEED_JS, SEED_JS_CONTENT)

    print("""
── All patches applied ─────────────────────────────────────────────────────

 MOBILE — next steps:
   cd PayPark-main/mobile
   npx expo install expo-local-authentication expo-crypto
   # (or just: npm install — package.json already updated)
   # For Android: ensure android/app/src/main/AndroidManifest.xml has:
   #   <uses-permission android:name="android.permission.USE_BIOMETRIC"/>
   #   <uses-permission android:name="android.permission.USE_FINGERPRINT"/>
   # For iOS: Info.plist needs:
   #   NSFaceIDUsageDescription → "Used to sign in to ParkiPay"

 BACKEND — next steps:
   cd PayPark-main/backend
   npx prisma migrate dev --name add_officer_biometrics
   # (or apply the raw SQL manually)
   node prisma/migrations/biometric/seed_biometrics.js

 RESTORE ORIGINALS (if needed):
   cp mobile/app/(auth)/login.tsx.bak    mobile/app/(auth)/login.tsx
   cp mobile/services/api.ts.bak         mobile/services/api.ts
   cp backend/src/routes/auth.js.bak     backend/src/routes/auth.js
   cp backend/prisma/schema.prisma.bak   backend/prisma/schema.prisma
""")

if __name__ == "__main__":
    main()

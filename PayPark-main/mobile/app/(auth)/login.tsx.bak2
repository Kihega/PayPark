/**
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

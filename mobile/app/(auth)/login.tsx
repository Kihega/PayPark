/**
 * ParkiPay — Login Screen
 * Officer login: employee_id + password.
 * TATURA palette, bilingual UI (Swahili / English), lockout feedback.
 * All auth logic lives in useAuth(); all field styling in shared Input.
 */
import { useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { router } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';

import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui';
import {
  Colors,
  SprintColors,
  FontSize,
  FontWeight,
  Spacing,
  Radius,
  Shadows,
  LetterSpacing,
} from '@/constants/theme';

export default function LoginScreen() {
  const { login, isLoading, error, clearError } = useAuth();

  const [employeeId, setEmployeeId] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  // Derive bilingual error message from structured hook error
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
        : `Hitilafu ya muunganisho. Jaribu tena.\n(Connection error. Please try again.)`
      : null
  );

  const handleFieldChange = () => { setLocalError(null); clearError(); };

  const handleLogin = async () => {
    setLocalError(null);
    clearError();

    if (!employeeId.trim()) {
      setLocalError('Tafadhali ingiza nambari yako ya utumishi.\n(Please enter your employee ID.)');
      return;
    }
    if (!password) {
      setLocalError('Tafadhali ingiza nenosiri lako.\n(Please enter your password.)');
      return;
    }

    const result = await login(employeeId, password);
    if (result.success) {
      router.replace('/(app)/home');
    }
  };

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
        {/* ── Branding Header ───────────────────────────────────────── */}
        <View style={styles.headerBlock}>
          <LinearGradient
            colors={[SprintColors.green, SprintColors.yellow]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={styles.headerAccent}
          />
          <View style={styles.wordmarkRow}>
            <Text style={[styles.wordmarkText, { color: SprintColors.green }]}>Parki</Text>
            <Text style={[styles.wordmarkText, { color: SprintColors.yellow }]}>Pay</Text>
          </View>
          <Text style={styles.subtitle}>Mfumo wa Maegesho wa Serikali</Text>
          <Text style={styles.subtitleEn}>Government Parking Management System</Text>
        </View>

        {/* ── Login Card ────────────────────────────────────────────── */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Ingia / Sign In</Text>
          <Text style={styles.cardSubtitle}>
            Tumia nambari yako ya utumishi{'\n'}Use your government employee ID
          </Text>

          {/* Employee ID Field */}
          <View style={styles.fieldGroup}>
            <Text style={styles.label}>Nambari ya Utumishi / Employee ID</Text>
            <TextInput
              style={[styles.input, errorMessage ? styles.inputError : null]}
              value={employeeId}
              onChangeText={(t) => { handleFieldChange(); setEmployeeId(t); }}
              placeholder="e.g. TZ-2024-001"
              placeholderTextColor={Colors.grey400}
              autoCapitalize="characters"
              autoCorrect={false}
              returnKeyType="next"
              editable={!isLoading}
            />
          </View>

          {/* Password Field */}
          <View style={styles.fieldGroup}>
            <Text style={styles.label}>Nenosiri / Password</Text>
            <View style={styles.passwordWrapper}>
              <TextInput
                style={[styles.input, styles.passwordInput, errorMessage ? styles.inputError : null]}
                value={password}
                onChangeText={(t) => { handleFieldChange(); setPassword(t); }}
                placeholder="••••••••"
                placeholderTextColor={Colors.grey400}
                secureTextEntry={!showPassword}
                autoCorrect={false}
                returnKeyType="done"
                onSubmitEditing={handleLogin}
                editable={!isLoading}
              />
              <TouchableOpacity
                style={styles.eyeBtn}
                onPress={() => setShowPassword((v) => !v)}
                hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
              >
                <Text style={styles.eyeIcon}>{showPassword ? '🙈' : '👁️'}</Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Error Banner */}
          {errorMessage ? (
            <View style={styles.errorBox}>
              <Text style={styles.errorText}>{errorMessage}</Text>
            </View>
          ) : null}

          {/* Submit */}
          <Button
            label="Ingia / Login"
            variant="primary"
            size="lg"
            fullWidth
            loading={isLoading}
            onPress={handleLogin}
            style={{ marginTop: Spacing.sm }}
          />

          {/* Forgot password (Phase 2) */}
          <Pressable style={styles.forgotRow}>
            <Text style={styles.forgotText}>
              Umesahau nenosiri?{' '}
              <Text style={styles.forgotLink}>Wasiliana na Msimamizi</Text>
            </Text>
          </Pressable>
        </View>

        {/* ── Footer ───────────────────────────────────────────────── */}
        <View style={styles.footer}>
          <LinearGradient
            colors={[SprintColors.yellow, SprintColors.black]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
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

  // Header
  headerBlock: { alignItems: 'center', paddingTop: Spacing['4xl'], paddingBottom: Spacing.xl },
  headerAccent: { width: 180, height: 4, borderRadius: 2, marginBottom: Spacing.lg },
  wordmarkRow: { flexDirection: 'row', alignItems: 'baseline', marginBottom: Spacing.sm },
  wordmarkText: {
    fontSize: FontSize['3xl'],
    fontWeight: FontWeight.black,
    letterSpacing: LetterSpacing.display,
    shadowColor: SprintColors.green,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.5,
    shadowRadius: 10,
  },
  subtitle: {
    fontSize: FontSize.sm,
    fontWeight: FontWeight.medium,
    color: Colors.grey700,
    textAlign: 'center',
  },
  subtitleEn: { fontSize: FontSize.sm, color: Colors.grey500, textAlign: 'center', marginTop: 2 },

  // Card
  card: { backgroundColor: Colors.white, borderRadius: Radius.lg, padding: Spacing.xl, ...Shadows.md },
  cardTitle: { fontSize: FontSize.xl, fontWeight: FontWeight.bold, color: Colors.textPrimary, marginBottom: Spacing.xs },
  cardSubtitle: { fontSize: FontSize.sm, color: Colors.textSecondary, lineHeight: 20, marginBottom: Spacing.xl },

  // Fields
  fieldGroup: { marginBottom: Spacing.md },
  label: { fontSize: FontSize.sm, fontWeight: FontWeight.semiBold, color: Colors.textSecondary, marginBottom: Spacing.xs },
  input: {
    height: 52,
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: Radius.md,
    paddingHorizontal: Spacing.base,
    fontSize: FontSize.base,
    color: Colors.textPrimary,
    backgroundColor: Colors.white,
  },
  inputError: { borderColor: Colors.error },
  passwordWrapper: { position: 'relative' },
  passwordInput: { paddingRight: 52 },
  eyeBtn: { position: 'absolute', right: 14, top: 0, bottom: 0, justifyContent: 'center' },
  eyeIcon: { fontSize: 20 },

  // Error
  errorBox: {
    backgroundColor: Colors.errorSurface,
    borderRadius: Radius.md,
    padding: Spacing.md,
    marginBottom: Spacing.base,
    borderLeftWidth: 3,
    borderLeftColor: Colors.error,
  },
  errorText: { fontSize: FontSize.sm, color: Colors.error, lineHeight: 18 },

  // Forgot
  forgotRow: { marginTop: Spacing.base, alignItems: 'center' },
  forgotText: { fontSize: FontSize.sm, color: Colors.textSecondary, textAlign: 'center' },
  forgotLink: { color: SprintColors.green, fontWeight: FontWeight.semiBold },

  // Footer
  footer: { alignItems: 'center', marginTop: Spacing['2xl'], gap: Spacing.sm },
  footerAccent: { width: 80, height: 3, borderRadius: 2 },
  footerText: { fontSize: FontSize.xs, color: Colors.grey400, textAlign: 'center', letterSpacing: 0.3 },
});

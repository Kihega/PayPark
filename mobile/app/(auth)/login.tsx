/**
 * ParkiPay — Login  (patch2: auto-dash, no footer, format guard)
 *
 * ID formats:
 *   Attendant   → TZ-XXXX   (TZ + dash auto-inserted + 4 digits)
 *   Supervisor  → SUP-XXXX  (SUP + dash auto-inserted + 4 digits)
 *
 * The dash is inserted automatically when the user finishes typing
 * the prefix (TZ or SUP), so they only need to type numbers after.
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
import { Colors, SprintColors, Shadows } from '@/constants/theme';

// Accepted final formats
const ATTENDANT_RE  = /^TZ-\d{4}$/;
const SUPERVISOR_RE = /^SUP-\d{4}$/;

function isValidIdFormat(id: string): boolean {
  return ATTENDANT_RE.test(id) || SUPERVISOR_RE.test(id);
}

/**
 * Smart formatter: keeps only A-Z 0-9 and one dash,
 * auto-inserts the dash after the prefix (TZ or SUP).
 */
function smartFormat(raw: string): string {
  // Strip everything except letters, digits, dash; force uppercase
  const clean = raw.toUpperCase().replace(/[^A-Z0-9-]/g, '');

  // Never allow more than one dash
  const parts = clean.split('-');
  const prefix = parts[0];
  const digits = parts.slice(1).join('').replace(/[^0-9]/g, '');

  // Auto-insert dash once prefix matches TZ or SUP
  if ((prefix === 'TZ' || prefix === 'SUP') && parts.length === 1) {
    // User just finished typing the prefix with no dash yet — add it
    return prefix + '-';
  }

  if (parts.length >= 2) {
    // Has a dash — reconstruct cleanly: PREFIX-DIGITS (max 4 digits)
    return prefix + '-' + digits.slice(0, 4);
  }

  // Still typing prefix (< 3 chars), just return cleaned prefix
  return prefix.slice(0, 3);
}

export default function LoginScreen() {
  const { loginById, isLoading, error, clearError } = useAuth();
  const { language } = useSettingsStore();
  const tr = (k: string) => t(language, k);

  const [employeeId, setEmployeeId] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);

  const errMsg = localError ?? error?.message ?? null;

  const handleChangeText = (raw: string) => {
    setLocalError(null);
    clearError();
    setEmployeeId(smartFormat(raw));
  };

  const handleLogin = async () => {
    setLocalError(null);
    clearError();

    const id = employeeId.trim();

    if (!id) {
      setLocalError(tr('enterIdError'));
      return;
    }

    if (!isValidIdFormat(id)) {
      setLocalError(
        'Invalid ID format. Use TZ-XXXX for attendants or SUP-XXXX for supervisors.'
      );
      return;
    }

    const result = await loginById(id);
    if (!result.success) return;

    if (result.role === 'SUPERVISOR') {
      router.replace('/(app)/admin');
    } else {
      router.replace('/(app)/home');
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.root}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">

        {/* Branding */}
        <View style={styles.header}>
          <LinearGradient
            colors={[SprintColors.green, SprintColors.yellow]}
            start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
            style={styles.accent}
          />
          <View style={{ flexDirection: 'row' }}>
            <Text style={[styles.logo, { color: SprintColors.green }]}>Parki</Text>
            <Text style={[styles.logo, { color: SprintColors.yellow }]}>Pay</Text>
          </View>
          <Text style={styles.sub1}>{tr('taglineSw')}</Text>
          <Text style={styles.sub2}>{tr('taglineEn')}</Text>
        </View>

        {/* Card */}
        <View style={styles.card}>
          <Text style={styles.title}>{tr('signIn')}</Text>
          <Text style={styles.subtitle}>{tr('signInSub')}</Text>

          <Text style={styles.label}>{tr('officerId')}</Text>
          <View style={[styles.inputRow, errMsg ? styles.inputErr : null]}>
            <Ionicons
              name="id-card-outline" size={18}
              color={errMsg ? Colors.error : '#6B7280'}
              style={{ marginLeft: 12 }}
            />
            <TextInput
              style={styles.input}
              value={employeeId}
              onChangeText={handleChangeText}
              placeholder="TZ-XXXX  or  SUP-XXXX"
              placeholderTextColor="#9CA3AF"
              autoCapitalize="characters"
              autoCorrect={false}
              returnKeyType="done"
              onSubmitEditing={handleLogin}
              editable={!isLoading}
            />
          </View>

          {/* Format hint */}
          <Text style={styles.formatHint}>
            Attendants: TZ-XXXX · Supervisors: SUP-XXXX
          </Text>

          {/* Error */}
          {errMsg ? (
            <View style={styles.errBox}>
              <Ionicons name="alert-circle-outline" size={15} color={Colors.error} />
              <Text style={styles.errText}>{errMsg}</Text>
            </View>
          ) : null}

          <TouchableOpacity
            style={[styles.btn, isLoading && { opacity: 0.6 }]}
            onPress={handleLogin}
            disabled={isLoading}
            activeOpacity={0.85}
          >
            {isLoading
              ? <ActivityIndicator color="#fff" />
              : <>
                  <Ionicons name="log-in-outline" size={20} color="#fff" />
                  <Text style={styles.btnText}>{tr('signInBtn')}</Text>
                </>
            }
          </TouchableOpacity>
        </View>

        {/* Footer intentionally removed */}

      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  root:       { flex: 1, backgroundColor: Colors.backgroundSecondary },
  scroll:     { flexGrow: 1, paddingHorizontal: 20, paddingBottom: 40, justifyContent: 'center' },
  header:     { alignItems: 'center', paddingTop: 60, paddingBottom: 28 },
  accent:     { width: 180, height: 4, borderRadius: 2, marginBottom: 16 },
  logo:       { fontSize: 36, fontWeight: '900', letterSpacing: 1 },
  sub1:       { fontSize: 13, color: '#404040', marginTop: 4 },
  sub2:       { fontSize: 13, color: '#737373' },
  card:       { backgroundColor: '#fff', borderRadius: 16, padding: 24, ...Shadows.md },
  title:      { fontSize: 28, fontWeight: '800', textAlign: 'center', color: '#1A1A1A', marginBottom: 4 },
  subtitle:   { fontSize: 13, color: '#595959', textAlign: 'center', marginBottom: 24, lineHeight: 20 },
  label:      { fontSize: 13, fontWeight: '700', color: '#1A1A1A', marginBottom: 6 },
  inputRow:   {
    flexDirection: 'row', alignItems: 'center', height: 54,
    borderWidth: 1.5, borderColor: '#D1D5DB', borderRadius: 12, backgroundColor: '#fff',
  },
  inputErr:   { borderColor: Colors.error },
  input:      { flex: 1, fontSize: 15, color: '#1A1A1A', paddingHorizontal: 10 },
  formatHint: { fontSize: 11, color: '#9CA3AF', marginTop: 5, marginBottom: 2 },
  errBox:     {
    flexDirection: 'row', alignItems: 'flex-start', gap: 6,
    backgroundColor: Colors.errorSurface, borderRadius: 10, padding: 10,
    marginTop: 8, borderLeftWidth: 3, borderLeftColor: Colors.error,
  },
  errText:    { fontSize: 13, color: Colors.error, flex: 1, lineHeight: 18 },
  btn:        {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10,
    height: 56, backgroundColor: '#0D1117', borderRadius: 12, marginTop: 20,
  },
  btnText:    { color: '#fff', fontSize: 15, fontWeight: '700', letterSpacing: 0.4 },
});

"""
patch_fix_login.py
==================
Fixes the "Employee ID not found" error on Render.

Root causes fixed:
  1. package.json  — adds postinstall/build so `prisma generate` runs on Render deploy
  2. schema.prisma — removes directUrl (only needed locally for migrations, crashes
                     Render if DIRECT_URL env var is missing)
  3. hooks/useAuth.ts — passes actual backend error detail through (not just code)
  4. login.tsx       — shows real backend error message for easier debugging
  5. Adds GET /api/health/ endpoint so you can verify the server is alive + DB connected

Run from project root:  python patch_fix_login.py
"""

import os, json

ROOT = os.path.dirname(os.path.abspath(__file__))
def p(*parts): return os.path.join(ROOT, *parts)
def read(f):
    with open(f, encoding="utf-8") as fh: return fh.read()
def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh: fh.write(content)
    print(f"  [✓] {path}")
def bak(path):
    b = path + ".bak3"
    if os.path.exists(path) and not os.path.exists(b):
        write(b, read(path))

# ── 1. package.json — add postinstall + build ─────────────────────────────────
PKG = p("backend","package.json")

def fix_pkg():
    bak(PKG)
    data = json.loads(read(PKG))
    data["scripts"]["postinstall"] = "prisma generate"
    data["scripts"]["build"]       = "prisma generate"
    write(PKG, json.dumps(data, indent=2) + "\n")

# ── 2. schema.prisma — remove directUrl (Render doesn't have DIRECT_URL) ──────
SCHEMA = p("backend","prisma","schema.prisma")

def fix_schema():
    bak(SCHEMA)
    content = read(SCHEMA)
    # Remove the directUrl line — only needed locally for `prisma migrate`
    fixed = "\n".join(
        line for line in content.splitlines()
        if "directUrl" not in line
    )
    write(SCHEMA, fixed)

# ── 3. hooks/useAuth.ts — surface real error message ─────────────────────────
USE_AUTH = p("mobile","hooks","useAuth.ts")

USE_AUTH_CONTENT = r'''/**
 * ParkiPay — useAuth Hook  (v3: ID-only login, real error messages)
 */
import { useState, useCallback } from 'react';
import { authService } from '@/services/api';
import { useAuthStore, OfficerProfile } from '@/store/authStore';

export interface AuthError {
  code: string;
  message: string;
}

interface LoginResult {
  success: boolean;
  role?: string;
  error?: AuthError;
}

export function useAuth() {
  const { setAuth, clearAuth, refreshToken, officer, isAuthenticated } = useAuthStore();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError]         = useState<AuthError | null>(null);

  const loginById = useCallback(async (employeeId: string): Promise<LoginResult> => {
    setIsLoading(true);
    setError(null);
    try {
      const { data } = await authService.loginById(employeeId.trim());
      await setAuth(data.access, data.refresh, data.officer as OfficerProfile);
      return { success: true, role: data.officer.role };
    } catch (err: unknown) {
      const resp = (err as any)?.response;
      const d    = resp?.data;

      // Surface the real backend message so we know exactly what went wrong
      const authError: AuthError = {
        code:    d?.error   ?? 'network_error',
        message: d?.detail  ?? (resp ? `Server error ${resp.status}` : 'No response from server. Check your connection.'),
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
    } catch { /* clear local regardless */ } finally {
      await clearAuth();
      setIsLoading(false);
    }
  }, [refreshToken, clearAuth]);

  return {
    officer, isAuthenticated, isLoading, error,
    clearError: () => setError(null),
    loginById, logout,
  };
}
'''

# ── 4. login.tsx — show real error message ────────────────────────────────────
LOGIN = p("mobile","app","(auth)","login.tsx")

LOGIN_CONTENT = r'''/**
 * ParkiPay — Login  (v4: shows real backend error message)
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

  // Show local validation error OR actual backend error message
  const errMsg = localError ?? error?.message ?? null;

  const handleLogin = async () => {
    setLocalError(null); clearError();
    if (!employeeId.trim()) {
      setLocalError(tr('enterIdError'));
      return;
    }
    const result = await loginById(employeeId.trim());
    if (!result.success) return;   // error already set in useAuth

    if (result.role === 'SUPERVISOR' || result.role === 'ADMIN') {
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

          {/* Real error message from backend */}
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

        <View style={styles.footer}>
          <LinearGradient
            colors={[SprintColors.yellow, SprintColors.black]}
            start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
            style={styles.footerAccent}
          />
          <Text style={styles.footerText}>© 2026 Serikali ya Tanzania — ParkiPay v1.0</Text>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  root:        { flex: 1, backgroundColor: Colors.backgroundSecondary },
  scroll:      { flexGrow: 1, paddingHorizontal: 20, paddingBottom: 40 },
  header:      { alignItems: 'center', paddingTop: 60, paddingBottom: 28 },
  accent:      { width: 180, height: 4, borderRadius: 2, marginBottom: 16 },
  logo:        { fontSize: 36, fontWeight: '900', letterSpacing: 1 },
  sub1:        { fontSize: 13, color: '#404040', marginTop: 4 },
  sub2:        { fontSize: 13, color: '#737373' },
  card:        { backgroundColor: '#fff', borderRadius: 16, padding: 24, ...Shadows.md },
  title:       { fontSize: 28, fontWeight: '800', textAlign: 'center', color: '#1A1A1A', marginBottom: 4 },
  subtitle:    { fontSize: 13, color: '#595959', textAlign: 'center', marginBottom: 24, lineHeight: 20 },
  label:       { fontSize: 13, fontWeight: '700', color: '#1A1A1A', marginBottom: 6 },
  inputRow:    {
    flexDirection: 'row', alignItems: 'center', height: 54,
    borderWidth: 1.5, borderColor: '#D1D5DB', borderRadius: 12, backgroundColor: '#fff',
  },
  inputErr:    { borderColor: Colors.error },
  input:       { flex: 1, fontSize: 15, color: '#1A1A1A', paddingHorizontal: 10 },
  errBox:      {
    flexDirection: 'row', alignItems: 'flex-start', gap: 6,
    backgroundColor: Colors.errorSurface, borderRadius: 10, padding: 10,
    marginTop: 8, borderLeftWidth: 3, borderLeftColor: Colors.error,
  },
  errText:     { fontSize: 13, color: Colors.error, flex: 1, lineHeight: 18 },
  btn:         {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10,
    height: 56, backgroundColor: '#0D1117', borderRadius: 12, marginTop: 20,
  },
  btnText:     { color: '#fff', fontSize: 15, fontWeight: '700', letterSpacing: 0.4 },
  footer:      { alignItems: 'center', marginTop: 32, gap: 8 },
  footerAccent:{ width: 80, height: 3, borderRadius: 2 },
  footerText:  { fontSize: 11, color: '#8C8C8C' },
});
'''

# ── 5. backend health + diagnostic endpoint ───────────────────────────────────
APP_JS = p("backend","src","app.js")

def add_health_route():
    bak(APP_JS)
    content = read(APP_JS)
    health = """
// ── Health check (GET /api/health/) ─────────────────────────────────────────
// Verifies the server is running AND the DB connection works.
// curl https://your-render-url.onrender.com/api/health/
const prisma = require('./lib/prisma');
app.get('/api/health/', async (req, res) => {
  try {
    await prisma.$queryRaw`SELECT 1`;
    res.json({ status: 'ok', db: 'connected', ts: new Date().toISOString() });
  } catch (err) {
    res.status(503).json({ status: 'error', db: 'unreachable', detail: err.message });
  }
});

"""
    # Insert after the rate-limiter block, before the routes
    marker = "app.use('/api/auth/',"
    if "api/health" not in content:
        content = content.replace(marker, health + marker)
        write(APP_JS, content)
    else:
        print("  [–] health route already present")

# ═════════════════════════════════════════════════════════════════════════════
def main():
    print("\n── patch_fix_login.py ───────────────────────────────────────────────\n")

    print("[1] backend/package.json — add postinstall + build (prisma generate)")
    fix_pkg()

    print("[2] backend/prisma/schema.prisma — remove directUrl (causes crash on Render)")
    fix_schema()

    print("[3] mobile/hooks/useAuth.ts — surface real backend error message")
    bak(USE_AUTH); write(USE_AUTH, USE_AUTH_CONTENT)

    print("[4] mobile/app/(auth)/login.tsx — show actual error (not i18n fallback)")
    bak(LOGIN); write(LOGIN, LOGIN_CONTENT)

    print("[5] backend/src/app.js — add /api/health/ diagnostic endpoint")
    add_health_route()

    print("""
── Done ─────────────────────────────────────────────────────────────────────

 STEP 1 — Push backend to Render:
   cd PayPark-main/backend
   git add -A && git commit -m "fix: prisma generate on deploy, remove directUrl" && git push
   (Render will run `npm install` → postinstall → `prisma generate` automatically)

 STEP 2 — Verify the server & DB are healthy:
   curl https://paypark-backend.onrender.com/api/health/
   Expected: {"status":"ok","db":"connected","ts":"..."}

 STEP 3 — Test login:
   curl -X POST https://paypark-backend.onrender.com/api/auth/login/ \\
     -H "Content-Type: application/json" \\
     -d '{"employee_id":"TZ-8821"}'
   Expected: {"access":"...","refresh":"...","officer":{...}}

 STEP 4 — Restart Expo (picks up useAuth + login changes):
   cd PayPark-main/mobile && npx expo start --clear

 If health check fails with db:unreachable
   → Set DATABASE_URL in Render dashboard → Environment → Add env var
   → Use the POOLER url (port 6543) from Supabase Settings → Database
""")

if __name__ == "__main__":
    main()


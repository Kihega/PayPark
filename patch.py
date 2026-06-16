#!/usr/bin/env python3
"""
patch2.py — ParkiPay Mobile App — Second-Round Patch
=====================================================
Applies the following fixes on top of patch.py:

  Fix 1 → Clean up all *.bak_patch files left by the previous patch.

  Fix 2 → Supervisor test ID: SUP-001 → SUP-0001
             • backend/prisma/seed.js  — update test-seed comment table +
               any hardcoded SUP-001 references to SUP-0001.
           Auto-dash insertion in ID inputs:
             • mobile/app/(auth)/login.tsx  — smart handleChangeText that
               inserts '-' automatically after "TZ" or "SUP" prefix, so
               the user never types the dash manually.
             • mobile/app/(app)/admin.tsx   — same logic applied to the
               Employee-ID field in the Add-Attendant modal.

  Fix 3 → mobile/app/(app)/home.tsx
             Remove the refresh icon TouchableOpacity from the top bar
             (the pull-to-refresh on the ScrollView still works).

  Fix 4 → mobile/app/(app)/lookup.tsx
             • Remove the "Not in Registry" red card entirely.
             • While typing: validate format on every keystroke;
               if the partial entry already violates the allowed
               character pattern highlight border red immediately
               (no card, no inline text — just red border).
             • On VERIFY with an invalid format: shake + red border,
               no card.
             • On VERIFY with valid format but plate not in database:
               Alert.alert popup "Enter Valid vehicle Plate Number"
               with a single OK button; closes cleanly so the user
               can retype.

Usage
-----
  python3 patch2.py                        # run from repo root or mobile dir
  python3 patch2.py /path/to/PayPark-main  # explicit path
"""

import os
import re
import sys
import glob
import shutil
from pathlib import Path

# ── helpers ───────────────────────────────────────────────────────────────────

def resolve_root(argv):
    root = Path(argv[1]).expanduser().resolve() if len(argv) > 1 else Path.cwd()
    mobile = root / "mobile"
    if not mobile.is_dir():
        if (root / "app").is_dir():
            mobile = root          # user passed the mobile dir directly
        else:
            sys.exit(f"[patch2] ERROR: cannot find 'mobile/' under {root}")
    return root, mobile


def backup(path):
    bak = path.with_suffix(path.suffix + ".bak_patch2")
    if not bak.exists():
        shutil.copy2(path, bak)
        print(f"  [backup] {path.name} → .bak_patch2")


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  [write]  {path}")


# ══════════════════════════════════════════════════════════════════════════════
# FIX 1 — Remove *.bak_patch files
# ══════════════════════════════════════════════════════════════════════════════

def remove_bak_patch_files(root):
    pattern = str(root / "**" / "*.bak_patch")
    files = glob.glob(pattern, recursive=True)
    if not files:
        print("  [info]  No *.bak_patch files found — already clean.")
        return
    for f in sorted(files):
        os.remove(f)
        print(f"  [del]   {f}")
    print(f"  [done]  Removed {len(files)} backup file(s).")


# ══════════════════════════════════════════════════════════════════════════════
# FIX 2a — seed.js: update SUP-001 → SUP-0001
# ══════════════════════════════════════════════════════════════════════════════

def patch_seed_js(seed_path):
    if not seed_path.exists():
        print(f"  [WARN]  seed.js not found at {seed_path}")
        return
    backup(seed_path)
    src = seed_path.read_text(encoding="utf-8")

    # Replace any occurrence of 'SUP-001' with 'SUP-0001' (test supervisor id)
    new_src = src.replace("'SUP-001'", "'SUP-0001'").replace('"SUP-001"', '"SUP-0001"')

    # Also update seed table comment if it references SUP-001
    new_src = new_src.replace("SUP-001", "SUP-0001")

    if new_src == src:
        print("  [info]  seed.js — SUP-001 not found (may already be SUP-0001).")
    else:
        seed_path.write_text(new_src, encoding="utf-8")
        print("  [patch] seed.js — SUP-001 → SUP-0001")

    # Add/update the supervisor entry if missing
    if "SUP-0001" not in seed_path.read_text(encoding="utf-8"):
        # Append a supervisor upsert before the closing main() block
        src2 = seed_path.read_text(encoding="utf-8")
        supervisor_block = """
  // ── Supervisor (test) ─────────────────────────────────────────────────────
  const supervisor = await prisma.officer.upsert({
    where:  { employeeId: 'SUP-0001' },
    update: {},
    create: {
      employeeId:   'SUP-0001',
      fullName:     'Test Supervisor',
      phone:        '+255700000002',
      email:        'supervisor@parkipay.go.tz',
      role:         'SUPERVISOR',
      locationId:   dar.id,
    },
  });
  console.log(`  ✅ Supervisor: ${supervisor.employeeId} (${supervisor.fullName})`);
"""
        src2 = src2.replace(
            "  console.log('\\n🎉 Seed complete.",
            supervisor_block + "\n  console.log('\\n🎉 Seed complete."
        )
        seed_path.write_text(src2, encoding="utf-8")
        print("  [patch] seed.js — added SUP-0001 supervisor upsert block")


# ══════════════════════════════════════════════════════════════════════════════
# FIX 2b — login.tsx: auto-dash insertion in ID input
# ══════════════════════════════════════════════════════════════════════════════

LOGIN_TSX = r"""/**
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
"""


# ══════════════════════════════════════════════════════════════════════════════
# FIX 2c — admin.tsx: auto-dash in employee-ID field (targeted replacement)
# ══════════════════════════════════════════════════════════════════════════════

ADMIN_EMP_ID_OLD = \
"""          <Text style={[S.inputLabel, { color: C.textSub }]}>{tr('employeeIdLabel')}</Text>
          <TextInput style={[S.input, { color: C.text, borderColor: C.border, backgroundColor: C.bg }]}
            value={newEmpId} onChangeText={setNewEmpId} placeholder=\"TZ-XXXX or SUP-XXXX\"
            autoCapitalize=\"characters\" placeholderTextColor={C.textMuted}/>"""

ADMIN_EMP_ID_NEW = \
"""          <Text style={[S.inputLabel, { color: C.textSub }]}>{tr('employeeIdLabel')}</Text>
          <TextInput style={[S.input, { color: C.text, borderColor: C.border, backgroundColor: C.bg }]}
            value={newEmpId}
            onChangeText={raw => {
              // Auto-insert dash after TZ or SUP prefix
              const clean = raw.toUpperCase().replace(/[^A-Z0-9-]/g, '');
              const parts = clean.split('-');
              const prefix = parts[0];
              const digits = parts.slice(1).join('').replace(/[^0-9]/g, '');
              if ((prefix === 'TZ' || prefix === 'SUP') && parts.length === 1) {
                setNewEmpId(prefix + '-');
              } else if (parts.length >= 2) {
                setNewEmpId(prefix + '-' + digits.slice(0, 4));
              } else {
                setNewEmpId(prefix.slice(0, 3));
              }
            }}
            placeholder="TZ-XXXX or SUP-XXXX"
            autoCapitalize="characters"
            placeholderTextColor={C.textMuted}
          />"""


def patch_admin_emp_id(admin_path):
    if not admin_path.exists():
        print(f"  [WARN]  admin.tsx not found at {admin_path}")
        return
    backup(admin_path)
    src = admin_path.read_text(encoding="utf-8")

    if ADMIN_EMP_ID_OLD in src:
        src = src.replace(ADMIN_EMP_ID_OLD, ADMIN_EMP_ID_NEW)
        admin_path.write_text(src, encoding="utf-8")
        print("  [patch] admin.tsx — auto-dash applied to Employee ID field")
    else:
        # Fallback: use regex to patch onChangeText on the employee ID input
        pattern = r"(value=\{newEmpId\} onChangeText=\{setNewEmpId\})"
        replacement = (
            "value={newEmpId} onChangeText={raw => { "
            "const c=raw.toUpperCase().replace(/[^A-Z0-9-]/g,''); "
            "const p=c.split('-'); const px=p[0]; const dg=p.slice(1).join('').replace(/[^0-9]/g,''); "
            "if((px==='TZ'||px==='SUP')&&p.length===1){setNewEmpId(px+'-');} "
            "else if(p.length>=2){setNewEmpId(px+'-'+dg.slice(0,4));} "
            "else{setNewEmpId(px.slice(0,3));} }}"
        )
        new_src = re.sub(pattern, replacement, src, count=1)
        if new_src != src:
            admin_path.write_text(new_src, encoding="utf-8")
            print("  [patch] admin.tsx — auto-dash applied (regex fallback)")
        else:
            print("  [WARN]  admin.tsx — could not locate employee ID input; skipping auto-dash")


# ══════════════════════════════════════════════════════════════════════════════
# FIX 3 — home.tsx: remove refresh icon button from top bar
# ══════════════════════════════════════════════════════════════════════════════

HOME_REFRESH_OLD = """\
        <TouchableOpacity style={S.iconBtn} onPress={loadData}>
          <Ionicons name=\"refresh-outline\" size={22} color={C.headerText} />
        </TouchableOpacity>"""

HOME_REFRESH_NEW = """\
        {/* refresh icon removed — pull-to-refresh on scroll still works */}
        <View style={S.iconBtn} />"""


def patch_home_refresh(home_path):
    if not home_path.exists():
        print(f"  [WARN]  home.tsx not found at {home_path}")
        return
    backup(home_path)
    src = home_path.read_text(encoding="utf-8")

    if HOME_REFRESH_OLD in src:
        src = src.replace(HOME_REFRESH_OLD, HOME_REFRESH_NEW)
        home_path.write_text(src, encoding="utf-8")
        print("  [patch] home.tsx — refresh icon removed from top bar")
    else:
        # Regex fallback
        pattern = (
            r'<TouchableOpacity\s+style=\{S\.iconBtn\}\s+onPress=\{loadData\}>\s*'
            r'<Ionicons\s+name="refresh-outline"[^/]*/>\s*'
            r'</TouchableOpacity>'
        )
        new_src = re.sub(
            pattern,
            '{/* refresh icon removed */}\n        <View style={S.iconBtn} />',
            src,
            count=1,
        )
        if new_src != src:
            home_path.write_text(new_src, encoding="utf-8")
            print("  [patch] home.tsx — refresh icon removed (regex fallback)")
        else:
            print("  [WARN]  home.tsx — refresh button pattern not matched; check manually")


# ══════════════════════════════════════════════════════════════════════════════
# FIX 4 — lookup.tsx: real-time format border, popup for not-found, no cards
# ══════════════════════════════════════════════════════════════════════════════

LOOKUP_TSX = r"""/**
 * ParkiPay — Vehicle Lookup Screen  (patch2)
 *
 * Changes vs patch1:
 *  • While typing: red border immediately if characters violate the
 *    allowed pattern — no card, no text error shown mid-typing.
 *  • On VERIFY with invalid format: shake + red border (no card).
 *  • On VERIFY with valid format but plate not in DB: Alert popup
 *    "Enter Valid vehicle Plate Number" → OK closes it, user retypes.
 *  • "Not in Registry" red card fully removed.
 *  • Camera and refresh icon already removed in patch1 (kept removed).
 */
import { useState, useRef, useCallback } from 'react';
import {
  ActivityIndicator,
  Alert,
  Animated,
  Keyboard,
  Modal,
  Platform,
  Pressable,
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  ToastAndroid,
  TouchableOpacity,
  View,
} from 'react-native';
import * as ExpoClipboard  from 'expo-clipboard';
import { LinearGradient }  from 'expo-linear-gradient';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import * as Haptics        from 'expo-haptics';
import { router }          from 'expo-router';
import { useAuthStore }               from '@/store/authStore';
import { useSettingsStore, palette }  from '@/store/settingsStore';
import { vehicleService, billingService } from '@/services/api';
import { SprintColors }               from '@/constants/theme';
import ConfirmModal                   from '@/components/ConfirmModal';
import {
  pushBillSuccess, pushDuplicateAlert, pushBillFailed,
} from '@/services/alertsService';

// ── Plate helpers ──────────────────────────────────────────────────────────
// Tanzania: T + 3 digits + 3 uppercase letters  → e.g. T000AAA
const PLATE_RE = /^T\d{3}[A-Z]{3}$/;

// Allowed characters at each position while typing (7 chars max, no spaces stored)
// pos 0 : T
// pos 1-3: digits
// pos 4-6: letters
function isPartialValid(raw: string): boolean {
  if (raw.length === 0) return true;
  if (raw[0] !== 'T') return false;
  for (let i = 1; i < Math.min(raw.length, 4); i++) {
    if (!/\d/.test(raw[i])) return false;
  }
  for (let i = 4; i < raw.length; i++) {
    if (!/[A-Z]/.test(raw[i])) return false;
  }
  return true;
}

function formatPlate(raw: string): string {
  const s = raw.replace(/\s/g, '');
  if (s.length <= 1) return s;
  if (s.length <= 4) return s[0] + ' ' + s.slice(1);
  return s[0] + ' ' + s.slice(1, 4) + ' ' + s.slice(4);
}

// ── Types ──────────────────────────────────────────────────────────────────
interface VehicleInfo {
  id: number; plateNumber: string; ownerName: string;
  ownerPhone: string; make?: string; model?: string; category?: string;
}
interface ActiveBill {
  control_number: string; expires_at: string; issued_by: string | null;
  officer_id: string | null; location: string | null;
  amount_due: number | string; generated_at: string;
}
interface GeneratedBill { controlNumber: string; amountDue: number; }
type LookupState =
  | 'idle' | 'loading' | 'found'
  | 'duplicate' | 'generating' | 'success';

// ── Component ──────────────────────────────────────────────────────────────
export default function LookupScreen() {
  const { officer }  = useAuthStore();
  const { theme }    = useSettingsStore();
  const C            = palette(theme);
  const S            = makeStyles(C);

  const [plateRaw,    setPlateRaw]    = useState('');
  const [lookupState, setLookupState] = useState<LookupState>('idle');
  const [vehicle,     setVehicle]     = useState<VehicleInfo | null>(null);
  const [activeBill,  setActiveBill]  = useState<ActiveBill | null>(null);
  const [genBill,     setGenBill]     = useState<GeneratedBill | null>(null);
  const [cnCopied,    setCnCopied]    = useState(false);
  const [allowedAfter, setAllowedAfter] = useState<string | null>(null);

  // Real-time format error (red border only while typing)
  const [borderError, setBorderError] = useState(false);

  const [showDupModal,        setShowDupModal]        = useState(false);
  const [showSuccessModal,    setShowSuccessModal]     = useState(false);
  const [showGenerateConfirm, setShowGenerateConfirm] = useState(false);

  const shakeAnim = useRef(new Animated.Value(0)).current;

  const shake = () => {
    Animated.sequence([
      Animated.timing(shakeAnim, { toValue:  8, duration: 55, useNativeDriver: true }),
      Animated.timing(shakeAnim, { toValue: -8, duration: 55, useNativeDriver: true }),
      Animated.timing(shakeAnim, { toValue:  4, duration: 45, useNativeDriver: true }),
      Animated.timing(shakeAnim, { toValue:  0, duration: 45, useNativeDriver: true }),
    ]).start();
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
  };

  const normalisePlate = (raw: string) => raw.trim().toUpperCase().replace(/\s/g, '');

  // ── Handle text change: real-time border feedback ────────────────────────
  const handlePlateChange = (text: string) => {
    // Strip spaces, force uppercase, keep only T/digit/letter chars
    const raw = text.replace(/\s/g, '').toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 7);
    setPlateRaw(raw);
    if (lookupState !== 'idle') setLookupState('idle');
    // Show red border if partial entry is already invalid
    setBorderError(raw.length > 0 && !isPartialValid(raw));
  };

  // ── Verify ───────────────────────────────────────────────────────────────
  const handleVerify = async () => {
    Keyboard.dismiss();
    const plate = normalisePlate(plateRaw);

    // Guard: invalid format
    if (!PLATE_RE.test(plate)) {
      shake();
      setBorderError(true);
      return;  // no card, no text — just red border + shake
    }

    setBorderError(false);
    setLookupState('loading');
    setVehicle(null);
    setActiveBill(null);
    setAllowedAfter(null);

    try {
      const [vRes, bRes] = await Promise.allSettled([
        vehicleService.lookup(plate),
        billingService.activeBill(plate, officer?.locationId ?? undefined),
      ]);

      const foundVehicle: VehicleInfo | null =
        vRes.status === 'fulfilled' ? (vRes.value.data as VehicleInfo) : null;
      const billData = bRes.status === 'fulfilled' ? bRes.value.data : null;

      setVehicle(foundVehicle);

      if (billData?.active && billData.bill) {
        setActiveBill(billData.bill);
        setAllowedAfter(billData.allowed_after ?? null);
        setLookupState('duplicate');
        setShowDupModal(true);
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
        pushDuplicateAlert({
          plateNumber:   plate,
          controlNumber: billData.bill.control_number ?? '',
          location:      billData.bill.location       ?? undefined,
          issuedAt:      billData.bill.generated_at   ?? undefined,
          expiresAt:     billData.bill.expires_at      ?? undefined,
        });
      } else if (foundVehicle) {
        setLookupState('found');
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      } else {
        // Valid format but NOT in database → Alert popup only, no card
        setLookupState('idle');
        shake();
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
        Alert.alert(
          'Vehicle Not Found',
          'Enter Valid vehicle Plate Number',
          [{ text: 'OK', onPress: () => { setPlateRaw(''); setBorderError(false); } }],
          { cancelable: false }
        );
      }
    } catch {
      setLookupState('idle');
      shake();
    }
  };

  // ── Generate bill ─────────────────────────────────────────────────────────
  const handleGenerateBill = useCallback(async () => {
    setShowGenerateConfirm(false);
    if (!officer?.locationId) return;
    const plate = normalisePlate(plateRaw);
    setLookupState('generating');

    try {
      const res  = await billingService.generate(plate, officer.locationId);
      const bill = res.data;
      const generated: GeneratedBill = {
        controlNumber: bill.controlNumber as string,
        amountDue:     Number(bill.amountDue),
      };
      setGenBill(generated);
      setLookupState('success');
      setShowSuccessModal(true);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      pushBillSuccess({
        plateNumber:   plate,
        controlNumber: generated.controlNumber,
        location:      (bill.location?.name as string | undefined) ?? officer?.locationName ?? 'Unknown',
        issuedAt:      (bill.generatedAt as string | undefined)    ?? new Date().toISOString(),
        expiresAt:     (bill.expiresAt   as string | undefined)    ?? '',
      });
    } catch (e: unknown) {
      const err = e as { response?: { status?: number; data?: { existing_bill?: ActiveBill; allowed_after?: string; detail?: string } } };
      if (err?.response?.status === 409 && err.response.data?.existing_bill) {
        setActiveBill(err.response.data.existing_bill);
        setAllowedAfter(err.response.data.allowed_after ?? null);
        setLookupState('duplicate');
        setShowDupModal(true);
      } else {
        const reason = err?.response?.data?.detail ?? 'Unknown error';
        pushBillFailed({ plateNumber: normalisePlate(plateRaw), reason });
        setLookupState(vehicle !== null ? 'found' : 'idle');
      }
    }
  }, [officer, plateRaw, vehicle]);

  // ── Copy CN ───────────────────────────────────────────────────────────────
  const copyControlNumber = async () => {
    if (!genBill?.controlNumber) return;
    await ExpoClipboard.setStringAsync(genBill.controlNumber);
    setCnCopied(true);
    if (Platform.OS === 'android') ToastAndroid.show('Copied!', ToastAndroid.SHORT);
    setTimeout(() => setCnCopied(false), 3000);
  };

  // ── Reset ─────────────────────────────────────────────────────────────────
  const reset = () => {
    setPlateRaw(''); setVehicle(null); setActiveBill(null);
    setGenBill(null); setLookupState('idle'); setCnCopied(false);
    setAllowedAfter(null); setBorderError(false);
    setShowDupModal(false); setShowSuccessModal(false); setShowGenerateConfirm(false);
  };

  const topOffset  = Platform.OS === 'android' ? (StatusBar.currentHeight ?? 24) : 0;
  const isLoading  = lookupState === 'loading' || lookupState === 'generating';
  const plate      = normalisePlate(plateRaw);

  const allowedAfterStr = allowedAfter
    ? new Date(allowedAfter).toLocaleTimeString('en-TZ', {
        hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true,
      })
    : null;

  return (
    <SafeAreaView style={[S.root, { backgroundColor: C.bg, paddingTop: topOffset }]}>

      {/* Header — no refresh icon */}
      <View style={[S.header, { backgroundColor: C.headerBg }]}>
        <TouchableOpacity onPress={() => router.back()} style={S.iconBtn}>
          <Ionicons name="arrow-back" size={22} color="#fff" />
        </TouchableOpacity>
        <View style={{ alignItems: 'center' }}>
          <Text style={S.headerTitle}>Vehicle Lookup</Text>
          <Text style={S.headerSub}>Enter plate number to verify</Text>
        </View>
        {/* Spacer keeps title centred */}
        <View style={S.iconBtn} />
      </View>

      <ScrollView contentContainerStyle={S.body} keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}>

        {/* Plate Input */}
        <Text style={[S.inputLabel, { color: C.textSub }]}>LICENSE PLATE NUMBER</Text>
        <Animated.View style={[
          S.inputRow,
          {
            transform: [{ translateX: shakeAnim }],
            backgroundColor: C.card,
            // Red border: either real-time format mismatch OR post-verify invalid
            borderColor: borderError ? '#EF4444' : C.border,
          },
        ]}>
          <MaterialCommunityIcons name="car-outline" size={22} color={C.textMuted}
            style={{ marginRight: 8 }} />
          <TextInput
            style={[S.plateInput, { color: C.text, flex: 1 }]}
            value={formatPlate(plateRaw)}
            onChangeText={handlePlateChange}
            placeholder="T 000 AAA"
            placeholderTextColor={C.textMuted}
            autoCapitalize="characters"
            autoCorrect={false}
            returnKeyType="search"
            onSubmitEditing={handleVerify}
            maxLength={9}   // "T 000 AAA" = 9 chars with spaces
          />
          {plateRaw.length > 0 && (
            <TouchableOpacity onPress={() => { setPlateRaw(''); setBorderError(false); setLookupState('idle'); }}>
              <Ionicons name="close-circle" size={20} color={C.textMuted} />
            </TouchableOpacity>
          )}
        </Animated.View>

        {/* Subtle format hint — always visible */}
        <Text style={[S.hintText, { color: borderError ? '#EF4444' : C.textMuted }]}>
          Format: T + 3 digits + 3 letters  (e.g. T 566 GHH)
        </Text>

        {/* Verify button — full width, no camera button */}
        <TouchableOpacity
          style={[S.verifyBtn, (isLoading || plate.length < 7) && { opacity: 0.6 }]}
          onPress={handleVerify}
          disabled={isLoading || plate.length < 7}
          activeOpacity={0.85}
        >
          <LinearGradient colors={['#1EB53A', '#158A2A']}
            start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={S.verifyGrad}>
            {isLoading
              ? <ActivityIndicator color="#fff" size="small" />
              : <>
                  <MaterialCommunityIcons name="shield-check-outline" size={18} color="#fff" />
                  <Text style={S.verifyText}>VERIFY</Text>
                </>
            }
          </LinearGradient>
        </TouchableOpacity>

        {/* Vehicle Found Card */}
        {lookupState === 'found' && vehicle !== null && (
          <View style={[S.resultCard, { backgroundColor: C.card, borderColor: SprintColors.green }]}>
            <View style={S.resultHeaderRow}>
              <View style={[S.resultIconBg, { backgroundColor: 'rgba(30,181,58,0.12)' }]}>
                <MaterialCommunityIcons name="check-circle" size={22} color={SprintColors.green} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={[S.resultTitle, { color: C.text }]}>Vehicle Found</Text>
                <Text style={[S.resultSub, { color: C.textSub }]}>Registered in ParkiPay</Text>
              </View>
              <View style={[S.plateTag, { borderColor: '#1A1A1A' }]}>
                <Text style={S.plateTagText}>{formatPlate(plateRaw)}</Text>
              </View>
            </View>

            {([
              { icon: 'account-outline', label: 'Owner',    val: vehicle.ownerName },
              { icon: 'phone-outline',   label: 'Phone',    val: vehicle.ownerPhone },
              { icon: 'car-outline',     label: 'Vehicle',  val: [vehicle.make, vehicle.model].filter(Boolean).join(' ') || '—' },
              { icon: 'tag-outline',     label: 'Category', val: (vehicle.category ?? 'PRIVATE_CAR').replace(/_/g, ' ') },
            ] as const).map(r => (
              <View key={r.label} style={[S.detailRow, { borderBottomColor: C.border }]}>
                <MaterialCommunityIcons name={r.icon as any} size={15} color={C.textMuted} />
                <Text style={[S.detailLabel, { color: C.textSub }]}>{r.label}</Text>
                <Text style={[S.detailVal,   { color: C.text  }]}>{r.val}</Text>
              </View>
            ))}

            <TouchableOpacity style={S.genBtn} onPress={() => setShowGenerateConfirm(true)}>
              <LinearGradient colors={['#1EB53A', '#158A2A']}
                start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={S.genBtnGrad}>
                <MaterialCommunityIcons name="receipt" size={18} color="#fff" />
                <Text style={S.genBtnText}>Generate Bill</Text>
              </LinearGradient>
            </TouchableOpacity>
          </View>
        )}

        <View style={{ height: 40 }} />
      </ScrollView>

      {/* Generate Confirm */}
      <ConfirmModal
        visible={showGenerateConfirm}
        title="Generate Parking Bill?"
        message={`Issue a parking bill for ${formatPlate(plateRaw)}?${!officer?.locationId ? '\n\n⚠ No location assigned.' : ''}`}
        confirmLabel="Generate Bill"
        cancelLabel="Cancel"
        variant="success"
        onConfirm={handleGenerateBill}
        onCancel={() => setShowGenerateConfirm(false)}
      />

      {/* Duplicate Modal */}
      <Modal visible={showDupModal} transparent animationType="slide"
        onRequestClose={() => setShowDupModal(false)}>
        <Pressable style={S.modalBackdrop} onPress={() => setShowDupModal(false)} />
        <View style={[S.modalSheet, { backgroundColor: C.card }]}>
          <View style={S.dupIconWrap}>
            <MaterialCommunityIcons name="alert" size={30} color={SprintColors.yellow} />
          </View>
          <Text style={[S.modalTitle, { color: C.text }]}>Duplicate Bill Blocked</Text>
          <Text style={[S.modalSub, { color: C.textSub }]}>
            A bill was already issued for this vehicle at this location.
          </Text>

          {allowedAfterStr && (
            <View style={[S.cooldownBox, { backgroundColor: 'rgba(252,209,22,0.1)', borderColor: SprintColors.yellow }]}>
              <Ionicons name="time-outline" size={18} color={SprintColors.yellow} />
              <View style={{ flex: 1 }}>
                <Text style={[S.cooldownTitle, { color: C.text }]}>Next bill allowed at:</Text>
                <Text style={[S.cooldownTime, { color: SprintColors.yellow }]}>{allowedAfterStr}</Text>
              </View>
            </View>
          )}

          <View style={[S.dupCard, { borderColor: SprintColors.yellow }]}>
            <View style={S.dupCardHeader}>
              <Text style={S.dupCardHeaderText}>EXISTING BILL</Text>
              <View style={S.liveBadge}><View style={S.liveDot} /><Text style={S.liveBadgeText}>LIVE</Text></View>
            </View>
            <View style={[S.plateTag, { borderColor: '#1A1A1A', alignSelf: 'center', marginVertical: 10, backgroundColor: '#fff' }]}>
              <Text style={[S.plateTagText, { fontSize: 20 }]}>{formatPlate(plateRaw)}</Text>
            </View>
            {[
              { label: 'Control Number', value: activeBill?.control_number ?? '—' },
              { label: 'Time Issued',    value: activeBill?.generated_at
                  ? new Date(activeBill.generated_at).toLocaleTimeString('en-TZ',
                      { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true }) : '—' },
              { label: 'Issued By',      value: activeBill?.issued_by ?? '—' },
              { label: 'Location',       value: activeBill?.location  ?? '—' },
              { label: 'Amount Due',     value: activeBill?.amount_due != null
                  ? `TZS ${Number(activeBill.amount_due).toLocaleString()}` : '—' },
            ].map(r => (
              <View key={r.label} style={[S.dupRow, { borderBottomColor: 'rgba(0,0,0,0.07)' }]}>
                <Text style={[S.dupLabel, { color: C.textSub }]}>{r.label}</Text>
                <Text style={[S.dupValue, { color: C.text }]}>{r.value}</Text>
              </View>
            ))}
          </View>

          <TouchableOpacity style={[S.closeSheetBtn, { borderColor: C.border }]}
            onPress={() => { setShowDupModal(false); reset(); }}>
            <Text style={[S.closeSheetText, { color: C.textSub }]}>New Lookup</Text>
          </TouchableOpacity>
        </View>
      </Modal>

      {/* Success Modal */}
      <Modal visible={showSuccessModal} transparent animationType="fade" onRequestClose={reset}>
        <View style={S.successBackdrop}>
          <View style={[S.successCard, { backgroundColor: C.card }]}>
            <LinearGradient colors={['#1EB53A', '#158A2A']}
              start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={S.successIconWrap}>
              <Ionicons name="checkmark" size={36} color="#fff" />
            </LinearGradient>
            <Text style={[S.successTitle, { color: C.text }]}>Bill Generated!</Text>
            <Text style={[S.successSub,   { color: C.textSub }]}>
              Parking bill issued successfully.
              {vehicle?.ownerPhone ? ' SMS sent to owner.' : ''}
            </Text>
            <View style={[S.cnBox, { backgroundColor: C.bg }]}>
              <Text style={[S.cnLabel, { color: C.textSub }]}>CONTROL NUMBER</Text>
              <View style={S.cnRow}>
                <Text style={[S.cnVal, { color: C.text }]}>{genBill?.controlNumber}</Text>
                <TouchableOpacity
                  style={[S.copyBtn, { backgroundColor: cnCopied ? 'rgba(30,181,58,0.15)' : 'rgba(0,0,0,0.07)' }]}
                  onPress={copyControlNumber}>
                  <Ionicons name={cnCopied ? 'checkmark' : 'copy-outline'} size={18}
                    color={cnCopied ? SprintColors.green : C.textMuted} />
                </TouchableOpacity>
              </View>
              <Text style={[S.cnAmt, { color: SprintColors.green }]}>
                TZS {genBill?.amountDue?.toLocaleString()}
              </Text>
            </View>
            <TouchableOpacity style={S.doneBtn} onPress={reset}>
              <Text style={S.doneBtnText}>New Lookup</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={() => { reset(); router.back(); }}>
              <Text style={[S.backText, { color: C.textSub }]}>Back to Dashboard</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
function makeStyles(C: ReturnType<typeof palette>) {
  return StyleSheet.create({
    root:        { flex: 1 },
    header:      { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, paddingVertical: 14 },
    iconBtn:     { width: 38, height: 38, borderRadius: 10, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(255,255,255,0.1)' },
    headerTitle: { fontSize: 17, fontWeight: '800', color: '#fff' },
    headerSub:   { fontSize: 11, color: 'rgba(255,255,255,0.6)', textAlign: 'center' },
    body:        { padding: 16, paddingBottom: 32 },
    inputLabel:  { fontSize: 11, fontWeight: '700', letterSpacing: 1.5, textTransform: 'uppercase', marginBottom: 8 },
    inputRow:    { flexDirection: 'row', alignItems: 'center', borderWidth: 2, borderRadius: 14, paddingHorizontal: 14, height: 60, marginBottom: 4 },
    plateInput:  { fontSize: 24, fontWeight: '800', letterSpacing: 4 },
    hintText:    { fontSize: 11, marginBottom: 12 },
    verifyBtn:   { borderRadius: 14, overflow: 'hidden', marginBottom: 16,
      shadowColor: SprintColors.green, shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.3, shadowRadius: 10, elevation: 6 },
    verifyGrad:  { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, height: 52 },
    verifyText:  { color: '#fff', fontSize: 14, fontWeight: '900', letterSpacing: 0.8 },
    // Vehicle found card
    resultCard:      { borderRadius: 16, borderWidth: 2, padding: 16, marginBottom: 14, shadowColor: '#000', shadowOffset: { width: 0, height: 3 }, shadowOpacity: 0.08, shadowRadius: 8, elevation: 4 },
    resultHeaderRow: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 14 },
    resultIconBg:    { width: 44, height: 44, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
    resultTitle:     { fontSize: 16, fontWeight: '800', marginBottom: 2 },
    resultSub:       { fontSize: 12, lineHeight: 18 },
    plateTag:        { paddingHorizontal: 12, paddingVertical: 7, borderRadius: 8, borderWidth: 2, alignItems: 'center', justifyContent: 'center' },
    plateTagText:    { fontSize: 16, fontWeight: '900', letterSpacing: 3, color: '#1A1A1A' },
    detailRow:       { flexDirection: 'row', alignItems: 'center', gap: 8, paddingVertical: 8, borderBottomWidth: 1 },
    detailLabel:     { width: 70, fontSize: 12, fontWeight: '600' },
    detailVal:       { flex: 1, fontSize: 13, fontWeight: '700' },
    genBtn:          { borderRadius: 12, overflow: 'hidden', marginTop: 14, shadowColor: SprintColors.green, shadowOffset: { width: 0, height: 3 }, shadowOpacity: 0.3, shadowRadius: 8, elevation: 5 },
    genBtnGrad:      { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10, height: 50 },
    genBtnText:      { color: '#fff', fontSize: 15, fontWeight: '900' },
    // Duplicate modal
    modalBackdrop:   { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)' },
    modalSheet:      { borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: 20, paddingBottom: 40 },
    dupIconWrap:     { width: 60, height: 60, borderRadius: 18, backgroundColor: 'rgba(252,209,22,0.15)', alignItems: 'center', justifyContent: 'center', alignSelf: 'center', marginBottom: 12 },
    modalTitle:      { fontSize: 19, fontWeight: '900', textAlign: 'center', marginBottom: 6 },
    modalSub:        { fontSize: 13, textAlign: 'center', marginBottom: 14 },
    cooldownBox:     { flexDirection: 'row', alignItems: 'center', gap: 10, padding: 12, borderRadius: 12, borderWidth: 1.5, marginBottom: 14 },
    cooldownTitle:   { fontSize: 12, fontWeight: '600', marginBottom: 2 },
    cooldownTime:    { fontSize: 16, fontWeight: '900' },
    dupCard:         { borderWidth: 2, borderRadius: 14, padding: 14, marginBottom: 14, backgroundColor: 'rgba(252,209,22,0.04)' },
    dupCardHeader:   { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
    dupCardHeaderText: { fontSize: 10, fontWeight: '800', color: '#C9A800', letterSpacing: 1, textTransform: 'uppercase' },
    liveBadge:       { flexDirection: 'row', alignItems: 'center', gap: 5, backgroundColor: '#C9A800', paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
    liveDot:         { width: 6, height: 6, borderRadius: 3, backgroundColor: '#fff' },
    liveBadgeText:   { color: '#fff', fontSize: 10, fontWeight: '800' },
    dupRow:          { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 7, borderBottomWidth: 1 },
    dupLabel:        { fontSize: 11, fontWeight: '600' },
    dupValue:        { fontSize: 11, fontWeight: '700', maxWidth: '60%', textAlign: 'right' },
    closeSheetBtn:   { height: 46, borderRadius: 10, alignItems: 'center', justifyContent: 'center', borderWidth: 1 },
    closeSheetText:  { fontWeight: '600', fontSize: 14 },
    // Success
    successBackdrop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)', alignItems: 'center', justifyContent: 'center', padding: 24 },
    successCard:     { width: '100%', borderRadius: 24, padding: 26, alignItems: 'center', shadowColor: '#000', shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.2, shadowRadius: 20, elevation: 12 },
    successIconWrap: { width: 76, height: 76, borderRadius: 22, alignItems: 'center', justifyContent: 'center', marginBottom: 14 },
    successTitle:    { fontSize: 21, fontWeight: '900', marginBottom: 8 },
    successSub:      { fontSize: 13, textAlign: 'center', lineHeight: 20, marginBottom: 18 },
    cnBox:    { width: '100%', borderRadius: 14, padding: 16, alignItems: 'center', marginBottom: 18 },
    cnLabel:  { fontSize: 10, fontWeight: '700', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 6 },
    cnRow:    { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 4 },
    cnVal:    { fontSize: 22, fontWeight: '900', letterSpacing: 3 },
    copyBtn:  { width: 36, height: 36, borderRadius: 10, alignItems: 'center', justifyContent: 'center' },
    cnAmt:    { fontSize: 19, fontWeight: '800' },
    doneBtn:  { width: '100%', height: 50, borderRadius: 12, backgroundColor: SprintColors.green, alignItems: 'center', justifyContent: 'center', marginBottom: 12 },
    doneBtnText: { color: '#fff', fontSize: 15, fontWeight: '900' },
    backText:    { fontSize: 13, fontWeight: '600' },
  });
}
"""


# ══════════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════════

def main():
    root, mobile = resolve_root(sys.argv)
    print(f"\n[patch2] Project root : {root}")
    print(f"[patch2] Mobile dir   : {mobile}\n")

    # ── Fix 1: remove *.bak_patch files ──────────────────────────────────────
    print("── Fix 1: Remove old *.bak_patch backup files ──────────────────────")
    remove_bak_patch_files(root)

    # ── Fix 2a: seed.js supervisor ID ────────────────────────────────────────
    print("\n── Fix 2a: seed.js — SUP-001 → SUP-0001 ───────────────────────────")
    seed = root / "backend" / "prisma" / "seed.js"
    patch_seed_js(seed)

    # ── Fix 2b: login.tsx — auto-dash ────────────────────────────────────────
    print("\n── Fix 2b: login.tsx — auto-dash insertion ─────────────────────────")
    login = mobile / "app" / "(auth)" / "login.tsx"
    backup(login)
    write(login, LOGIN_TSX)

    # ── Fix 2c: admin.tsx — auto-dash in employee-ID field ───────────────────
    print("\n── Fix 2c: admin.tsx — auto-dash in Add-Attendant Employee ID field ─")
    admin = mobile / "app" / "(app)" / "admin.tsx"
    patch_admin_emp_id(admin)

    # ── Fix 3: home.tsx — remove top-bar refresh icon ────────────────────────
    print("\n── Fix 3: home.tsx — remove top-bar refresh icon ───────────────────")
    home = mobile / "app" / "(app)" / "home.tsx"
    patch_home_refresh(home)

    # ── Fix 4: lookup.tsx — real-time border, popup alert, no cards ──────────
    print("\n── Fix 4: lookup.tsx — border validation + popup alert ─────────────")
    lookup = mobile / "app" / "(app)" / "lookup.tsx"
    backup(lookup)
    write(lookup, LOOKUP_TSX)

    print("\n[patch2] ✓ All fixes applied.\n")
    print("Next steps:")
    print("  cd mobile && npx expo start")
    print("  (If you changed seed data: cd backend && npm run db:seed)\n")
    print("  Backups saved as *.bak_patch2 next to each modified file.\n")


if __name__ == "__main__":
    main()

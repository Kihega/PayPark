/**
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
import { moderateScale } from '@/utils/responsive';

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
              <Text style={[S.plateTagText, { fontSize: moderateScale(20) }]}>{formatPlate(plateRaw)}</Text>
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
            </Text>
            {!!vehicle?.ownerPhone && (
              <View style={S.smsNoteRow}>
                <Ionicons name="information-circle-outline" size={16} color={SprintColors.green} />
                <Text style={[S.smsNoteText, { color: C.textSub }]}>
                  An SMS confirmation has been sent to the owner&apos;s phone number.
                </Text>
              </View>
            )}
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
    headerTitle: { fontSize: moderateScale(17), fontWeight: '800', color: '#fff' },
    headerSub:   { fontSize: moderateScale(11), color: 'rgba(255,255,255,0.6)', textAlign: 'center' },
    body:        { padding: 16, paddingBottom: 32 },
    inputLabel:  { fontSize: moderateScale(11), fontWeight: '700', letterSpacing: 1.5, textTransform: 'uppercase', marginBottom: 8 },
    inputRow:    { flexDirection: 'row', alignItems: 'center', borderWidth: 2, borderRadius: 14, paddingHorizontal: 14, height: 60, marginBottom: 4 },
    plateInput:  { fontSize: moderateScale(24), fontWeight: '800', letterSpacing: 4 },
    hintText:    { fontSize: moderateScale(11), marginBottom: 12 },
    verifyBtn:   { borderRadius: 14, overflow: 'hidden', marginBottom: 16,
      shadowColor: SprintColors.green, shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.3, shadowRadius: 10, elevation: 6 },
    verifyGrad:  { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, height: 52 },
    verifyText:  { color: '#fff', fontSize: moderateScale(14), fontWeight: '900', letterSpacing: 0.8 },
    // Vehicle found card
    resultCard:      { borderRadius: 16, borderWidth: 2, padding: 16, marginBottom: 14, shadowColor: '#000', shadowOffset: { width: 0, height: 3 }, shadowOpacity: 0.08, shadowRadius: 8, elevation: 4 },
    resultHeaderRow: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 14 },
    resultIconBg:    { width: 44, height: 44, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
    resultTitle:     { fontSize: moderateScale(16), fontWeight: '800', marginBottom: 2 },
    resultSub:       { fontSize: moderateScale(12), lineHeight: 18 },
    plateTag:        { paddingHorizontal: 12, paddingVertical: 7, borderRadius: 8, borderWidth: 2, alignItems: 'center', justifyContent: 'center' },
    plateTagText:    { fontSize: moderateScale(16), fontWeight: '900', letterSpacing: 3, color: '#1A1A1A' },
    detailRow:       { flexDirection: 'row', alignItems: 'center', gap: 8, paddingVertical: 8, borderBottomWidth: 1 },
    detailLabel:     { width: 70, fontSize: moderateScale(12), fontWeight: '600' },
    detailVal:       { flex: 1, fontSize: moderateScale(13), fontWeight: '700' },
    genBtn:          { borderRadius: 12, overflow: 'hidden', marginTop: 14, shadowColor: SprintColors.green, shadowOffset: { width: 0, height: 3 }, shadowOpacity: 0.3, shadowRadius: 8, elevation: 5 },
    genBtnGrad:      { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10, height: 50 },
    genBtnText:      { color: '#fff', fontSize: moderateScale(15), fontWeight: '900' },
    // Duplicate modal
    modalBackdrop:   { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)' },
    modalSheet:      { borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: 20, paddingBottom: 40 },
    dupIconWrap:     { width: 60, height: 60, borderRadius: 18, backgroundColor: 'rgba(252,209,22,0.15)', alignItems: 'center', justifyContent: 'center', alignSelf: 'center', marginBottom: 12 },
    modalTitle:      { fontSize: moderateScale(19), fontWeight: '900', textAlign: 'center', marginBottom: 6 },
    modalSub:        { fontSize: moderateScale(13), textAlign: 'center', marginBottom: 14 },
    cooldownBox:     { flexDirection: 'row', alignItems: 'center', gap: 10, padding: 12, borderRadius: 12, borderWidth: 1.5, marginBottom: 14 },
    cooldownTitle:   { fontSize: moderateScale(12), fontWeight: '600', marginBottom: 2 },
    cooldownTime:    { fontSize: moderateScale(16), fontWeight: '900' },
    dupCard:         { borderWidth: 2, borderRadius: 14, padding: 14, marginBottom: 14, backgroundColor: 'rgba(252,209,22,0.04)' },
    dupCardHeader:   { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
    dupCardHeaderText: { fontSize: moderateScale(10), fontWeight: '800', color: '#C9A800', letterSpacing: 1, textTransform: 'uppercase' },
    liveBadge:       { flexDirection: 'row', alignItems: 'center', gap: 5, backgroundColor: '#C9A800', paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
    liveDot:         { width: 6, height: 6, borderRadius: 3, backgroundColor: '#fff' },
    liveBadgeText:   { color: '#fff', fontSize: moderateScale(10), fontWeight: '800' },
    dupRow:          { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 7, borderBottomWidth: 1 },
    dupLabel:        { fontSize: moderateScale(11), fontWeight: '600' },
    dupValue:        { fontSize: moderateScale(11), fontWeight: '700', maxWidth: '60%', textAlign: 'right' },
    closeSheetBtn:   { height: 46, borderRadius: 10, alignItems: 'center', justifyContent: 'center', borderWidth: 1 },
    closeSheetText:  { fontWeight: '600', fontSize: moderateScale(14) },
    // Success
    successBackdrop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)', alignItems: 'center', justifyContent: 'center', padding: 24 },
    successCard:     { width: '100%', borderRadius: 24, padding: 26, alignItems: 'center', shadowColor: '#000', shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.2, shadowRadius: 20, elevation: 12 },
    successIconWrap: { width: 76, height: 76, borderRadius: 22, alignItems: 'center', justifyContent: 'center', marginBottom: 14 },
    successTitle:    { fontSize: moderateScale(21), fontWeight: '900', marginBottom: 8 },
    successSub:      { fontSize: moderateScale(13), textAlign: 'center', lineHeight: 20, marginBottom: 18 },
    smsNoteRow:      { flexDirection: 'row', gap: 8, padding: 10, borderRadius: 10,
      backgroundColor: 'rgba(30,181,58,0.06)', borderLeftWidth: 3,
      borderLeftColor: SprintColors.green, marginBottom: 18, alignItems: 'flex-start', width: '100%' },
    smsNoteText:     { flex: 1, fontSize: moderateScale(12), lineHeight: 17 },
    cnBox:    { width: '100%', borderRadius: 14, padding: 16, alignItems: 'center', marginBottom: 18 },
    cnLabel:  { fontSize: moderateScale(10), fontWeight: '700', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 6 },
    cnRow:    { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 4 },
    cnVal:    { fontSize: moderateScale(22), fontWeight: '900', letterSpacing: 3 },
    copyBtn:  { width: 36, height: 36, borderRadius: 10, alignItems: 'center', justifyContent: 'center' },
    cnAmt:    { fontSize: moderateScale(19), fontWeight: '800' },
    doneBtn:  { width: '100%', height: 50, borderRadius: 12, backgroundColor: SprintColors.green, alignItems: 'center', justifyContent: 'center', marginBottom: 12 },
    doneBtnText: { color: '#fff', fontSize: moderateScale(15), fontWeight: '900' },
    backText:    { fontSize: moderateScale(13), fontWeight: '600' },
  });
}

/**
 * ParkiPay — Reusable Confirm / Alert Modal
 * Replaces native Alert.alert with a polished card dialog.
 */
import { Modal, Pressable, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSettingsStore, palette } from '@/store/settingsStore';
import { moderateScale } from '@/utils/responsive';

export type ConfirmVariant = 'danger' | 'warning' | 'info' | 'success';

interface ConfirmModalProps {
  visible: boolean;
  title: string;
  message?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: ConfirmVariant;
  onConfirm: () => void;
  onCancel: () => void;
}

const VARIANT_CONFIG: Record<ConfirmVariant, { icon: string; color: string; bg: string }> = {
  danger:  { icon: 'trash-outline',          color: '#EF4444', bg: 'rgba(239,68,68,0.1)' },
  warning: { icon: 'alert-circle-outline',   color: '#F59E0B', bg: 'rgba(245,158,11,0.1)' },
  info:    { icon: 'information-circle-outline', color: '#3B82F6', bg: 'rgba(59,130,246,0.1)' },
  success: { icon: 'checkmark-circle-outline',   color: '#1EB53A', bg: 'rgba(30,181,58,0.1)' },
};

export default function ConfirmModal({
  visible, title, message,
  confirmLabel = 'Confirm', cancelLabel = 'Cancel',
  variant = 'danger', onConfirm, onCancel,
}: ConfirmModalProps) {
  const { theme } = useSettingsStore();
  const C = palette(theme);
  const cfg = VARIANT_CONFIG[variant];

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onCancel}>
      <Pressable style={S.backdrop} onPress={onCancel} />
      <View style={S.centeredView}>
        <View style={[S.card, { backgroundColor: C.card }]}>
          {/* Icon */}
          <View style={[S.iconWrap, { backgroundColor: cfg.bg }]}>
            <Ionicons name={cfg.icon as any} size={30} color={cfg.color} />
          </View>

          {/* Title + message */}
          <Text style={[S.title, { color: C.text }]}>{title}</Text>
          {!!message && <Text style={[S.message, { color: C.textSub }]}>{message}</Text>}

          {/* Buttons */}
          <View style={S.btnRow}>
            <TouchableOpacity style={[S.btn, S.cancelBtn, { borderColor: C.border }]}
              onPress={onCancel} activeOpacity={0.8}>
              <Ionicons name="close-outline" size={16} color={C.textSub} />
              <Text style={[S.cancelText, { color: C.textSub }]}>{cancelLabel}</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[S.btn, S.confirmBtn, { backgroundColor: cfg.color }]}
              onPress={onConfirm} activeOpacity={0.85}>
              <Ionicons name={cfg.icon as any} size={16} color="#fff" />
              <Text style={S.confirmText}>{confirmLabel}</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const S = StyleSheet.create({
  backdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.55)',
  },
  centeredView: {
    flex: 1, alignItems: 'center', justifyContent: 'center', padding: 32,
  },
  card: {
    width: '100%', borderRadius: 20, padding: 24, alignItems: 'center',
    shadowColor: '#000', shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.2, shadowRadius: 20, elevation: 12,
  },
  iconWrap: {
    width: 64, height: 64, borderRadius: 20,
    alignItems: 'center', justifyContent: 'center', marginBottom: 16,
  },
  title: { fontSize: moderateScale(18), fontWeight: '800', textAlign: 'center', marginBottom: 8 },
  message: { fontSize: moderateScale(14), textAlign: 'center', lineHeight: 21, marginBottom: 24 },
  btnRow: { flexDirection: 'row', gap: 12, width: '100%' },
  btn: {
    flex: 1, height: 48, borderRadius: 12,
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7,
  },
  cancelBtn: { borderWidth: 1.5 },
  confirmBtn: {},
  cancelText: { fontWeight: '600', fontSize: moderateScale(14) },
  confirmText: { color: '#fff', fontWeight: '800', fontSize: moderateScale(14) },
});

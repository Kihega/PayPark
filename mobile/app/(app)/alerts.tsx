/**
 * ParkiPay — Alerts Screen  (v2)
 * Reads local alerts stored by the Lookup screen.
 * Scenarios: duplicate-bill blocked, bill success, bill failed, expired bills.
 */
import { useState, useEffect, useCallback } from 'react';
import {
  ActivityIndicator, FlatList, Platform, RefreshControl,
  SafeAreaView, StatusBar, StyleSheet, Text,
  TouchableOpacity, View,
} from 'react-native';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useSettingsStore, palette } from '@/store/settingsStore';
import { billingService } from '@/services/api';
import { SprintColors } from '@/constants/theme';
import {
  getAlerts, markAllRead, clearAlerts,
  type LocalAlert,
} from '@/services/alertsService';
import { moderateScale } from '@/utils/responsive';

function fmtTime(iso: string) {
  return new Date(iso).toLocaleTimeString('en-TZ', { hour: '2-digit', minute: '2-digit', hour12: true });
}
function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-TZ', { day: '2-digit', month: 'short', year: 'numeric' });
}
function timeSince(iso: string) {
  const m = Math.floor((Date.now() - new Date(iso).getTime()) / 60000);
  if (m < 1) return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

const TYPE_CFG: Record<LocalAlert['type'] | 'EXPIRED', {
  bg: string; border: string; iconBg: string;
  icon: string; color: string; label: string;
}> = {
  BILL_SUCCESS:   { bg:'rgba(30,181,58,0.06)',  border:'#1EB53A', iconBg:'rgba(30,181,58,0.12)',
    icon:'checkmark-circle',          color:'#1EB53A', label:'ISSUED'    },
  BILL_DUPLICATE: { bg:'rgba(245,158,11,0.06)', border:'#F59E0B', iconBg:'rgba(245,158,11,0.12)',
    icon:'alert-circle',              color:'#F59E0B', label:'DUPLICATE' },
  BILL_FAILED:    { bg:'rgba(239,68,68,0.06)',  border:'#EF4444', iconBg:'rgba(239,68,68,0.12)',
    icon:'close-circle',              color:'#EF4444', label:'FAILED'    },
  EXPIRED:        { bg:'rgba(107,114,128,0.06)',border:'#6B7280', iconBg:'rgba(107,114,128,0.1)',
    icon:'time-outline',              color:'#6B7280', label:'EXPIRED'   },
};

interface AnyAlert extends Omit<LocalAlert, 'type'> {
  type: LocalAlert['type'] | 'EXPIRED';
}

export default function AlertsScreen() {
  const { theme } = useSettingsStore();
  const C = palette(theme);
  const S = makeStyles(C);

  const [alerts,     setAlerts]     = useState<AnyAlert[]>([]);
  const [loading,    setLoading]    = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filter,     setFilter]     = useState<'ALL' | LocalAlert['type'] | 'EXPIRED'>('ALL');
  const [unread,     setUnread]     = useState(0);

  const load = useCallback(async () => {
    try {
      // Local stored alerts (lookup events)
      const local: AnyAlert[] = await getAlerts() as AnyAlert[];

      // Expired bills from billing history
      try {
        const res = await billingService.history();
        const expired = (res.data ?? [])
          .filter((b: any) => b.status === 'ACTIVE' && new Date(b.expiresAt) < new Date())
          .map((b: any): AnyAlert => ({
            id:          `exp_${b.id}`,
            type:        'EXPIRED',
            severity:    'warning',
            title:       `Bill Expired — ${b.plateNumber}`,
            description: `Bill ${b.controlNumber} expired unpaid${b.location?.name ? ` at ${b.location.name}` : ''}.`,
            plateNumber: b.plateNumber,
            controlNumber: b.controlNumber,
            location:    b.location?.name,
            issuedAt:    b.generatedAt,
            expiresAt:   b.expiresAt,
            createdAt:   b.expiresAt,
            read:        true,
          }));
        const merged = [...local, ...expired].sort(
          (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
        );
        setAlerts(merged);
        setUnread(merged.filter(a => !a.read).length);
      } catch {
        setAlerts(local);
        setUnread(local.filter(a => !a.read).length);
      }
    } finally { setLoading(false); setRefreshing(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleMarkAllRead = async () => {
    await markAllRead();
    setAlerts(prev => prev.map(a => ({ ...a, read: true })));
    setUnread(0);
  };

  const handleClearAll = async () => {
    await clearAlerts();
    setAlerts(prev => prev.filter(a => a.type === 'EXPIRED'));
    setUnread(0);
  };

  const filtered = filter === 'ALL' ? alerts : alerts.filter(a => a.type === filter);
  const topOffset = Platform.OS === 'android' ? (StatusBar.currentHeight ?? 24) : 0;

  return (
    <SafeAreaView style={[S.root, { backgroundColor: C.bg, paddingTop: topOffset }]}>
      {/* Header */}
      <View style={[S.header, { backgroundColor: C.headerBg }]}>
        <TouchableOpacity onPress={() => router.back()} style={S.iconBtn}>
          <Ionicons name="arrow-back" size={22} color="#fff" />
        </TouchableOpacity>
        <View style={{ alignItems: 'center' }}>
          <Text style={S.headerTitle}>Alerts</Text>
          {unread > 0 && (
            <View style={S.unreadBadge}>
              <Text style={S.unreadText}>{unread} unread</Text>
            </View>
          )}
        </View>
        <TouchableOpacity onPress={() => { setRefreshing(true); load(); }} style={S.iconBtn}>
          <Ionicons name="refresh-outline" size={20} color="#fff" />
        </TouchableOpacity>
      </View>

      {/* Action bar */}
      <View style={[S.actionBar, { backgroundColor: C.card, borderBottomColor: C.border }]}>
        {unread > 0 && (
          <TouchableOpacity style={S.actionBtn} onPress={handleMarkAllRead}>
            <Ionicons name="checkmark-done-outline" size={16} color={SprintColors.green} />
            <Text style={[S.actionBtnText, { color: SprintColors.green }]}>Mark all read</Text>
          </TouchableOpacity>
        )}
        <TouchableOpacity style={S.actionBtn} onPress={handleClearAll}>
          <Ionicons name="trash-outline" size={16} color="#6B7280" />
          <Text style={[S.actionBtnText, { color: '#6B7280' }]}>Clear all</Text>
        </TouchableOpacity>
      </View>

      {/* Filter chips */}
      <View style={S.filterRow}>
        {(['ALL','BILL_SUCCESS','BILL_DUPLICATE','BILL_FAILED','EXPIRED'] as const).map(f => {
          const cfg = f === 'ALL' ? null : TYPE_CFG[f];
          const isActive = filter === f;
          return (
            <TouchableOpacity key={f}
              style={[S.filterChip,
                isActive ? { backgroundColor: cfg?.color ?? SprintColors.green,
                  borderColor: cfg?.color ?? SprintColors.green }
                : { borderColor: cfg?.color ?? C.border }]}
              onPress={() => setFilter(f)}>
              <Text style={[S.filterText, { color: isActive ? '#fff' : (cfg?.color ?? C.textSub) }]}>
                {f === 'ALL' ? 'All' : (cfg?.label ?? f)}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>

      {loading ? (
        <ActivityIndicator color={SprintColors.green} size="large" style={{ flex: 1 }} />
      ) : filtered.length === 0 ? (
        <View style={S.empty}>
          <MaterialCommunityIcons name="bell-check-outline" size={56} color={C.textMuted} />
          <Text style={[S.emptyTitle, { color: C.textMuted }]}>
            {filter === 'ALL' ? 'No Alerts Yet' : `No ${TYPE_CFG[filter as keyof typeof TYPE_CFG]?.label ?? filter} alerts`}
          </Text>
          <Text style={[S.emptySub, { color: C.textMuted }]}>
            {filter === 'ALL'
              ? 'Alerts appear here when you issue bills or encounter duplicate plate lookups.'
              : 'Switch to "All" to see all alerts.'}
          </Text>
        </View>
      ) : (
        <FlatList
          data={filtered}
          keyExtractor={a => a.id}
          contentContainerStyle={{ padding: 14, paddingBottom: 32 }}
          refreshControl={<RefreshControl refreshing={refreshing}
            onRefresh={() => { setRefreshing(true); load(); }}
            tintColor={SprintColors.green} />}
          renderItem={({ item: a }) => {
            const cfg = TYPE_CFG[a.type];
            return (
              <View style={[S.card, { backgroundColor: C.card, borderLeftColor: cfg.border },
                !a.read && S.cardUnread]}>
                {!a.read && <View style={[S.unreadDot, { backgroundColor: cfg.color }]} />}

                <View style={[S.iconBox, { backgroundColor: cfg.iconBg }]}>
                  <Ionicons name={cfg.icon as any} size={24} color={cfg.color} />
                </View>

                <View style={{ flex: 1 }}>
                  {/* Top row */}
                  <View style={S.cardTop}>
                    <View style={[S.typeBadge, { backgroundColor: cfg.iconBg }]}>
                      <Text style={[S.typeBadgeText, { color: cfg.color }]}>{cfg.label}</Text>
                    </View>
                    <Text style={[S.timeText, { color: C.textMuted }]}>{timeSince(a.createdAt)}</Text>
                  </View>

                  {/* Title */}
                  <Text style={[S.cardTitle, { color: C.text }]}>{a.title}</Text>

                  {/* Description */}
                  <Text style={[S.cardDesc, { color: C.textSub }]}>{a.description}</Text>

                  {/* Detail rows — only for bill events */}
                  {(a.controlNumber || a.issuedAt || a.expiresAt) && (
                    <View style={[S.detailBox, { backgroundColor: cfg.bg, borderColor: cfg.border }]}>
                      {a.controlNumber && (
                        <View style={S.detailRow}>
                          <Ionicons name="receipt-outline" size={12} color={cfg.color} />
                          <Text style={[S.detailLabel, { color: C.textSub }]}>Control No.</Text>
                          <Text style={[S.detailVal, { color: C.text }]}>{a.controlNumber}</Text>
                        </View>
                      )}
                      {a.issuedAt && (
                        <View style={S.detailRow}>
                          <Ionicons name="time-outline" size={12} color={cfg.color} />
                          <Text style={[S.detailLabel, { color: C.textSub }]}>Issued</Text>
                          <Text style={[S.detailVal, { color: C.text }]}>
                            {fmtDate(a.issuedAt)} {fmtTime(a.issuedAt)}
                          </Text>
                        </View>
                      )}
                      {a.expiresAt && (
                        <View style={S.detailRow}>
                          <Ionicons name="alarm-outline" size={12} color={cfg.color} />
                          <Text style={[S.detailLabel, { color: C.textSub }]}>Expires</Text>
                          <Text style={[S.detailVal, { color: C.text }]}>
                            {fmtDate(a.expiresAt)} {fmtTime(a.expiresAt)}
                          </Text>
                        </View>
                      )}
                      {a.type === 'BILL_DUPLICATE' && a.expiresAt && (
                        <View style={[S.allowRow, { borderColor: cfg.border }]}>
                          <Ionicons name="information-circle-outline" size={13} color={cfg.color} />
                          <Text style={[S.allowText, { color: cfg.color }]}>
                            New bill allowed after: {fmtDate(a.expiresAt)} {fmtTime(a.expiresAt)}
                          </Text>
                        </View>
                      )}
                    </View>
                  )}
                </View>
              </View>
            );
          }}
        />
      )}
    </SafeAreaView>
  );
}

function makeStyles(C: ReturnType<typeof palette>) {
  return StyleSheet.create({
    root: { flex: 1 },
    header: { flexDirection: 'row', alignItems: 'center',
      justifyContent: 'space-between', paddingHorizontal: 16, paddingVertical: 14 },
    iconBtn: { width: 38, height: 38, borderRadius: 10, alignItems: 'center',
      justifyContent: 'center', backgroundColor: 'rgba(255,255,255,0.1)' },
    headerTitle: { fontSize: moderateScale(17), fontWeight: '800', color: '#fff' },
    unreadBadge: { backgroundColor: SprintColors.yellow, borderRadius: 10,
      paddingHorizontal: 8, paddingVertical: 2, marginTop: 2 },
    unreadText: { fontSize: moderateScale(10), fontWeight: '800', color: '#1A1A1A' },
    actionBar: { flexDirection: 'row', justifyContent: 'flex-end', gap: 4,
      paddingHorizontal: 12, paddingVertical: 8, borderBottomWidth: 1 },
    actionBtn: { flexDirection: 'row', alignItems: 'center', gap: 5,
      paddingHorizontal: 12, paddingVertical: 7, borderRadius: 20 },
    actionBtnText: { fontSize: moderateScale(12), fontWeight: '700' },
    filterRow: { flexDirection: 'row', gap: 7, paddingHorizontal: 14,
      paddingVertical: 10, flexWrap: 'wrap' },
    filterChip: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20,
      borderWidth: 1.5 },
    filterText: { fontSize: moderateScale(11), fontWeight: '700' },
    empty: { flex: 1, alignItems: 'center', justifyContent: 'center',
      gap: 10, padding: 32, marginTop: 20 },
    emptyTitle: { fontSize: moderateScale(17), fontWeight: '700', textAlign: 'center' },
    emptySub: { fontSize: moderateScale(13), textAlign: 'center', lineHeight: 20 },
    card: { flexDirection: 'row', gap: 12, borderRadius: 14, padding: 14,
      marginBottom: 10, borderLeftWidth: 4, position: 'relative',
      shadowColor: '#000', shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.07, shadowRadius: 6, elevation: 3 },
    cardUnread: { shadowOpacity: 0.12, elevation: 5 },
    unreadDot: { position: 'absolute', top: 12, right: 12,
      width: 8, height: 8, borderRadius: 4 },
    iconBox: { width: 48, height: 48, borderRadius: 14,
      alignItems: 'center', justifyContent: 'center', flexShrink: 0 },
    cardTop: { flexDirection: 'row', alignItems: 'center',
      justifyContent: 'space-between', marginBottom: 5 },
    typeBadge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 8 },
    typeBadgeText: { fontSize: moderateScale(9), fontWeight: '900', letterSpacing: 1, textTransform: 'uppercase' },
    timeText: { fontSize: moderateScale(11) },
    cardTitle: { fontSize: moderateScale(14), fontWeight: '800', marginBottom: 4 },
    cardDesc: { fontSize: moderateScale(12), lineHeight: 18, marginBottom: 8 },
    detailBox: { borderRadius: 10, borderWidth: 1, padding: 10, gap: 6 },
    detailRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
    detailLabel: { width: 75, fontSize: moderateScale(11), fontWeight: '600' },
    detailVal: { flex: 1, fontSize: moderateScale(11), fontWeight: '700' },
    allowRow: { flexDirection: 'row', alignItems: 'center', gap: 6,
      paddingTop: 6, borderTopWidth: 1, marginTop: 2 },
    allowText: { flex: 1, fontSize: moderateScale(11), fontWeight: '700', lineHeight: 16 },
  });
}

/**
 * ParkiPay — History Screen
 * Shows all bills issued by the logged-in officer, grouped by date.
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
import { moderateScale } from '@/utils/responsive';

interface Bill {
  id: number;
  plateNumber: string;
  controlNumber: string;
  amountDue: string | number;
  generatedAt: string;
  expiresAt: string;
  status: string;
  location?: { name?: string } | null;
  vehicle?: { ownerName?: string; category?: string } | null;
}

function fmtDate(iso: string) {
  const d = new Date(iso);
  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(today.getDate() - 1);

  if (d.toDateString() === today.toDateString()) return 'Today';
  if (d.toDateString() === yesterday.toDateString()) return 'Yesterday';
  return d.toLocaleDateString('en-TZ', { weekday: 'short', day: 'numeric', month: 'short' });
}

function fmtTime(iso: string) {
  return new Date(iso).toLocaleTimeString('en-TZ', { hour: '2-digit', minute: '2-digit', hour12: true });
}

function groupByDate(bills: Bill[]): { date: string; data: Bill[] }[] {
  const map: Record<string, Bill[]> = {};
  for (const b of bills) {
    const key = new Date(b.generatedAt).toDateString();
    if (!map[key]) map[key] = [];
    map[key].push(b);
  }
  return Object.entries(map).map(([date, data]) => ({ date: fmtDate(new Date(date).toISOString()), data }));
}

const STATUS_STYLES: Record<string, { bg: string; color: string; icon: string }> = {
  PAID:     { bg: 'rgba(30,181,58,0.12)',  color: '#1EB53A', icon: 'checkmark-circle-outline' },
  PENDING:  { bg: 'rgba(245,158,11,0.15)', color: '#F59E0B', icon: 'time-outline' },
  EXPIRED:  { bg: 'rgba(107,114,128,0.15)',color: '#6B7280', icon: 'close-circle-outline' },
  ACTIVE:   { bg: 'rgba(30,181,58,0.12)',  color: '#1EB53A', icon: 'radio-button-on-outline' },
};

export default function HistoryScreen() {
  const { theme } = useSettingsStore();
  const C = palette(theme);
  const S = makeStyles(C);

  const [bills,     setBills]     = useState<Bill[]>([]);
  const [loading,   setLoading]   = useState(true);
  const [refreshing,setRefreshing]= useState(false);
  const [filter,    setFilter]    = useState<'ALL' | 'PAID' | 'PENDING' | 'ACTIVE'>('ALL');

  const load = useCallback(async () => {
    try {
      const res = await billingService.history();
      setBills(res.data);
    } catch { /* silent */ }
    finally { setLoading(false); setRefreshing(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const filtered = filter === 'ALL' ? bills : bills.filter(b => b.status === filter);
  const grouped  = groupByDate(filtered);

  const totalAmount = bills.reduce((s, b) => s + Number(b.amountDue), 0);
  const paidCount   = bills.filter(b => b.status === 'PAID').length;

  const topOffset = Platform.OS === 'android' ? (StatusBar.currentHeight ?? 24) : 0;

  return (
    <SafeAreaView style={[S.root, { backgroundColor: C.bg, paddingTop: topOffset }]}>
      {/* Header */}
      <View style={[S.header, { backgroundColor: C.headerBg }]}>
        <TouchableOpacity onPress={() => router.back()} style={S.backBtn}>
          <Ionicons name="arrow-back" size={22} color="#fff" />
        </TouchableOpacity>
        <View>
          <Text style={S.headerTitle}>Bill History</Text>
          <Text style={S.headerSub}>{bills.length} bills total</Text>
        </View>
        <View style={{ width: 38 }} />
      </View>

      {/* Summary row */}
      <View style={[S.summaryRow, { backgroundColor: C.card }]}>
        {[
          { label: 'Total Bills', value: String(bills.length), icon: 'document-text-outline' },
          { label: 'Paid',        value: String(paidCount),    icon: 'checkmark-circle-outline' },
          { label: 'Revenue',     value: `TZS ${(totalAmount/1000).toFixed(0)}k`, icon: 'cash-outline' },
        ].map(s => (
          <View key={s.label} style={S.summaryItem}>
            <Ionicons name={s.icon as any} size={18} color={C.accent} />
            <Text style={[S.summaryVal, { color: C.text }]}>{s.value}</Text>
            <Text style={[S.summaryLabel, { color: C.textSub }]}>{s.label}</Text>
          </View>
        ))}
      </View>

      {/* Filter chips */}
      <View style={S.filterRow}>
        {(['ALL','ACTIVE','PAID','PENDING'] as const).map(f => (
          <TouchableOpacity key={f}
            style={[S.filterChip, filter === f && S.filterActive]}
            onPress={() => setFilter(f)}>
            <Text style={[S.filterText, filter === f && { color: '#fff' }]}>{f}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading ? (
        <ActivityIndicator color={SprintColors.green} size="large" style={{ flex: 1 }} />
      ) : filtered.length === 0 ? (
        <View style={S.emptyWrap}>
          <MaterialCommunityIcons name="file-document-outline" size={52} color={C.textMuted} />
          <Text style={[S.emptyTitle, { color: C.textMuted }]}>No Bills Found</Text>
          <Text style={[S.emptySub, { color: C.textMuted }]}>
            {filter === 'ALL' ? 'No bills have been issued today.' : `No ${filter.toLowerCase()} bills.`}
          </Text>
        </View>
      ) : (
        <FlatList
          data={grouped}
          keyExtractor={g => g.date}
          contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
          refreshControl={<RefreshControl refreshing={refreshing}
            onRefresh={() => { setRefreshing(true); load(); }}
            tintColor={SprintColors.green} />}
          renderItem={({ item: group }) => (
            <View>
              {/* Date header */}
              <View style={S.dateHeader}>
                <View style={[S.dateLine, { backgroundColor: C.border }]} />
                <Text style={[S.dateLabel, { color: C.textSub }]}>{group.date}</Text>
                <View style={[S.dateLine, { backgroundColor: C.border }]} />
              </View>

              {group.data.map(bill => {
                const st = STATUS_STYLES[bill.status] ?? STATUS_STYLES.PENDING;
                return (
                  <View key={bill.id} style={[S.card, { backgroundColor: C.card }]}>
                    {/* Left accent bar */}
                    <View style={[S.accentBar, { backgroundColor: st.color }]} />

                    <View style={S.cardInner}>
                      {/* Top row */}
                      <View style={S.cardTop}>
                        <View style={S.plateChip}>
                          <Text style={S.plateChipText}>{bill.plateNumber}</Text>
                        </View>
                        <View style={[S.statusBadge, { backgroundColor: st.bg }]}>
                          <Ionicons name={st.icon as any} size={12} color={st.color} />
                          <Text style={[S.statusText, { color: st.color }]}>{bill.status}</Text>
                        </View>
                      </View>

                      {/* Info rows */}
                      <View style={S.infoRow}>
                        <Ionicons name="receipt-outline" size={13} color={C.textMuted} />
                        <Text style={[S.infoText, { color: C.textSub }]}>
                          CN: {bill.controlNumber}
                        </Text>
                      </View>

                      {bill.location?.name && (
                        <View style={S.infoRow}>
                          <Ionicons name="location-outline" size={13} color={C.textMuted} />
                          <Text style={[S.infoText, { color: C.textSub }]}>{bill.location.name}</Text>
                        </View>
                      )}

                      {bill.vehicle?.ownerName && (
                        <View style={S.infoRow}>
                          <Ionicons name="person-outline" size={13} color={C.textMuted} />
                          <Text style={[S.infoText, { color: C.textSub }]}>{bill.vehicle.ownerName}</Text>
                        </View>
                      )}

                      {/* Bottom row */}
                      <View style={S.cardBottom}>
                        <Text style={[S.amount, { color: C.text }]}>
                          TZS {Number(bill.amountDue).toLocaleString()}
                        </Text>
                        <Text style={[S.time, { color: C.textMuted }]}>
                          {fmtTime(bill.generatedAt)}
                        </Text>
                      </View>
                    </View>
                  </View>
                );
              })}
            </View>
          )}
        />
      )}
    </SafeAreaView>
  );
}

function makeStyles(C: ReturnType<typeof palette>) {
  return StyleSheet.create({
    root: { flex: 1 },
    header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
      paddingHorizontal: 16, paddingVertical: 14 },
    backBtn: { width: 38, height: 38, borderRadius: 10, alignItems: 'center',
      justifyContent: 'center', backgroundColor: 'rgba(255,255,255,0.1)' },
    headerTitle: { fontSize: moderateScale(17), fontWeight: '800', color: '#fff', textAlign: 'center' },
    headerSub: { fontSize: moderateScale(11), color: 'rgba(255,255,255,0.6)', textAlign: 'center' },
    summaryRow: { flexDirection: 'row', marginHorizontal: 16, marginTop: 12, marginBottom: 4,
      borderRadius: 14, padding: 14, shadowColor: '#000', shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.06, shadowRadius: 6, elevation: 3 },
    summaryItem: { flex: 1, alignItems: 'center', gap: 4 },
    summaryVal: { fontSize: moderateScale(16), fontWeight: '800' },
    summaryLabel: { fontSize: moderateScale(10), fontWeight: '600' },
    filterRow: { flexDirection: 'row', gap: 8, paddingHorizontal: 16, paddingVertical: 12 },
    filterChip: { paddingHorizontal: 14, paddingVertical: 7, borderRadius: 20,
      backgroundColor: 'rgba(30,181,58,0.08)', borderWidth: 1.5,
      borderColor: 'rgba(30,181,58,0.3)' },
    filterActive: { backgroundColor: SprintColors.green, borderColor: SprintColors.green },
    filterText: { fontSize: moderateScale(11), fontWeight: '700', color: SprintColors.green },
    emptyWrap: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 10, padding: 32 },
    emptyTitle: { fontSize: moderateScale(16), fontWeight: '700' },
    emptySub: { fontSize: moderateScale(13), textAlign: 'center', lineHeight: 20 },
    dateHeader: { flexDirection: 'row', alignItems: 'center', gap: 10, marginVertical: 10 },
    dateLine: { flex: 1, height: 1 },
    dateLabel: { fontSize: moderateScale(12), fontWeight: '700' },
    card: { borderRadius: 14, marginBottom: 10, flexDirection: 'row', overflow: 'hidden',
      shadowColor: '#000', shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.06, shadowRadius: 5, elevation: 3 },
    accentBar: { width: 4 },
    cardInner: { flex: 1, padding: 14 },
    cardTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
      marginBottom: 8 },
    plateChip: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 8,
      borderWidth: 1.5, borderColor: '#1A1A1A', backgroundColor: '#fff' },
    plateChipText: { fontSize: moderateScale(14), fontWeight: '900', letterSpacing: 2, color: '#1A1A1A' },
    statusBadge: { flexDirection: 'row', alignItems: 'center', gap: 5,
      paddingHorizontal: 10, paddingVertical: 4, borderRadius: 20 },
    statusText: { fontSize: moderateScale(10), fontWeight: '800' },
    infoRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 3 },
    infoText: { fontSize: moderateScale(12) },
    cardBottom: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
      marginTop: 8, paddingTop: 8, borderTopWidth: 1, borderTopColor: 'rgba(0,0,0,0.05)' },
    amount: { fontSize: moderateScale(15), fontWeight: '800' },
    time: { fontSize: moderateScale(12) },
  });
}

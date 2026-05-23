/**
 * ParkiPay — Officer Dashboard  (v3 — real data)
 */
import { useState, useRef, useEffect, useCallback } from 'react';
import {
  Alert, Animated, Dimensions, Platform, SafeAreaView, ScrollView,
  StyleSheet, StatusBar, Text, TouchableOpacity, View, Modal, Pressable,
  ActivityIndicator, RefreshControl,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useAuthStore } from '@/store/authStore';
import { useSettingsStore, palette } from '@/store/settingsStore';
import { t } from '@/constants/i18n';
import { authService, billingService } from '@/services/api';
import { SprintColors } from '@/constants/theme';

const { width: W } = Dimensions.get('window');
const SIDEBAR_W = W * 0.72;

interface Bill {
  id: number;
  plateNumber: string;
  controlNumber: string;
  amountDue: string | number;
  generatedAt: string;
  status: string;
  vehicle?: { ownerName?: string } | null;
}

function formatAmount(amount: number): string {
  if (amount >= 1_000_000) return `${(amount / 1_000_000).toFixed(1)}M`;
  if (amount >= 1_000)     return `${Math.round(amount / 1_000)}k`;
  return String(amount);
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString('en-TZ', { hour: '2-digit', minute: '2-digit' });
}

/* ─── Sidebar Settings Menu ─────────────────────────────────────── */
function SidebarSettingsMenu({ C, dynStyles, language, theme, setLanguage, setTheme, tr, onLogout }: any) {
  const [langOpen, setLangOpen] = useState(false);
  const [modeOpen, setModeOpen] = useState(false);

  return (
    <>
      {/* Language */}
      <TouchableOpacity style={dynStyles.sbMenuRow} onPress={() => { setLangOpen(v => !v); setModeOpen(false); }}>
        <Ionicons name="language-outline" size={17} color="#9CA3AF" />
        <Text style={dynStyles.sbMenuLabel}>{tr('language')}</Text>
        <Ionicons name={langOpen ? 'chevron-up' : 'chevron-down'} size={15} color="#9CA3AF" />
      </TouchableOpacity>
      {langOpen && (
        <View style={dynStyles.sbDropdown}>
          {([['en','🇬🇧 English (US)'],['sw','🇹🇿 Kiswahili']] as const).map(([code, label]) => (
            <TouchableOpacity key={code} style={[dynStyles.sbDropdownItem,
              language === code && { backgroundColor: 'rgba(30,181,58,0.15)' }]}
              onPress={() => { setLanguage(code); setLangOpen(false); }}>
              <Text style={[dynStyles.sbDropdownText,
                { color: language === code ? '#1EB53A' : '#D1D5DB' }]}>{label}</Text>
              {language === code && <Ionicons name="checkmark" size={15} color="#1EB53A" />}
            </TouchableOpacity>
          ))}
        </View>
      )}

      {/* Theme / Mode */}
      <TouchableOpacity style={dynStyles.sbMenuRow} onPress={() => { setModeOpen(v => !v); setLangOpen(false); }}>
        <Ionicons name={theme === 'dark' ? 'moon-outline' : 'sunny-outline'} size={17} color="#9CA3AF" />
        <Text style={dynStyles.sbMenuLabel}>Mode</Text>
        <Ionicons name={modeOpen ? 'chevron-up' : 'chevron-down'} size={15} color="#9CA3AF" />
      </TouchableOpacity>
      {modeOpen && (
        <View style={dynStyles.sbDropdown}>
          {([['light','☀️ Light'],['dark','🌙 Dark']] as const).map(([mode, label]) => (
            <TouchableOpacity key={mode} style={[dynStyles.sbDropdownItem,
              theme === mode && { backgroundColor: 'rgba(30,181,58,0.15)' }]}
              onPress={() => { setTheme(mode); setModeOpen(false); }}>
              <Text style={[dynStyles.sbDropdownText,
                { color: theme === mode ? '#1EB53A' : '#D1D5DB' }]}>{label}</Text>
              {theme === mode && <Ionicons name="checkmark" size={15} color="#1EB53A" />}
            </TouchableOpacity>
          ))}
        </View>
      )}

      <View style={dynStyles.sbDivider} />
      <TouchableOpacity style={dynStyles.logoutBtn} onPress={onLogout}>
        <Ionicons name="log-out-outline" size={18} color="#EF4444" />
        <Text style={dynStyles.logoutText}>{tr('logout')}</Text>
      </TouchableOpacity>
    </>
  );
}

export default function HomeScreen() {
  const { officer, clearAuth, refreshToken } = useAuthStore();
  const { language, theme, setLanguage, setTheme } = useSettingsStore();
  const C = palette(theme);
  const tr = (k: string) => t(language, k);

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [onDuty, setOnDuty]           = useState(true);
  const [bills,  setBills]            = useState<Bill[]>([]);
  const [totalBills,  setTotalBills]  = useState(0);
  const [totalAmount, setTotalAmount] = useState(0);
  const [loading,  setLoading]        = useState(true);
  const [refreshing, setRefreshing]   = useState(false);
  const slideX = useRef(new Animated.Value(-SIDEBAR_W)).current;

  const openSidebar = () => {
    setSidebarOpen(true);
    Animated.spring(slideX, { toValue: 0, useNativeDriver: true, bounciness: 0 }).start();
  };
  const closeSidebar = () => {
    Animated.timing(slideX, { toValue: -SIDEBAR_W, duration: 220, useNativeDriver: true }).start(
      () => setSidebarOpen(false)
    );
  };

  const loadData = useCallback(async () => {
    try {
      const [histRes, statsRes] = await Promise.allSettled([
        billingService.history(),
        billingService.stats(),
      ]);

      if (histRes.status === 'fulfilled') {
        setBills(histRes.value.data.slice(0, 5));
      }
      if (statsRes.status === 'fulfilled') {
        setTotalBills(statsRes.value.data.totalBills ?? 0);
        setTotalAmount(statsRes.value.data.totalAmount ?? 0);
      }
    } catch {
      // silent — show whatever we have
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const onRefresh = () => { setRefreshing(true); loadData(); };

  const handleLogout = () => {
    closeSidebar();
    Alert.alert(tr('logout'), tr('logoutConfirm'), [
      { text: tr('no'), style: 'cancel' },
      { text: tr('yes'), style: 'destructive', onPress: async () => {
        try { if (refreshToken) await authService.logout(refreshToken); } catch {}
        await clearAuth();
        router.replace('/(auth)/login');
      }},
    ]);
  };

  if (!officer) return null;

  const today = new Date().toLocaleDateString(language === 'sw' ? 'sw-TZ' : 'en-TZ', {
    weekday: 'long', month: 'long', day: 'numeric',
  });

  const dynStyles = makeStyles(C);

  const topOffset = Platform.OS === 'android' ? (StatusBar.currentHeight ?? 24) : 0;

  return (
    <SafeAreaView style={[dynStyles.root, { paddingTop: topOffset }]}>

      {/* ── Sidebar overlay ────────────────────────────────────────────── */}
      {sidebarOpen && (
        <Modal transparent animationType="none" visible={sidebarOpen} onRequestClose={closeSidebar}>
          <Pressable style={dynStyles.overlay} onPress={closeSidebar} />
          <Animated.View style={[dynStyles.sidebar, { transform:[{ translateX: slideX }] }]}>
            <View style={dynStyles.sbHeader}>
              <Text style={dynStyles.sbHeaderText}>⚙ {tr('settings')}</Text>
              <TouchableOpacity onPress={closeSidebar}>
                <Ionicons name="close" size={22} color={C.sidebarText} />
              </TouchableOpacity>
            </View>

            <SidebarSettingsMenu C={C} dynStyles={dynStyles}
              language={language} theme={theme}
              setLanguage={setLanguage} setTheme={setTheme}
              tr={tr} onLogout={handleLogout} />
          </Animated.View>
        </Modal>
      )}

      {/* ── Top bar ────────────────────────────────────────────────────── */}
      <View style={[dynStyles.topBar, { backgroundColor: C.headerBg }]}>
        <TouchableOpacity onPress={openSidebar} style={dynStyles.iconBtn}>
          <Ionicons name="menu" size={24} color={C.headerText} />
        </TouchableOpacity>
        <View style={{ flexDirection: 'row' }}>
          <Text style={[dynStyles.topLogo, { color: SprintColors.green }]}>Parki</Text>
          <Text style={[dynStyles.topLogo, { color: SprintColors.yellow }]}>Pay</Text>
        </View>
        <TouchableOpacity style={dynStyles.iconBtn} onPress={loadData}>
          <Ionicons name="refresh-outline" size={22} color={C.headerText} />
        </TouchableOpacity>
      </View>

      <ScrollView
        contentContainerStyle={[dynStyles.body, { backgroundColor: C.bg }]}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh}
          tintColor={SprintColors.green} />}
      >
        {/* ── Active Session card ────────────────────────────────────── */}
        <LinearGradient colors={['#1EB53A','#158A2A']}
          start={{ x:0, y:0 }} end={{ x:1, y:1 }} style={dynStyles.sessionCard}>
          <View style={dynStyles.sessionTop}>
            <View style={{ flex: 1 }}>
              <Text style={dynStyles.sessionLabel}>{tr('activeSession')}</Text>
              <Text style={dynStyles.sessionName}>{officer.fullName}</Text>
              <Text style={dynStyles.sessionZone}>
                <Ionicons name="location-outline" size={13} color="#cfffdf" />
                {'  '}{officer.locationName ?? 'Unassigned'}
              </Text>
            </View>
            <TouchableOpacity onPress={() => setOnDuty(v => !v)}
              style={[dynStyles.dutyBadge, !onDuty && dynStyles.dutyBadgeOff]}>
              <View style={[dynStyles.dutyDot, !onDuty && { backgroundColor: '#9CA3AF' }]} />
              <Text style={dynStyles.dutyText}>{onDuty ? tr('onDuty') : tr('offDuty')}</Text>
            </TouchableOpacity>
          </View>
          <Text style={dynStyles.sessionDate}>{today}</Text>
        </LinearGradient>

        {/* ── Stats row ─────────────────────────────────────────────── */}
        <View style={dynStyles.statsRow}>
          <View style={[dynStyles.statCard, { backgroundColor: C.statCard }]}>
            <MaterialCommunityIcons name="file-document-outline" size={22} color={C.accent} />
            {loading
              ? <ActivityIndicator size="small" color={C.accent} />
              : <Text style={[dynStyles.statVal, { color: C.text }]}>{totalBills}</Text>
            }
            <Text style={[dynStyles.statLabel, { color: C.textSub }]}>{tr('totalBills')}</Text>
          </View>
          <View style={[dynStyles.statCard, { backgroundColor: C.statCard }]}>
            <MaterialCommunityIcons name="cash-multiple" size={22} color={C.accent} />
            {loading
              ? <ActivityIndicator size="small" color={C.accent} />
              : <Text style={[dynStyles.statVal, { color: C.text }]}>{formatAmount(totalAmount)}</Text>
            }
            <Text style={[dynStyles.statLabel, { color: C.textSub }]}>{tr('amountCollected')}</Text>
          </View>
        </View>

        {/* ── CTA ───────────────────────────────────────────────────── */}
        <TouchableOpacity style={dynStyles.ctaBtn} activeOpacity={0.85}
          onPress={() => router.push('/(app)/lookup')}>
          <Ionicons name="search" size={20} color="#1A1A1A" />
          <Text style={dynStyles.ctaText}>{tr('newLookup')}</Text>
        </TouchableOpacity>

        {/* ── Recent Bills ──────────────────────────────────────────── */}
        <View style={dynStyles.sectionHeader}>
          <Text style={[dynStyles.sectionTitle, { color: C.text }]}>{tr('recentBills')}</Text>
          <TouchableOpacity onPress={() => router.push('/(app)/history')}>
            <Text style={[dynStyles.viewAll, { color: C.accent }]}>{tr('viewAll')}</Text>
          </TouchableOpacity>
        </View>

        {loading ? (
          <View style={{ padding: 32, alignItems: 'center' }}>
            <ActivityIndicator color={SprintColors.green} size="large" />
          </View>
        ) : bills.length === 0 ? (
          <View style={[dynStyles.emptyCard, { backgroundColor: C.card }]}>
            <MaterialCommunityIcons name="car-off" size={36} color={C.textMuted} />
            <Text style={[dynStyles.emptyText, { color: C.textMuted }]}>{tr('noBills')}</Text>
          </View>
        ) : (
          bills.map(bill => (
            <View key={bill.id} style={[dynStyles.billCard, { backgroundColor: C.card }]}>
              <View style={dynStyles.billIcon}>
                <MaterialCommunityIcons name="car-outline" size={22} color={C.accent} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={[dynStyles.billPlate, { color: C.text }]}>{bill.plateNumber}</Text>
                <Text style={[dynStyles.billMeta, { color: C.textSub }]}>
                  {Number(bill.amountDue).toLocaleString()} {tr('tzs')} · {formatTime(bill.generatedAt)}
                </Text>
              </View>
              <View style={[dynStyles.statusBadge,
                bill.status === 'PAID' ? dynStyles.badgePaid : dynStyles.badgePending]}>
                <Text style={dynStyles.statusText}>
                  {bill.status === 'PAID' ? tr('paid') : tr('pending')}
                </Text>
              </View>
            </View>
          ))
        )}

        <View style={{ height: 24 }} />
      </ScrollView>

      {/* ── Bottom Tab Bar ────────────────────────────────────────────── */}
      <View style={[dynStyles.tabBar, { backgroundColor: C.navBg, borderTopColor: C.navBorder }]}>
        {[
          { icon: 'grid-outline',         label: tr('dashboard'), active: true,  onPress: () => {}               },
          { icon: 'search-outline',        label: tr('lookup'),    active: false, onPress: () => router.push('/(app)/lookup') },
          { icon: 'time-outline',          label: tr('history'),   active: false, onPress: () => router.push('/(app)/history') },
          { icon: 'alert-circle-outline',  label: tr('alerts'),    active: false, onPress: () => router.push('/(app)/alerts') },
        ].map((tab, i) => (
          <TouchableOpacity key={i} style={dynStyles.tabItem} onPress={tab.onPress}>
            <Ionicons name={tab.icon as any} size={22}
              color={tab.active ? C.navActive : C.textMuted} />
            <Text style={[dynStyles.tabLabel,
              { color: tab.active ? C.navActive : C.textMuted }]}>{tab.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </SafeAreaView>
  );
}

function makeStyles(C: ReturnType<typeof palette>) {
  return StyleSheet.create({
    root:{ flex:1 },
    overlay:{ ...StyleSheet.absoluteFillObject, backgroundColor:'rgba(0,0,0,0.5)' },
    sidebar:{
      position:'absolute', left:0, top:0, bottom:0, width: W * 0.72,
      backgroundColor: C.sidebarBg, paddingTop:56, paddingHorizontal:20, zIndex:99,
    },
    sbHeader:{ flexDirection:'row', justifyContent:'space-between', alignItems:'center', marginBottom:28 },
    sbHeaderText:{ fontSize:17, fontWeight:'700', color: C.sidebarText },
    sbSection:{ fontSize:11, fontWeight:'700', color:'#6B7280', letterSpacing:1.2, textTransform:'uppercase', marginBottom:10, marginTop:4 },
    toggleRow:{ flexDirection:'row', gap:8, marginBottom:20 },
    toggleBtn:{ flex:1, paddingVertical:9, borderRadius:8, alignItems:'center', justifyContent:'center', flexDirection:'row', gap:5, backgroundColor:'rgba(255,255,255,0.08)' },
    toggleActive:{ backgroundColor: SprintColors.green },
    toggleText:{ fontSize:13, color: C.sidebarText, fontWeight:'600' },
    toggleActiveText:{ color:'#fff' },
    sbDivider:{ height:1, backgroundColor:'rgba(255,255,255,0.1)', marginVertical:16 },
    logoutBtn:{ flexDirection:'row', alignItems:'center', gap:10, paddingVertical:12, paddingHorizontal:14, borderRadius:10, backgroundColor:'rgba(239,68,68,0.12)' },
    logoutText:{ color:'#EF4444', fontWeight:'700', fontSize:15 },
    sbMenuRow:{ flexDirection:'row', alignItems:'center', gap:10, paddingVertical:12, paddingHorizontal:4 },
    sbMenuLabel:{ flex:1, fontSize:14, color:'#D1D5DB', fontWeight:'600' },
    sbDropdown:{ borderRadius:10, overflow:'hidden', marginBottom:6, backgroundColor:'rgba(255,255,255,0.05)' },
    sbDropdownItem:{ flexDirection:'row', alignItems:'center', justifyContent:'space-between', paddingHorizontal:14, paddingVertical:11 },
    sbDropdownText:{ fontSize:13, fontWeight:'600' },
    topBar:{ flexDirection:'row', alignItems:'center', justifyContent:'space-between', paddingHorizontal:16, paddingVertical:12 },
    topLogo:{ fontSize:22, fontWeight:'900', letterSpacing:0.5 },
    iconBtn:{ padding:4 },
    body:{ padding:16 },
    sessionCard:{ borderRadius:16, padding:18, marginBottom:14 },
    sessionTop:{ flexDirection:'row', justifyContent:'space-between', alignItems:'flex-start' },
    sessionLabel:{ fontSize:11, color:'#cfffdf', fontWeight:'600', textTransform:'uppercase', letterSpacing:1, marginBottom:4 },
    sessionName:{ fontSize:18, fontWeight:'800', color:'#fff', marginBottom:2 },
    sessionZone:{ fontSize:13, color:'#cfffdf' },
    sessionDate:{ fontSize:12, color:'rgba(255,255,255,0.6)', marginTop:12 },
    dutyBadge:{ flexDirection:'row', alignItems:'center', gap:5, backgroundColor:'rgba(255,255,255,0.2)', paddingHorizontal:10, paddingVertical:6, borderRadius:20 },
    dutyBadgeOff:{ backgroundColor:'rgba(0,0,0,0.2)' },
    dutyDot:{ width:7, height:7, borderRadius:4, backgroundColor:'#86efac' },
    dutyText:{ color:'#fff', fontSize:11, fontWeight:'800', letterSpacing:0.5 },
    statsRow:{ flexDirection:'row', gap:12, marginBottom:14 },
    statCard:{ flex:1, borderRadius:14, padding:16, alignItems:'center', gap:6, shadowColor:'#000', shadowOffset:{width:0,height:2}, shadowOpacity:0.06, shadowRadius:6, elevation:3 },
    statVal:{ fontSize:24, fontWeight:'800' },
    statLabel:{ fontSize:11, textAlign:'center', fontWeight:'600' },
    ctaBtn:{ flexDirection:'row', alignItems:'center', justifyContent:'center', gap:10, height:52, backgroundColor: SprintColors.yellow, borderRadius:14, marginBottom:20 },
    ctaText:{ fontSize:15, fontWeight:'800', color:'#1A1A1A', letterSpacing:0.3 },
    sectionHeader:{ flexDirection:'row', justifyContent:'space-between', alignItems:'center', marginBottom:10 },
    sectionTitle:{ fontSize:16, fontWeight:'800' },
    viewAll:{ fontSize:13, fontWeight:'600' },
    emptyCard:{ alignItems:'center', padding:32, borderRadius:14, gap:8 },
    emptyText:{ fontSize:14 },
    billCard:{ flexDirection:'row', alignItems:'center', gap:12, borderRadius:14, padding:14, marginBottom:8, shadowColor:'#000', shadowOffset:{width:0,height:1}, shadowOpacity:0.05, shadowRadius:4, elevation:2 },
    billIcon:{ width:40, height:40, borderRadius:10, backgroundColor:'rgba(30,181,58,0.1)', alignItems:'center', justifyContent:'center' },
    billPlate:{ fontSize:15, fontWeight:'700' },
    billMeta:{ fontSize:12, marginTop:2 },
    statusBadge:{ paddingHorizontal:10, paddingVertical:4, borderRadius:20 },
    badgePaid:{ backgroundColor:'rgba(30,181,58,0.12)' },
    badgePending:{ backgroundColor:'rgba(252,209,22,0.2)' },
    statusText:{ fontSize:10, fontWeight:'800', letterSpacing:0.5, color:'#1A1A1A' },
    tabBar:{ flexDirection:'row', borderTopWidth:1, paddingBottom:6, paddingTop:8 },
    tabItem:{ flex:1, alignItems:'center', gap:3 },
    tabLabel:{ fontSize:10, fontWeight:'600' },
  });
}

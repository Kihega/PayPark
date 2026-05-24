/**
 * ParkiPay — Officer Dashboard  (v3)
 */
import { useState, useRef, useEffect, useCallback } from 'react';
import {
  ActivityIndicator, Animated, Dimensions, Platform, SafeAreaView,
  ScrollView, StatusBar, StyleSheet, Text, TouchableOpacity,
  View, Modal, Pressable, RefreshControl,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useAuthStore }             from '@/store/authStore';
import { useSettingsStore, palette } from '@/store/settingsStore';
import { t }                        from '@/constants/i18n';
import { authService, billingService } from '@/services/api';
import { SprintColors }             from '@/constants/theme';

const { width: W } = Dimensions.get('window');
const SIDEBAR_W    = W * 0.75;

interface Bill {
  id: number; plateNumber: string; controlNumber: string;
  amountDue: string | number; generatedAt: string; status: string;
}

function fmtAmount(n: number) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000)     return `${Math.round(n / 1_000)}k`;
  return String(n);
}
function fmtTime(iso: string) {
  return new Date(iso).toLocaleTimeString('en-TZ', { hour: '2-digit', minute: '2-digit' });
}

export default function HomeScreen() {
  const { officer, clearAuth, refreshToken } = useAuthStore();
  const { language, theme, setLanguage, setTheme } = useSettingsStore();
  const C  = palette(theme);
  const tr = (k: string) => t(language, k);

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [onDuty,  setOnDuty]   = useState(true);
  const [bills,   setBills]    = useState<Bill[]>([]);
  const [totalBills,  setTotalBills]  = useState(0);
  const [totalAmount, setTotalAmount] = useState(0);
  const [loading,  setLoading]  = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  // Sidebar dropdown state
  const [langOpen, setLangOpen] = useState(false);
  const [modeOpen, setModeOpen] = useState(false);

  const slideX = useRef(new Animated.Value(-SIDEBAR_W)).current;

  const openSidebar = () => {
    setSidebarOpen(true);
    Animated.spring(slideX, { toValue: 0, useNativeDriver: true, bounciness: 0 }).start();
  };
  const closeSidebar = () => {
    setLangOpen(false); setModeOpen(false);
    Animated.timing(slideX, { toValue: -SIDEBAR_W, duration: 220, useNativeDriver: true })
      .start(() => setSidebarOpen(false));
  };

  const loadData = useCallback(async () => {
    try {
      const [hRes, sRes] = await Promise.allSettled([
        billingService.history(),
        billingService.stats(),
      ]);
      if (hRes.status === 'fulfilled') setBills((hRes.value.data as Bill[]).slice(0, 5));
      if (sRes.status === 'fulfilled') {
        setTotalBills(sRes.value.data.totalBills ?? 0);
        setTotalAmount(sRes.value.data.totalAmount ?? 0);
      }
    } catch { /* silent */ }
    finally { setLoading(false); setRefreshing(false); }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const doLogout = async () => {
    setShowLogoutModal(false);
    try { if (refreshToken) await authService.logout(refreshToken); } catch {}
    await clearAuth();
    router.replace('/(auth)/login');
  };

  if (!officer) return null;

  const today = new Date().toLocaleDateString(language === 'sw' ? 'sw-TZ' : 'en-TZ', {
    weekday: 'long', month: 'long', day: 'numeric',
  });
  const S = makeStyles(C);
  const topOffset = Platform.OS === 'android' ? (StatusBar.currentHeight ?? 24) : 0;

  return (
    <SafeAreaView style={[S.root, { backgroundColor: C.bg, paddingTop: topOffset }]}>

      {/* ══ Sidebar ════════════════════════════════════════════════════ */}
      {sidebarOpen && (
        <Modal transparent animationType="none" visible onRequestClose={closeSidebar}>
          <Pressable style={S.overlay} onPress={closeSidebar} />
          <Animated.View style={[S.sidebar, { transform: [{ translateX: slideX }] }]}>

            {/* Sidebar header */}
            <View style={S.sbHead}>
              <View style={S.sbAvatar}>
                <Text style={S.sbAvatarText}>{officer.fullName.charAt(0).toUpperCase()}</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={S.sbName} numberOfLines={1}>{officer.fullName}</Text>
                <Text style={S.sbRole}>{officer.role === 'FIELD_OFFICER' ? tr('fieldOfficer') : tr('supervisor')}</Text>
              </View>
              <TouchableOpacity onPress={closeSidebar}>
                <Ionicons name="close" size={22} color="#9CA3AF" />
              </TouchableOpacity>
            </View>

            <View style={S.sbDivider} />

            {/* Language dropdown */}
            <TouchableOpacity style={S.sbRow}
              onPress={() => { setLangOpen(v => !v); setModeOpen(false); }}>
              <Ionicons name="language-outline" size={18} color="#9CA3AF" />
              <Text style={S.sbRowLabel}>{tr('language')}</Text>
              <View style={S.sbRowRight}>
                <Text style={S.sbRowValue}>
                  {language === 'en' ? '🇬🇧 English' : '🇹🇿 Kiswahili'}
                </Text>
                <Ionicons name={langOpen ? 'chevron-up' : 'chevron-down'} size={14} color="#9CA3AF" />
              </View>
            </TouchableOpacity>
            {langOpen && (
              <View style={S.sbDropdown}>
                {([['en', '🇬🇧 English (US)'], ['sw', '🇹🇿 Kiswahili']] as const).map(([code, label]) => (
                  <TouchableOpacity key={code}
                    style={[S.sbDropItem, language === code && S.sbDropItemActive]}
                    onPress={() => { setLanguage(code); setLangOpen(false); }}>
                    <Text style={[S.sbDropText, language === code && { color: SprintColors.green }]}>
                      {label}
                    </Text>
                    {language === code && <Ionicons name="checkmark" size={15} color={SprintColors.green} />}
                  </TouchableOpacity>
                ))}
              </View>
            )}

            {/* Mode dropdown */}
            <TouchableOpacity style={S.sbRow}
              onPress={() => { setModeOpen(v => !v); setLangOpen(false); }}>
              <Ionicons name={theme === 'dark' ? 'moon-outline' : 'sunny-outline'} size={18} color="#9CA3AF" />
              <Text style={S.sbRowLabel}>Mode</Text>
              <View style={S.sbRowRight}>
                <Text style={S.sbRowValue}>{theme === 'dark' ? '🌙 Dark' : '☀️ Light'}</Text>
                <Ionicons name={modeOpen ? 'chevron-up' : 'chevron-down'} size={14} color="#9CA3AF" />
              </View>
            </TouchableOpacity>
            {modeOpen && (
              <View style={S.sbDropdown}>
                {([['light', '☀️ Light'], ['dark', '🌙 Dark']] as const).map(([mode, label]) => (
                  <TouchableOpacity key={mode}
                    style={[S.sbDropItem, theme === mode && S.sbDropItemActive]}
                    onPress={() => { setTheme(mode); setModeOpen(false); }}>
                    <Text style={[S.sbDropText, theme === mode && { color: SprintColors.green }]}>
                      {label}
                    </Text>
                    {theme === mode && <Ionicons name="checkmark" size={15} color={SprintColors.green} />}
                  </TouchableOpacity>
                ))}
              </View>
            )}

            <View style={S.sbDivider} />

            {/* Logout */}
            <TouchableOpacity style={S.sbLogout}
              onPress={() => { closeSidebar(); setTimeout(() => setShowLogoutModal(true), 260); }}>
              <View style={S.sbLogoutIcon}>
                <Ionicons name="log-out-outline" size={20} color="#EF4444" />
              </View>
              <Text style={S.sbLogoutText}>{tr('logout')}</Text>
            </TouchableOpacity>
          </Animated.View>
        </Modal>
      )}

      {/* ══ Logout Confirm Modal ══════════════════════════════════════ */}
      <Modal visible={showLogoutModal} transparent animationType="fade"
        onRequestClose={() => setShowLogoutModal(false)}>
        <Pressable style={S.modalBackdrop} onPress={() => setShowLogoutModal(false)} />
        <View style={S.modalCenter}>
          <View style={[S.logoutCard, { backgroundColor: C.card }]}>
            <View style={S.logoutIconWrap}>
              <Ionicons name="log-out-outline" size={32} color="#EF4444" />
            </View>
            <Text style={[S.logoutCardTitle, { color: C.text }]}>{tr('logout')}</Text>
            <Text style={[S.logoutCardMsg,   { color: C.textSub }]}>{tr('logoutConfirm')}</Text>
            <View style={S.logoutBtnRow}>
              <TouchableOpacity style={[S.logoutCancelBtn, { borderColor: C.border }]}
                onPress={() => setShowLogoutModal(false)}>
                <Text style={[S.logoutCancelText, { color: C.textSub }]}>{tr('no')}</Text>
              </TouchableOpacity>
              <TouchableOpacity style={S.logoutConfirmBtn} onPress={doLogout}>
                <Ionicons name="log-out-outline" size={16} color="#fff" />
                <Text style={S.logoutConfirmText}>{tr('yes')}</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* ══ Top bar ══════════════════════════════════════════════════ */}
      <View style={[S.topBar, { backgroundColor: C.headerBg }]}>
        <TouchableOpacity onPress={openSidebar} style={S.iconBtn}>
          <Ionicons name="menu" size={24} color={C.headerText} />
        </TouchableOpacity>
        <View style={{ flexDirection: 'row' }}>
          <Text style={[S.topLogo, { color: SprintColors.green }]}>Parki</Text>
          <Text style={[S.topLogo, { color: SprintColors.yellow }]}>Pay</Text>
        </View>
        <TouchableOpacity style={S.iconBtn} onPress={loadData}>
          <Ionicons name="refresh-outline" size={22} color={C.headerText} />
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={[S.body, { backgroundColor: C.bg }]}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing}
          onRefresh={() => { setRefreshing(true); loadData(); }}
          tintColor={SprintColors.green} />}>

        {/* Active Session */}
        <LinearGradient colors={['#1EB53A', '#158A2A']}
          start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={S.sessionCard}>
          <View style={S.sessionTop}>
            <View style={{ flex: 1 }}>
              <Text style={S.sessionLabel}>{tr('activeSession')}</Text>
              <Text style={S.sessionName}>{officer.fullName}</Text>
              <Text style={S.sessionZone}>
                <Ionicons name="location-outline" size={13} color="#cfffdf" />
                {'  '}{officer.locationName ?? 'Unassigned'}
              </Text>
            </View>
            <TouchableOpacity onPress={() => setOnDuty(v => !v)}
              style={[S.dutyBadge, !onDuty && S.dutyBadgeOff]}>
              <View style={[S.dutyDot, !onDuty && { backgroundColor: '#9CA3AF' }]} />
              <Text style={S.dutyText}>{onDuty ? tr('onDuty') : tr('offDuty')}</Text>
            </TouchableOpacity>
          </View>
          <Text style={S.sessionDate}>{today}</Text>
        </LinearGradient>

        {/* Stats */}
        <View style={S.statsRow}>
          {[
            { icon: 'file-document-outline', label: tr('totalBills'), value: loading ? '…' : String(totalBills) },
            { icon: 'cash-multiple',          label: tr('amountCollected'), value: loading ? '…' : fmtAmount(totalAmount) },
          ].map(s => (
            <View key={s.label} style={[S.statCard, { backgroundColor: C.statCard }]}>
              <MaterialCommunityIcons name={s.icon as any} size={22} color={C.accent} />
              {loading
                ? <ActivityIndicator size="small" color={C.accent} />
                : <Text style={[S.statVal, { color: C.text }]}>{s.value}</Text>
              }
              <Text style={[S.statLabel, { color: C.textSub }]}>{s.label}</Text>
            </View>
          ))}
        </View>

        {/* CTA */}
        <TouchableOpacity style={S.ctaBtn} activeOpacity={0.85}
          onPress={() => router.push('/(app)/lookup')}>
          <Ionicons name="search" size={20} color="#1A1A1A" />
          <Text style={S.ctaText}>{tr('newLookup')}</Text>
        </TouchableOpacity>

        {/* Recent Bills */}
        <View style={S.sectionRow}>
          <Text style={[S.sectionTitle, { color: C.text }]}>{tr('recentBills')}</Text>
          <TouchableOpacity onPress={() => router.push('/(app)/history')}>
            <Text style={[S.viewAll, { color: C.accent }]}>{tr('viewAll')}</Text>
          </TouchableOpacity>
        </View>

        {loading ? (
          <ActivityIndicator color={SprintColors.green} size="large" style={{ marginTop: 24 }} />
        ) : bills.length === 0 ? (
          <View style={[S.emptyCard, { backgroundColor: C.card }]}>
            <MaterialCommunityIcons name="car-off" size={36} color={C.textMuted} />
            <Text style={[S.emptyText, { color: C.textMuted }]}>{tr('noBills')}</Text>
          </View>
        ) : (
          bills.map(bill => (
            <View key={bill.id} style={[S.billCard, { backgroundColor: C.card }]}>
              <View style={S.billIcon}>
                <MaterialCommunityIcons name="car-outline" size={22} color={C.accent} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={[S.billPlate, { color: C.text }]}>{bill.plateNumber}</Text>
                <Text style={[S.billMeta,  { color: C.textSub }]}>
                  {Number(bill.amountDue).toLocaleString()} {tr('tzs')} · {fmtTime(bill.generatedAt)}
                </Text>
              </View>
              <View style={[S.statusBadge,
                bill.status === 'PAID' ? S.badgePaid : S.badgePending]}>
                <Text style={S.statusText}>
                  {bill.status === 'PAID' ? tr('paid') : tr('pending')}
                </Text>
              </View>
            </View>
          ))
        )}

        <View style={{ height: 24 }} />
      </ScrollView>

      {/* Tab Bar */}
      <View style={[S.tabBar, { backgroundColor: C.navBg, borderTopColor: C.navBorder }]}>
        {([
          { icon: 'grid-outline',        label: tr('dashboard'), active: true,  onPress: () => {} },
          { icon: 'search-outline',      label: tr('lookup'),    active: false, onPress: () => router.push('/(app)/lookup') },
          { icon: 'time-outline',        label: tr('history'),   active: false, onPress: () => router.push('/(app)/history') },
          { icon: 'alert-circle-outline',label: tr('alerts'),    active: false, onPress: () => router.push('/(app)/alerts') },
        ] as const).map((tab, i) => (
          <TouchableOpacity key={i} style={S.tabItem} onPress={tab.onPress}>
            <Ionicons name={tab.icon as any} size={22}
              color={tab.active ? C.navActive : C.textMuted} />
            <Text style={[S.tabLabel, { color: tab.active ? C.navActive : C.textMuted }]}>
              {tab.label}
            </Text>
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
    // Sidebar
    sidebar:{ position:'absolute', left:0, top:0, bottom:0, width: W * 0.75,
      backgroundColor:'#111827', paddingTop:56, zIndex:99 },
    sbHead:{ flexDirection:'row', alignItems:'center', gap:12, paddingHorizontal:20, marginBottom:20 },
    sbAvatar:{ width:42, height:42, borderRadius:21, backgroundColor: SprintColors.green,
      alignItems:'center', justifyContent:'center' },
    sbAvatarText:{ color:'#fff', fontWeight:'900', fontSize:18 },
    sbName:{ fontSize:14, fontWeight:'800', color:'#F9FAFB' },
    sbRole:{ fontSize:11, color:'#9CA3AF', marginTop:1 },
    sbDivider:{ height:1, backgroundColor:'rgba(255,255,255,0.08)', marginHorizontal:20, marginVertical:8 },
    sbRow:{ flexDirection:'row', alignItems:'center', gap:12, paddingHorizontal:20, paddingVertical:13 },
    sbRowLabel:{ flex:1, fontSize:14, color:'#D1D5DB', fontWeight:'600' },
    sbRowRight:{ flexDirection:'row', alignItems:'center', gap:6 },
    sbRowValue:{ fontSize:12, color:'#9CA3AF' },
    sbDropdown:{ marginHorizontal:20, borderRadius:10, overflow:'hidden',
      backgroundColor:'rgba(255,255,255,0.05)', marginBottom:4 },
    sbDropItem:{ flexDirection:'row', alignItems:'center', justifyContent:'space-between',
      paddingHorizontal:16, paddingVertical:12 },
    sbDropItemActive:{ backgroundColor:'rgba(30,181,58,0.12)' },
    sbDropText:{ fontSize:13, fontWeight:'600', color:'#D1D5DB' },
    sbLogout:{ flexDirection:'row', alignItems:'center', gap:12, paddingHorizontal:20, paddingVertical:14, marginTop:4 },
    sbLogoutIcon:{ width:36, height:36, borderRadius:10,
      backgroundColor:'rgba(239,68,68,0.12)', alignItems:'center', justifyContent:'center' },
    sbLogoutText:{ color:'#EF4444', fontWeight:'700', fontSize:15 },
    // Logout modal
    modalBackdrop:{ ...StyleSheet.absoluteFillObject, backgroundColor:'rgba(0,0,0,0.55)' },
    modalCenter:{ flex:1, alignItems:'center', justifyContent:'center', padding:32 },
    logoutCard:{ width:'100%', borderRadius:20, padding:24, alignItems:'center',
      shadowColor:'#000', shadowOffset:{width:0,height:8},
      shadowOpacity:0.2, shadowRadius:20, elevation:12 },
    logoutIconWrap:{ width:64, height:64, borderRadius:18,
      backgroundColor:'rgba(239,68,68,0.1)', alignItems:'center',
      justifyContent:'center', marginBottom:14 },
    logoutCardTitle:{ fontSize:20, fontWeight:'900', marginBottom:8 },
    logoutCardMsg:{ fontSize:14, textAlign:'center', lineHeight:21, marginBottom:24 },
    logoutBtnRow:{ flexDirection:'row', gap:12, width:'100%' },
    logoutCancelBtn:{ flex:1, height:48, borderRadius:12, borderWidth:1.5,
      alignItems:'center', justifyContent:'center' },
    logoutCancelText:{ fontWeight:'600', fontSize:14 },
    logoutConfirmBtn:{ flex:1, height:48, borderRadius:12, backgroundColor:'#EF4444',
      flexDirection:'row', alignItems:'center', justifyContent:'center', gap:8 },
    logoutConfirmText:{ color:'#fff', fontWeight:'800', fontSize:14 },
    // Top bar
    topBar:{ flexDirection:'row', alignItems:'center', justifyContent:'space-between',
      paddingHorizontal:16, paddingVertical:12 },
    topLogo:{ fontSize:22, fontWeight:'900', letterSpacing:0.5 },
    iconBtn:{ padding:4 },
    body:{ padding:16 },
    // Session
    sessionCard:{ borderRadius:16, padding:18, marginBottom:14 },
    sessionTop:{ flexDirection:'row', justifyContent:'space-between', alignItems:'flex-start' },
    sessionLabel:{ fontSize:11, color:'#cfffdf', fontWeight:'600',
      textTransform:'uppercase', letterSpacing:1, marginBottom:4 },
    sessionName:{ fontSize:18, fontWeight:'800', color:'#fff', marginBottom:2 },
    sessionZone:{ fontSize:13, color:'#cfffdf' },
    sessionDate:{ fontSize:12, color:'rgba(255,255,255,0.6)', marginTop:12 },
    dutyBadge:{ flexDirection:'row', alignItems:'center', gap:5,
      backgroundColor:'rgba(255,255,255,0.2)', paddingHorizontal:10,
      paddingVertical:6, borderRadius:20 },
    dutyBadgeOff:{ backgroundColor:'rgba(0,0,0,0.2)' },
    dutyDot:{ width:7, height:7, borderRadius:4, backgroundColor:'#86efac' },
    dutyText:{ color:'#fff', fontSize:11, fontWeight:'800', letterSpacing:0.5 },
    // Stats
    statsRow:{ flexDirection:'row', gap:12, marginBottom:14 },
    statCard:{ flex:1, borderRadius:14, padding:16, alignItems:'center', gap:6,
      shadowColor:'#000', shadowOffset:{width:0,height:2},
      shadowOpacity:0.06, shadowRadius:6, elevation:3 },
    statVal:{ fontSize:24, fontWeight:'800' },
    statLabel:{ fontSize:11, textAlign:'center', fontWeight:'600' },
    ctaBtn:{ flexDirection:'row', alignItems:'center', justifyContent:'center',
      gap:10, height:52, backgroundColor: SprintColors.yellow,
      borderRadius:14, marginBottom:20 },
    ctaText:{ fontSize:15, fontWeight:'800', color:'#1A1A1A', letterSpacing:0.3 },
    sectionRow:{ flexDirection:'row', justifyContent:'space-between',
      alignItems:'center', marginBottom:10 },
    sectionTitle:{ fontSize:16, fontWeight:'800' },
    viewAll:{ fontSize:13, fontWeight:'600' },
    emptyCard:{ alignItems:'center', padding:32, borderRadius:14, gap:8 },
    emptyText:{ fontSize:14 },
    billCard:{ flexDirection:'row', alignItems:'center', gap:12, borderRadius:14,
      padding:14, marginBottom:8, shadowColor:'#000',
      shadowOffset:{width:0,height:1}, shadowOpacity:0.05, shadowRadius:4, elevation:2 },
    billIcon:{ width:40, height:40, borderRadius:10,
      backgroundColor:'rgba(30,181,58,0.1)', alignItems:'center', justifyContent:'center' },
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

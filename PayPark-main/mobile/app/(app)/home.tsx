/**
 * ParkiPay — Officer Dashboard  (v2)
 */
import { useState, useRef, useEffect } from 'react';
import {
  Alert, Animated, Dimensions, SafeAreaView, ScrollView,
  StyleSheet, Text, TouchableOpacity, View, Modal, Pressable,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useAuthStore } from '@/store/authStore';
import { useSettingsStore, palette } from '@/store/settingsStore';
import { t } from '@/constants/i18n';
import { authService } from '@/services/api';
import { SprintColors } from '@/constants/theme';

const { width: W } = Dimensions.get('window');
const SIDEBAR_W = W * 0.72;

/* ── mock recent bills (replace with API in Sprint 2) ──────────────────────── */
const MOCK_BILLS = [
  { id:'1', plate:'T 482 DXG', amount:'1,000', time:'14:22', status:'paid'    },
  { id:'2', plate:'T 109 ASZ', amount:'5,000', time:'13:10', status:'pending' },
  { id:'3', plate:'T 882 KLP', amount:'1,000', time:'12:00', status:'paid'    },
];

export default function HomeScreen() {
  const { officer, clearAuth, refreshToken } = useAuthStore();
  const { language, theme, setLanguage, setTheme } = useSettingsStore();
  const C = palette(theme);
  const tr = (k: string) => t(language, k);

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [onDuty, setOnDuty]           = useState(true);
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
    weekday:'long', month:'long', day:'numeric',
  });

  const dynStyles = makeStyles(C);

  return (
    <SafeAreaView style={[dynStyles.root]}>

      {/* ── Sidebar overlay ────────────────────────────────────────────── */}
      {sidebarOpen && (
        <Modal transparent animationType="none" visible={sidebarOpen}
          onRequestClose={closeSidebar}>
          <Pressable style={dynStyles.overlay} onPress={closeSidebar} />
          <Animated.View style={[dynStyles.sidebar, { transform:[{translateX: slideX}] }]}>
            <View style={dynStyles.sbHeader}>
              <Text style={dynStyles.sbHeaderText}>⚙ {tr('settings')}</Text>
              <TouchableOpacity onPress={closeSidebar}>
                <Ionicons name="close" size={22} color={C.sidebarText} />
              </TouchableOpacity>
            </View>

            {/* Language */}
            <Text style={dynStyles.sbSection}>{tr('language')}</Text>
            <View style={dynStyles.toggleRow}>
              {(['en','sw'] as const).map(lang => (
                <TouchableOpacity key={lang} onPress={() => setLanguage(lang)}
                  style={[dynStyles.toggleBtn, language===lang && dynStyles.toggleActive]}>
                  <Text style={[dynStyles.toggleText, language===lang && dynStyles.toggleActiveText]}>
                    {lang==='en' ? tr('english') : tr('swahili')}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            {/* Theme */}
            <Text style={dynStyles.sbSection}>{tr('theme')}</Text>
            <View style={dynStyles.toggleRow}>
              {(['light','dark'] as const).map(th => (
                <TouchableOpacity key={th} onPress={() => setTheme(th)}
                  style={[dynStyles.toggleBtn, theme===th && dynStyles.toggleActive]}>
                  <Ionicons name={th==='light' ? 'sunny-outline' : 'moon-outline'}
                    size={14} color={theme===th ? '#fff' : C.sidebarText} />
                  <Text style={[dynStyles.toggleText, theme===th && dynStyles.toggleActiveText]}>
                    {th==='light' ? tr('lightMode') : tr('darkMode')}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <View style={dynStyles.sbDivider} />

            <TouchableOpacity style={dynStyles.logoutBtn} onPress={handleLogout}>
              <Ionicons name="log-out-outline" size={18} color="#EF4444" />
              <Text style={dynStyles.logoutText}>{tr('logout')}</Text>
            </TouchableOpacity>
          </Animated.View>
        </Modal>
      )}

      {/* ── Top bar ────────────────────────────────────────────────────── */}
      <View style={[dynStyles.topBar, {backgroundColor: C.headerBg}]}>
        <TouchableOpacity onPress={openSidebar} style={dynStyles.iconBtn}>
          <Ionicons name="menu" size={24} color={C.headerText} />
        </TouchableOpacity>
        <View style={{flexDirection:'row'}}>
          <Text style={[dynStyles.topLogo,{color:SprintColors.green}]}>Parki</Text>
          <Text style={[dynStyles.topLogo,{color:SprintColors.yellow}]}>Pay</Text>
        </View>
        <TouchableOpacity style={dynStyles.iconBtn}>
          <Ionicons name="notifications-outline" size={22} color={C.headerText} />
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={[dynStyles.body,{backgroundColor:C.bg}]}
        showsVerticalScrollIndicator={false}>

        {/* ── Active Session card ────────────────────────────────────── */}
        <LinearGradient colors={['#1EB53A','#158A2A']}
          start={{x:0,y:0}} end={{x:1,y:1}} style={dynStyles.sessionCard}>
          <View style={dynStyles.sessionTop}>
            <View>
              <Text style={dynStyles.sessionLabel}>{tr('activeSession')}</Text>
              <Text style={dynStyles.sessionName}>{officer.fullName}</Text>
              <Text style={dynStyles.sessionZone}>
                <Ionicons name="location-outline" size={13} color="#cfffdf" />
                {'  '}{officer.locationName ?? 'Unassigned'}
              </Text>
            </View>
            <TouchableOpacity onPress={() => setOnDuty(v=>!v)}
              style={[dynStyles.dutyBadge, !onDuty && dynStyles.dutyBadgeOff]}>
              <View style={[dynStyles.dutyDot, !onDuty && {backgroundColor:'#9CA3AF'}]} />
              <Text style={dynStyles.dutyText}>{onDuty ? tr('onDuty') : tr('offDuty')}</Text>
            </TouchableOpacity>
          </View>
          <Text style={dynStyles.sessionDate}>{today}</Text>
        </LinearGradient>

        {/* ── Stats row ─────────────────────────────────────────────── */}
        <View style={dynStyles.statsRow}>
          <View style={[dynStyles.statCard, {backgroundColor: C.statCard}]}>
            <MaterialCommunityIcons name="file-document-outline" size={22} color={C.accent} />
            <Text style={[dynStyles.statVal, {color: C.text}]}>24</Text>
            <Text style={[dynStyles.statLabel, {color: C.textSub}]}>{tr('totalBills')}</Text>
          </View>
          <View style={[dynStyles.statCard, {backgroundColor: C.statCard}]}>
            <MaterialCommunityIcons name="cash-multiple" size={22} color={C.accent} />
            <Text style={[dynStyles.statVal, {color: C.text}]}>48k</Text>
            <Text style={[dynStyles.statLabel, {color: C.textSub}]}>{tr('amountCollected')}</Text>
          </View>
        </View>

        {/* ── CTA ───────────────────────────────────────────────────── */}
        <TouchableOpacity style={dynStyles.ctaBtn} activeOpacity={0.85}>
          <Ionicons name="search" size={20} color="#1A1A1A" />
          <Text style={dynStyles.ctaText}>{tr('newLookup')}</Text>
        </TouchableOpacity>

        {/* ── Recent Bills ──────────────────────────────────────────── */}
        <View style={dynStyles.sectionHeader}>
          <Text style={[dynStyles.sectionTitle, {color: C.text}]}>{tr('recentBills')}</Text>
          <TouchableOpacity>
            <Text style={[dynStyles.viewAll, {color: C.accent}]}>{tr('viewAll')}</Text>
          </TouchableOpacity>
        </View>

        {MOCK_BILLS.length === 0
          ? <View style={[dynStyles.emptyCard, {backgroundColor: C.card}]}>
              <MaterialCommunityIcons name="car-off" size={36} color={C.textMuted} />
              <Text style={[dynStyles.emptyText, {color: C.textMuted}]}>{tr('noBills')}</Text>
            </View>
          : MOCK_BILLS.map(bill => (
            <View key={bill.id} style={[dynStyles.billCard, {backgroundColor: C.card}]}>
              <View style={dynStyles.billIcon}>
                <MaterialCommunityIcons name="car-outline" size={22} color={C.accent} />
              </View>
              <View style={{flex:1}}>
                <Text style={[dynStyles.billPlate, {color: C.text}]}>{bill.plate}</Text>
                <Text style={[dynStyles.billMeta, {color: C.textSub}]}>
                  {bill.amount} {tr('tzs')} · {bill.time}
                </Text>
              </View>
              <View style={[dynStyles.statusBadge,
                bill.status==='paid' ? dynStyles.badgePaid : dynStyles.badgePending]}>
                <Text style={dynStyles.statusText}>
                  {bill.status==='paid' ? tr('paid') : tr('pending')}
                </Text>
              </View>
            </View>
          ))
        }

        <View style={{height: 24}} />
      </ScrollView>

      {/* ── Bottom Tab Bar ────────────────────────────────────────────── */}
      <View style={[dynStyles.tabBar, {backgroundColor: C.navBg, borderTopColor: C.navBorder}]}>
        {[
          { icon:'grid-outline',    label: tr('dashboard'), active: true  },
          { icon:'search-outline',  label: tr('lookup'),    active: false },
          { icon:'time-outline',    label: tr('history'),   active: false },
          { icon:'alert-circle-outline', label: tr('alerts'), active: false },
        ].map((tab,i) => (
          <TouchableOpacity key={i} style={dynStyles.tabItem}>
            <Ionicons name={tab.icon as any} size={22}
              color={tab.active ? C.navActive : C.textMuted} />
            <Text style={[dynStyles.tabLabel,
              {color: tab.active ? C.navActive : C.textMuted}]}>{tab.label}</Text>
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
      position:'absolute', left:0, top:0, bottom:0, width:SIDEBAR_W,
      backgroundColor: C.sidebarBg, paddingTop:56, paddingHorizontal:20, zIndex:99,
    },
    sbHeader:{ flexDirection:'row', justifyContent:'space-between',
      alignItems:'center', marginBottom:28 },
    sbHeaderText:{ fontSize:17, fontWeight:'700', color: C.sidebarText },
    sbSection:{ fontSize:11, fontWeight:'700', color:'#6B7280',
      letterSpacing:1.2, textTransform:'uppercase', marginBottom:10, marginTop:4 },
    toggleRow:{ flexDirection:'row', gap:8, marginBottom:20 },
    toggleBtn:{ flex:1, paddingVertical:9, borderRadius:8, alignItems:'center',
      justifyContent:'center', flexDirection:'row', gap:5,
      backgroundColor:'rgba(255,255,255,0.08)' },
    toggleActive:{ backgroundColor: SprintColors.green },
    toggleText:{ fontSize:13, color: C.sidebarText, fontWeight:'600' },
    toggleActiveText:{ color:'#fff' },
    sbDivider:{ height:1, backgroundColor:'rgba(255,255,255,0.1)', marginVertical:16 },
    logoutBtn:{ flexDirection:'row', alignItems:'center', gap:10,
      paddingVertical:12, paddingHorizontal:14, borderRadius:10,
      backgroundColor:'rgba(239,68,68,0.12)' },
    logoutText:{ color:'#EF4444', fontWeight:'700', fontSize:15 },

    topBar:{ flexDirection:'row', alignItems:'center', justifyContent:'space-between',
      paddingHorizontal:16, paddingVertical:12 },
    topLogo:{ fontSize:22, fontWeight:'900', letterSpacing:0.5 },
    iconBtn:{ padding:4 },

    body:{ padding:16 },

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

    sectionHeader:{ flexDirection:'row', justifyContent:'space-between',
      alignItems:'center', marginBottom:10 },
    sectionTitle:{ fontSize:16, fontWeight:'800' },
    viewAll:{ fontSize:13, fontWeight:'600' },

    emptyCard:{ alignItems:'center', padding:32, borderRadius:14, gap:8 },
    emptyText:{ fontSize:14 },

    billCard:{ flexDirection:'row', alignItems:'center', gap:12,
      borderRadius:14, padding:14, marginBottom:8,
      shadowColor:'#000', shadowOffset:{width:0,height:1},
      shadowOpacity:0.05, shadowRadius:4, elevation:2 },
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

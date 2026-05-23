/**
 * ParkiPay — Admin Screen (simple officer management)
 */
import { useState, useEffect, useCallback } from 'react';
import { ActivityIndicator, FlatList, Modal, Platform, Pressable,
  SafeAreaView, StatusBar, StyleSheet, Text, TextInput,
  TouchableOpacity, View, Alert } from "react-native";
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useAuthStore } from '@/store/authStore';
import { useSettingsStore, palette } from '@/store/settingsStore';
import { t } from '@/constants/i18n';
import { adminService, authService } from '@/services/api';
import { SprintColors } from '@/constants/theme';
import ConfirmModal from '@/components/ConfirmModal';

interface Officer { id:number; employeeId:string; fullName:string; locationName:string|null; role:string; }
interface Location { id:number; name:string; region:string; }

const ROLE_COLORS: Record<string,string> = {
  FIELD_OFFICER: SprintColors.green, SUPERVISOR: '#1565C0', ADMIN: '#6A1B9A',
};

export default function AdminScreen() {
  const { clearAuth, refreshToken, officer: me } = useAuthStore();
  const { language, theme, setLanguage, setTheme } = useSettingsStore();
  const C = palette(theme);
  const tr = (k:string) => t(language, k);

  const [officers,     setOfficers]     = useState<Officer[]>([]);
  const [locations,    setLocations]    = useState<Location[]>([]);
  const [loading,      setLoading]      = useState(true);
  const [showAdd,      setShowAdd]      = useState(false);
  const [showMove,     setShowMove]     = useState<Officer|null>(null);
  const [newName,      setNewName]      = useState('');
  const [newEmpId,     setNewEmpId]     = useState('');
  const [newLocId,     setNewLocId]     = useState<number|null>(null);
  const [saving,       setSaving]       = useState(false);
  const [sidebarOpen,  setSidebarOpen]  = useState(false);
  const [removeTarget, setRemoveTarget] = useState<Officer|null>(null);
  const [confirmAlert, setConfirmAlert] = useState<{title:string;message:string;variant:any;onOk:()=>void}|null>(null);
  const [langOpen,     setLangOpen]     = useState(false);
  const [modeOpen,     setModeOpen]     = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [oRes, lRes] = await Promise.all([
        adminService.listOfficers(),
        adminService.listLocations(),
      ]);
      setOfficers(oRes.data);
      setLocations(lRes.data);
    } catch { Alert.alert('Error','Failed to load data'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleAdd = async () => {
    if (!newName.trim() || !newEmpId.trim()) {
      Alert.alert('', 'Name and Employee ID are required'); return;
    }
    setSaving(true);
    try {
      await adminService.createOfficer({ fullName:newName.trim(),
        employeeId:newEmpId.trim().toUpperCase(), locationId:newLocId });
      setShowAdd(false); setNewName(''); setNewEmpId(''); setNewLocId(null);
      load();
    } catch (e:any) {
      Alert.alert('Error', e?.response?.data?.detail ?? 'Failed to create officer');
    } finally { setSaving(false); }
  };


  const handleRemove = (o: Officer) => setRemoveTarget(o);

  const confirmRemove = async () => {
    if (!removeTarget) return;
    setRemoveTarget(null);
    try { await adminService.removeOfficer(removeTarget.id); load(); }
    catch (e: any) {
      const msg = e?.response?.data?.detail ?? 'Failed to remove officer.';
      setConfirmAlert({ title: 'Error', message: msg, variant: 'warning',
        onOk: () => setConfirmAlert(null) });
    }
  };

  const handleMove = async (locationId: number) => {
    if (!showMove) return;
    try {
      await adminService.moveOfficer(showMove.id, locationId);
      setShowMove(null); load();
    } catch { Alert.alert('Error','Failed to move officer'); }
  };

  const handleLogout = async () => {
    try { if (refreshToken) await (await import('@/services/api')).authService.logout(refreshToken); }
    catch {}
    await clearAuth(); router.replace('/(auth)/login');
  };

  const topOffset = Platform.OS === 'android' ? (StatusBar.currentHeight ?? 24) : 0;
  return (
    <SafeAreaView style={[styles.root, {backgroundColor: C.bg, paddingTop: topOffset}]}>
      {/* Header */}
      <View style={[styles.header, {backgroundColor: C.headerBg}]}>
        <TouchableOpacity onPress={() => setSidebarOpen(true)} style={styles.menuBtn}>
          <Ionicons name="menu" size={22} color="#fff" />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, {color: '#fff'}]}>{tr('adminPanel')}</Text>
        <TouchableOpacity onPress={handleLogout} style={styles.logoutBtn}>
          <Ionicons name="log-out-outline" size={20} color="#EF4444" />
        </TouchableOpacity>
      </View>

      {/* ── Sidebar ────────────────────────────────────────────────────── */}
      {sidebarOpen && (
        <Modal transparent animationType="none" visible={sidebarOpen} onRequestClose={() => setSidebarOpen(false)}>
          <Pressable style={styles.sidebarOverlay} onPress={() => setSidebarOpen(false)} />
          <View style={[styles.sidebarPanel, {backgroundColor: C.sidebarBg ?? '#111827'}]}>
            <View style={styles.sbTop}>
              <MaterialCommunityIcons name="shield-account" size={28} color={SprintColors.yellow} />
              <Text style={styles.sbTitle}>Admin Menu</Text>
              <TouchableOpacity onPress={() => setSidebarOpen(false)} style={styles.sbClose}>
                <Ionicons name="close" size={20} color="#9CA3AF" />
              </TouchableOpacity>
            </View>

            <View style={styles.sbDivider} />

            {[
              { icon: 'people-outline', matIcon: null, label: 'Manage Officers',
                sub: 'Officer management & locations', onPress: () => setSidebarOpen(false) },
              { icon: null, matIcon: 'car-outline', label: 'Register Cars',
                sub: 'Vehicle registry management',
                onPress: () => { setSidebarOpen(false); router.push('/(app)/vehicles'); }},
            ].map(item => (
              <TouchableOpacity key={item.label} style={styles.sbItem} onPress={item.onPress}>
                <View style={styles.sbItemIcon}>
                  {item.matIcon
                    ? <MaterialCommunityIcons name={item.matIcon as any} size={22} color={SprintColors.green} />
                    : <Ionicons name={item.icon as any} size={22} color={SprintColors.green} />
                  }
                </View>
                <View style={{flex:1}}>
                  <Text style={styles.sbItemLabel}>{item.label}</Text>
                  <Text style={styles.sbItemSub}>{item.sub}</Text>
                </View>
                <Ionicons name="chevron-forward" size={16} color="#6B7280" />
              </TouchableOpacity>
            ))}

            <View style={styles.sbDivider} />

            <TouchableOpacity style={styles.sbLogout} onPress={handleLogout}>
              <Ionicons name="log-out-outline" size={20} color="#EF4444" />
              <Text style={styles.sbLogoutText}>{tr('logout')}</Text>
            </TouchableOpacity>
          </View>
        </Modal>
      )}

      {/* Officers list */}
      {loading
        ? <ActivityIndicator style={{flex:1}} color={SprintColors.green} size="large" />
        : <FlatList
            data={officers}
            keyExtractor={o => String(o.id)}
            contentContainerStyle={{padding:16, paddingBottom:100}}
            ListEmptyComponent={
              <View style={styles.emptyWrap}>
                <MaterialCommunityIcons name="account-off-outline" size={48} color={C.textMuted}/>
                <Text style={[styles.emptyText,{color:C.textMuted}]}>{tr('noOfficers')}</Text>
              </View>
            }
            renderItem={({item:o}) => (
              <View style={[styles.card, {backgroundColor: C.card}]}>
                <View style={{flex:1}}>
                  <View style={{flexDirection:'row', alignItems:'center', gap:8, marginBottom:4}}>
                    <View style={[styles.roleChip,{backgroundColor:ROLE_COLORS[o.role]??SprintColors.green}]}>
                      <Text style={styles.roleText}>
                        {o.role==='FIELD_OFFICER' ? tr('fieldOfficer') : tr('supervisor')}
                      </Text>
                    </View>
                  </View>
                  <Text style={[styles.name,{color:C.text}]}>{o.fullName}</Text>
                  <Text style={[styles.meta,{color:C.textSub}]}>ID: {o.employeeId}</Text>
                  {o.locationName
                    ? <Text style={[styles.meta,{color:C.textSub}]}>
                        <Ionicons name="location-outline" size={12}/> {o.locationName}
                      </Text>
                    : <Text style={[styles.meta,{color:C.textMuted}]}>Unassigned</Text>}
                </View>
                <View style={styles.actions}>
                  <TouchableOpacity style={styles.actionBtn} onPress={()=>setShowMove(o)}>
                    <Ionicons name="swap-horizontal-outline" size={18} color={SprintColors.green}/>
                  </TouchableOpacity>
                  <TouchableOpacity style={[styles.actionBtn,{backgroundColor:'rgba(239,68,68,0.08)'}]}
                    onPress={()=>setRemoveTarget(o)}>
                    <Ionicons name="trash-outline" size={18} color="#EF4444"/>
                  </TouchableOpacity>
                </View>
              </View>
            )}
          />
      }

      {/* FAB */}
      <TouchableOpacity style={styles.fab} onPress={()=>setShowAdd(true)}>
        <Ionicons name="person-add-outline" size={22} color="#fff"/>
        <Text style={styles.fabText}>{tr('addOfficer')}</Text>
      </TouchableOpacity>

      {/* ── Add Officer Modal ──────────────────────────────────────────── */}
      <Modal visible={showAdd} transparent animationType="slide" onRequestClose={()=>setShowAdd(false)}>
        <Pressable style={styles.backdrop} onPress={()=>setShowAdd(false)}/>
        <View style={[styles.sheet, {backgroundColor: C.card}]}>
          <Text style={[styles.sheetTitle,{color:C.text}]}>{tr('addOfficer')}</Text>

          <Text style={[styles.inputLabel,{color:C.textSub}]}>{tr('officerName')}</Text>
          <TextInput style={[styles.input,{color:C.text,borderColor:C.border,backgroundColor:C.bg}]}
            value={newName} onChangeText={setNewName} placeholder="e.g. Juma Ally"
            placeholderTextColor={C.textMuted}/>

          <Text style={[styles.inputLabel,{color:C.textSub}]}>{tr('employeeIdLabel')}</Text>
          <TextInput style={[styles.input,{color:C.text,borderColor:C.border,backgroundColor:C.bg}]}
            value={newEmpId} onChangeText={setNewEmpId} placeholder="e.g. TZ-1234"
            autoCapitalize="characters" placeholderTextColor={C.textMuted}/>

          <Text style={[styles.inputLabel,{color:C.textSub}]}>{tr('selectLocation')}</Text>
          <View style={styles.locGrid}>
            {locations.map(loc => (
              <TouchableOpacity key={loc.id}
                style={[styles.locChip, newLocId===loc.id && styles.locChipActive]}
                onPress={()=>setNewLocId(loc.id)}>
                <Text style={[styles.locChipText, newLocId===loc.id && {color:'#fff'}]}>
                  {loc.name}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <TouchableOpacity style={[styles.saveBtn, saving && {opacity:0.6}]}
            onPress={handleAdd} disabled={saving}>
            {saving ? <ActivityIndicator color="#fff"/> :
              <Text style={styles.saveBtnText}>{tr('save')}</Text>}
          </TouchableOpacity>
        </View>
      </Modal>

      {/* ── Move Location Modal ────────────────────────────────────────── */}
      <Modal visible={!!showMove} transparent animationType="slide" onRequestClose={()=>setShowMove(null)}>
        <Pressable style={styles.backdrop} onPress={()=>setShowMove(null)}/>
        <View style={[styles.sheet,{backgroundColor:C.card}]}>
          <Text style={[styles.sheetTitle,{color:C.text}]}>{tr('moveLocation')}: {showMove?.fullName}</Text>
          <View style={styles.locGrid}>
            {locations.map(loc => (
              <TouchableOpacity key={loc.id} style={styles.locChip} onPress={()=>handleMove(loc.id)}>
                <Text style={styles.locChipText}>{loc.name}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      </Modal>

      {/* ── Remove Officer Confirm ────────────────────────────────────── */}
      <ConfirmModal
        visible={!!removeTarget}
        title={`Remove ${removeTarget?.fullName ?? ''}?`}
        message="This will permanently remove the officer from the system. Their bills will be retained."
        confirmLabel="Remove Officer"
        cancelLabel="Cancel"
        variant="danger"
        onConfirm={confirmRemove}
        onCancel={() => setRemoveTarget(null)}
      />

      {/* ── Generic Alert Modal ───────────────────────────────────────── */}
      {confirmAlert && (
        <ConfirmModal
          visible
          title={confirmAlert.title}
          message={confirmAlert.message}
          variant={confirmAlert.variant}
          confirmLabel="OK"
          cancelLabel=""
          onConfirm={confirmAlert.onOk}
          onCancel={confirmAlert.onOk}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root:{ flex:1 },
  header:{ flexDirection:'row', alignItems:'center', justifyContent:'space-between',
    paddingHorizontal:16, paddingVertical:14, backgroundColor:'#0D1117' },
  headerTitle:{ fontSize:18, fontWeight:'800' },
  menuBtn:{ width:36, height:36, borderRadius:10, alignItems:'center', justifyContent:'center',
    backgroundColor:'rgba(255,255,255,0.1)' },
  logoutBtn:{ padding:6 },
  // Sidebar
  sidebarOverlay:{ ...StyleSheet.absoluteFillObject, backgroundColor:'rgba(0,0,0,0.5)' },
  sidebarPanel:{ position:'absolute', left:0, top:0, bottom:0, width:280,
    paddingTop:56, paddingHorizontal:0, zIndex:99 },
  sbTop:{ flexDirection:'row', alignItems:'center', gap:12, paddingHorizontal:20, marginBottom:20 },
  sbTitle:{ flex:1, fontSize:17, fontWeight:'800', color:'#F9FAFB' },
  sbClose:{ padding:4 },
  sbDivider:{ height:1, backgroundColor:'rgba(255,255,255,0.08)', marginHorizontal:20, marginVertical:8 },
  sbItem:{ flexDirection:'row', alignItems:'center', gap:12, paddingHorizontal:20,
    paddingVertical:14 },
  sbItemIcon:{ width:38, height:38, borderRadius:10, alignItems:'center', justifyContent:'center',
    backgroundColor:'rgba(30,181,58,0.12)' },
  sbItemLabel:{ fontSize:15, fontWeight:'700', color:'#F9FAFB' },
  sbItemSub:{ fontSize:11, color:'#6B7280', marginTop:1 },
  sbLogout:{ flexDirection:'row', alignItems:'center', gap:12, paddingHorizontal:20,
    paddingVertical:14 },
  sbLogoutText:{ color:'#EF4444', fontWeight:'700', fontSize:15 },
  sbMenuRow:{ flexDirection:'row', alignItems:'center', gap:10,
    paddingHorizontal:20, paddingVertical:12 },
  sbMenuLabel:{ flex:1, fontSize:14, color:'#D1D5DB', fontWeight:'600' },
  sbDropdown:{ marginHorizontal:20, borderRadius:10, overflow:'hidden', marginBottom:4,
    backgroundColor:'rgba(255,255,255,0.05)' },
  sbDropdownItem:{ flexDirection:'row', alignItems:'center', justifyContent:'space-between',
    paddingHorizontal:14, paddingVertical:11 },
  sbDropdownText:{ fontSize:13, fontWeight:'600' },
  emptyWrap:{ alignItems:'center', marginTop:60, gap:12 },
  emptyText:{ fontSize:15 },
  card:{ borderRadius:14, padding:16, marginBottom:10, flexDirection:'row',
    alignItems:'center', shadowColor:'#000', shadowOffset:{width:0,height:2},
    shadowOpacity:0.06, shadowRadius:5, elevation:3 },
  roleChip:{ paddingHorizontal:8, paddingVertical:3, borderRadius:20 },
  roleText:{ fontSize:10, color:'#fff', fontWeight:'700' },
  name:{ fontSize:15, fontWeight:'700', marginBottom:2 },
  meta:{ fontSize:12, marginTop:1 },
  actions:{ flexDirection:'row', gap:8 },
  actionBtn:{ width:36, height:36, borderRadius:10, alignItems:'center',
    justifyContent:'center', backgroundColor:'rgba(30,181,58,0.08)' },
  fab:{ position:'absolute', bottom:24, right:20, flexDirection:'row',
    alignItems:'center', gap:8, backgroundColor: SprintColors.green,
    paddingHorizontal:18, paddingVertical:14, borderRadius:30,
    shadowColor:SprintColors.green, shadowOffset:{width:0,height:4},
    shadowOpacity:0.4, shadowRadius:8, elevation:8 },
  fabText:{ color:'#fff', fontWeight:'800', fontSize:14 },
  backdrop:{ flex:1, backgroundColor:'rgba(0,0,0,0.5)' },
  sheet:{ borderTopLeftRadius:20, borderTopRightRadius:20, padding:24, paddingBottom:40 },
  sheetTitle:{ fontSize:18, fontWeight:'800', marginBottom:16 },
  inputLabel:{ fontSize:13, fontWeight:'600', marginBottom:6 },
  input:{ height:48, borderWidth:1.5, borderRadius:10, paddingHorizontal:14,
    fontSize:15, marginBottom:14 },
  locGrid:{ flexDirection:'row', flexWrap:'wrap', gap:8, marginBottom:20 },
  locChip:{ paddingHorizontal:12, paddingVertical:7, borderRadius:20,
    backgroundColor:'rgba(30,181,58,0.08)', borderWidth:1.5,
    borderColor: SprintColors.green },
  locChipActive:{ backgroundColor: SprintColors.green },
  locChipText:{ fontSize:12, fontWeight:'600', color: SprintColors.green },
  saveBtn:{ height:52, backgroundColor: SprintColors.green, borderRadius:12,
    alignItems:'center', justifyContent:'center' },
  saveBtnText:{ color:'#fff', fontSize:15, fontWeight:'800' },
});

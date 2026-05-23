/**
 * ParkiPay — Vehicle Registry Screen (Admin/Supervisor only)
 *
 * Lists all registered vehicles, allows adding new ones (with SMS to owner)
 * and removing existing ones.
 */
import { useState, useEffect, useCallback } from 'react';
import {
  ActivityIndicator, Alert, FlatList, Modal, Pressable,
  SafeAreaView, StyleSheet, Text, TextInput,
  TouchableOpacity, View,
} from 'react-native';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useSettingsStore, palette } from '@/store/settingsStore';
import { vehicleRegistryService } from '@/services/api';
import { SprintColors } from '@/constants/theme';

interface Vehicle {
  id: number;
  plateNumber: string;
  ownerName: string;
  ownerPhone: string;
  make?: string;
  model?: string;
  category?: string;
  isValid?: boolean;
  createdAt: string;
}

const CATEGORIES = [
  { key: 'PRIVATE_CAR', label: 'Private Car' },
  { key: 'MOTORCYCLE',  label: 'Motorcycle' },
  { key: 'MINIBUS',     label: 'Minibus' },
  { key: 'BUS',         label: 'Bus' },
  { key: 'TRUCK',       label: 'Truck' },
  { key: 'GOVERNMENT',  label: 'Government' },
];

function formatPlate(raw: string): string {
  const s = raw.replace(/\s/g, '');
  if (s.length <= 1)  return s;
  if (s.length <= 4)  return s[0] + ' ' + s.slice(1);
  return s[0] + ' ' + s.slice(1, 4) + ' ' + s.slice(4);
}

export default function VehiclesScreen() {
  const { theme } = useSettingsStore();
  const C = palette(theme);
  const S = makeStyles(C);

  const [vehicles, setVehicles]     = useState<Vehicle[]>([]);
  const [loading,  setLoading]      = useState(true);
  const [showAdd,  setShowAdd]      = useState(false);
  const [saving,   setSaving]       = useState(false);

  // Form fields
  const [fOwnerName,  setFOwnerName]  = useState('');
  const [fPhone,      setFPhone]      = useState('');
  const [fPlate,      setFPlate]      = useState('');
  const [fMake,       setFMake]       = useState('');
  const [fModel,      setFModel]      = useState('');
  const [fCategory,   setFCategory]   = useState('PRIVATE_CAR');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await vehicleRegistryService.list();
      setVehicles(res.data);
    } catch { Alert.alert('Error', 'Failed to load vehicles'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const resetForm = () => {
    setFOwnerName(''); setFPhone(''); setFPlate('');
    setFMake(''); setFModel(''); setFCategory('PRIVATE_CAR');
  };

  const handleRegister = async () => {
    if (!fOwnerName.trim() || !fPhone.trim() || !fPlate.trim()) {
      Alert.alert('', 'Owner name, phone and plate number are required.'); return;
    }
    setSaving(true);
    try {
      await vehicleRegistryService.register({
        ownerName:  fOwnerName.trim(),
        ownerPhone: fPhone.trim(),
        plateNumber: fPlate.trim().toUpperCase(),
        make:     fMake.trim(),
        model:    fModel.trim(),
        category: fCategory,
      });
      setShowAdd(false);
      resetForm();
      load();
      Alert.alert('✓ Registered', 'Vehicle registered and SMS sent to owner.');
    } catch (e: any) {
      const detail = e?.response?.data?.detail ?? 'Registration failed.';
      Alert.alert('Error', detail);
    } finally { setSaving(false); }
  };

  const handleRemove = (v: Vehicle) => {
    Alert.alert('Remove Vehicle', `Remove ${formatPlate(v.plateNumber)} from registry?`, [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Remove', style: 'destructive', onPress: async () => {
        try { await vehicleRegistryService.remove(v.id); load(); }
        catch { Alert.alert('Error', 'Failed to remove vehicle.'); }
      }},
    ]);
  };

  const catLabel = (cat?: string) =>
    CATEGORIES.find(c => c.key === cat)?.label ?? 'Private Car';

  return (
    <SafeAreaView style={[S.root, { backgroundColor: C.bg }]}>
      {/* ── Header ────────────────────────────────────────────────────── */}
      <View style={[S.header, { backgroundColor: C.headerBg }]}>
        <TouchableOpacity onPress={() => router.back()} style={S.backBtn}>
          <Ionicons name="arrow-back" size={22} color="#fff" />
        </TouchableOpacity>
        <View>
          <Text style={S.headerTitle}>Vehicle Registry</Text>
          <Text style={S.headerSub}>{vehicles.length} registered vehicles</Text>
        </View>
        <View style={{ width: 38 }} />
      </View>

      {/* ── List ──────────────────────────────────────────────────────── */}
      {loading ? (
        <ActivityIndicator style={{ flex:1 }} color={SprintColors.green} size="large" />
      ) : (
        <FlatList
          data={vehicles}
          keyExtractor={v => String(v.id)}
          contentContainerStyle={{ padding:16, paddingBottom:100 }}
          ListEmptyComponent={
            <View style={S.emptyWrap}>
              <MaterialCommunityIcons name="car-off" size={52} color={C.textMuted} />
              <Text style={[S.emptyTitle, { color: C.textMuted }]}>No Registered Vehicles</Text>
              <Text style={[S.emptySub, { color: C.textMuted }]}>
                Tap the button below to register the first vehicle.
              </Text>
            </View>
          }
          renderItem={({ item: v }) => (
            <View style={[S.card, { backgroundColor: C.card }]}>
              {/* Plate */}
              <View style={[S.plateChip, { borderColor: SprintColors.green }]}>
                <Text style={[S.plateChipText, { color: C.text }]}>{formatPlate(v.plateNumber)}</Text>
              </View>

              <View style={S.cardBody}>
                <View style={{ flex:1 }}>
                  <Text style={[S.ownerName, { color: C.text }]}>{v.ownerName}</Text>
                  <Text style={[S.ownerPhone, { color: C.textSub }]}>
                    <Ionicons name="call-outline" size={12} /> {v.ownerPhone}
                  </Text>
                  <View style={S.tagRow}>
                    <View style={[S.catTag, { backgroundColor: 'rgba(30,181,58,0.1)' }]}>
                      <Text style={[S.catTagText, { color: SprintColors.green }]}>{catLabel(v.category)}</Text>
                    </View>
                    {(v.make || v.model) && (
                      <View style={[S.catTag, { backgroundColor: 'rgba(0,0,0,0.05)' }]}>
                        <Text style={[S.catTagText, { color: C.textSub }]}>
                          {[v.make, v.model].filter(Boolean).join(' ')}
                        </Text>
                      </View>
                    )}
                  </View>
                </View>

                <TouchableOpacity style={S.deleteBtn} onPress={() => handleRemove(v)}>
                  <Ionicons name="trash-outline" size={18} color="#EF4444" />
                </TouchableOpacity>
              </View>
            </View>
          )}
        />
      )}

      {/* ── FAB ────────────────────────────────────────────────────────── */}
      <TouchableOpacity style={S.fab} onPress={() => setShowAdd(true)}>
        <Ionicons name="car-outline" size={20} color="#fff" />
        <Text style={S.fabText}>Register Vehicle</Text>
      </TouchableOpacity>

      {/* ── Add Vehicle Modal ─────────────────────────────────────────── */}
      <Modal visible={showAdd} transparent animationType="slide" onRequestClose={() => setShowAdd(false)}>
        <Pressable style={S.backdrop} onPress={() => setShowAdd(false)} />
        <View style={[S.sheet, { backgroundColor: C.card }]}>
          <View style={S.sheetHandle} />
          <Text style={[S.sheetTitle, { color: C.text }]}>Register Vehicle</Text>

          {[
            { label: 'Owner Full Name *', value: fOwnerName, setter: setFOwnerName, placeholder: 'e.g. Juma Ally Hassan' },
            { label: 'Phone Number *',    value: fPhone,     setter: setFPhone,     placeholder: '+255 7XX XXX XXX', keyboardType: 'phone-pad' as any },
            { label: 'Plate Number *',    value: fPlate,     setter: setFPlate,     placeholder: 'T 882 DXZ', autoCapitalize: 'characters' as any },
            { label: 'Make (optional)',   value: fMake,      setter: setFMake,      placeholder: 'e.g. Toyota' },
            { label: 'Model (optional)',  value: fModel,     setter: setFModel,     placeholder: 'e.g. Corolla' },
          ].map(field => (
            <View key={field.label} style={{ marginBottom: 12 }}>
              <Text style={[S.inputLabel, { color: C.textSub }]}>{field.label}</Text>
              <TextInput
                style={[S.input, { color: C.text, borderColor: C.border, backgroundColor: C.bg }]}
                value={field.value}
                onChangeText={field.setter}
                placeholder={field.placeholder}
                placeholderTextColor={C.textMuted}
                keyboardType={field.keyboardType}
                autoCapitalize={field.autoCapitalize}
              />
            </View>
          ))}

          <Text style={[S.inputLabel, { color: C.textSub }]}>Vehicle Category</Text>
          <View style={S.catGrid}>
            {CATEGORIES.map(cat => (
              <TouchableOpacity key={cat.key}
                style={[S.catChip, fCategory === cat.key && S.catChipActive]}
                onPress={() => setFCategory(cat.key)}>
                <Text style={[S.catChipText, fCategory === cat.key && { color: '#fff' }]}>
                  {cat.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <View style={S.infoNote}>
            <Ionicons name="information-circle-outline" size={16} color={SprintColors.green} />
            <Text style={[S.infoNoteText, { color: C.textSub }]}>
              An SMS confirmation will be sent to the owner&apos;s phone number.
            </Text>
          </View>

          <TouchableOpacity style={[S.saveBtn, saving && { opacity: 0.6 }]}
            onPress={handleRegister} disabled={saving}>
            {saving
              ? <ActivityIndicator color="#fff" />
              : <>
                  <Ionicons name="checkmark-circle-outline" size={18} color="#fff" />
                  <Text style={S.saveBtnText}>Register Vehicle</Text>
                </>
            }
          </TouchableOpacity>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

function makeStyles(C: ReturnType<typeof palette>) {
  return StyleSheet.create({
    root:{ flex:1 },
    header:{ flexDirection:'row', alignItems:'center', justifyContent:'space-between',
      paddingHorizontal:16, paddingVertical:14 },
    backBtn:{ width:38, height:38, borderRadius:10, alignItems:'center', justifyContent:'center',
      backgroundColor:'rgba(255,255,255,0.1)' },
    headerTitle:{ fontSize:17, fontWeight:'800', color:'#fff', textAlign:'center' },
    headerSub:{ fontSize:11, color:'rgba(255,255,255,0.6)', textAlign:'center' },
    emptyWrap:{ alignItems:'center', marginTop:60, gap:10, paddingHorizontal:32 },
    emptyTitle:{ fontSize:16, fontWeight:'700' },
    emptySub:{ fontSize:13, textAlign:'center', lineHeight:20 },
    card:{ borderRadius:14, padding:14, marginBottom:10,
      shadowColor:'#000', shadowOffset:{width:0,height:2},
      shadowOpacity:0.06, shadowRadius:5, elevation:3 },
    plateChip:{ alignSelf:'flex-start', paddingHorizontal:14, paddingVertical:5,
      borderRadius:8, borderWidth:2, marginBottom:10 },
    plateChipText:{ fontSize:18, fontWeight:'900', letterSpacing:3 },
    cardBody:{ flexDirection:'row', alignItems:'flex-start' },
    ownerName:{ fontSize:15, fontWeight:'700', marginBottom:3 },
    ownerPhone:{ fontSize:12, marginBottom:6 },
    tagRow:{ flexDirection:'row', gap:6, flexWrap:'wrap' },
    catTag:{ paddingHorizontal:8, paddingVertical:3, borderRadius:20 },
    catTagText:{ fontSize:10, fontWeight:'700' },
    deleteBtn:{ width:36, height:36, borderRadius:10, alignItems:'center', justifyContent:'center',
      backgroundColor:'rgba(239,68,68,0.08)' },
    fab:{ position:'absolute', bottom:24, right:20, flexDirection:'row', alignItems:'center',
      gap:8, backgroundColor: SprintColors.green, paddingHorizontal:18, paddingVertical:14,
      borderRadius:30, shadowColor: SprintColors.green, shadowOffset:{width:0,height:4},
      shadowOpacity:0.4, shadowRadius:8, elevation:8 },
    fabText:{ color:'#fff', fontWeight:'800', fontSize:14 },
    backdrop:{ flex:1, backgroundColor:'rgba(0,0,0,0.5)' },
    sheet:{ borderTopLeftRadius:24, borderTopRightRadius:24, padding:24, paddingBottom:40,
      maxHeight:'92%' },
    sheetHandle:{ width:40, height:4, borderRadius:2, backgroundColor:'rgba(0,0,0,0.15)',
      alignSelf:'center', marginBottom:16 },
    sheetTitle:{ fontSize:19, fontWeight:'900', marginBottom:18 },
    inputLabel:{ fontSize:13, fontWeight:'600', marginBottom:6 },
    input:{ height:48, borderWidth:1.5, borderRadius:10, paddingHorizontal:14,
      fontSize:15, marginBottom:2 },
    catGrid:{ flexDirection:'row', flexWrap:'wrap', gap:8, marginBottom:14 },
    catChip:{ paddingHorizontal:12, paddingVertical:7, borderRadius:20,
      backgroundColor:'rgba(30,181,58,0.08)', borderWidth:1.5,
      borderColor: SprintColors.green },
    catChipActive:{ backgroundColor: SprintColors.green },
    catChipText:{ fontSize:12, fontWeight:'600', color: SprintColors.green },
    infoNote:{ flexDirection:'row', gap:8, padding:10, borderRadius:10,
      backgroundColor:'rgba(30,181,58,0.06)', borderLeftWidth:3,
      borderLeftColor: SprintColors.green, marginBottom:16, alignItems:'center' },
    infoNoteText:{ flex:1, fontSize:12 },
    saveBtn:{ height:54, backgroundColor: SprintColors.green, borderRadius:12,
      alignItems:'center', justifyContent:'center', flexDirection:'row', gap:10 },
    saveBtnText:{ color:'#fff', fontSize:15, fontWeight:'900' },
  });
}

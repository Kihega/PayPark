#!/usr/bin/env python3
"""
ParkiPay — mobile UX fixes (5 items)
=====================================

1. Register Vehicle form: Owner Full Name auto-capitalizes each word as
   typed and requires exactly three names (first, middle, surname).
   Plate Number field now uses the SAME format/validation as the
   attendant's Vehicle Lookup screen (T + 3 digits + 3 letters, live
   "T 000 AAA" grouping, red border on invalid partial input).

2. Add Officer form: Full Name gets the same auto-capitalize + three-name
   validation as (1).

4. The "SMS will be sent to owner" info note is removed from the Register
   Vehicle form AND from its own success modal. Instead, it now appears
   in the attendant's "Bill Generated!" success modal (lookup.tsx) as a
   proper info card, since that's the point an SMS is actually triggered
   (billing/generate, not vehicle registration).

5. "Admin Panel" -> "Supervisor Panel" (constants/i18n.ts, English only;
   the Swahili string already reads as "Supervisor's Panel").

Run from the REPO ROOT (the directory containing backend/ and mobile/):
    python3 patch_form_validation_and_ui.py
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT       = Path(".")
MOBILE     = ROOT / "mobile"
VEHICLES   = MOBILE / "app" / "(app)" / "vehicles.tsx"
ADMIN      = MOBILE / "app" / "(app)" / "admin.tsx"
LOOKUP     = MOBILE / "app" / "(app)" / "lookup.tsx"
I18N       = MOBILE / "constants" / "i18n.ts"


def fail(msg: str) -> None:
    print(f"❌ {msg}")
    sys.exit(1)


def must_contain(src: str, snippet: str, path: Path, what: str) -> None:
    if snippet not in src:
        fail(f"Could not find {what} in {path} — aborting, no changes made.")


# ── Shared name-formatting helper (inserted into both vehicles.tsx and admin.tsx) ──

NAME_HELPER = """
// ── Full-name formatting (shared pattern: title-case + 3-name check) ───────
// Auto-capitalizes each word as the user types, e.g. "juma ally hassan"
// -> "Juma Ally Hassan". Does not trim while typing (so trailing spaces
// while the user is still composing a word are preserved).
function formatFullName(raw: string): string {
  return raw.replace(/\\b\\w/g, (c) => c.toUpperCase());
}

// True only when the trimmed name has exactly 3 space-separated parts
// (first, middle, surname) and none of them are empty.
function isThreeNames(raw: string): boolean {
  const parts = raw.trim().split(/\\s+/).filter(Boolean);
  return parts.length === 3;
}
"""

PLATE_HELPER = """
// ── Plate helpers (matches attendant Vehicle Lookup screen exactly) ────────
// Tanzania: T + 3 digits + 3 uppercase letters  -> e.g. T000AAA
const PLATE_RE = /^T\\d{3}[A-Z]{3}$/;

function isPartialPlateValid(raw: string): boolean {
  if (raw.length === 0) return true;
  if (raw[0] !== 'T') return false;
  for (let i = 1; i < Math.min(raw.length, 4); i++) {
    if (!/\\d/.test(raw[i])) return false;
  }
  for (let i = 4; i < raw.length; i++) {
    if (!/[A-Z]/.test(raw[i])) return false;
  }
  return true;
}
"""


def patch_vehicles() -> None:
    if not VEHICLES.exists():
        fail(f"{VEHICLES} not found.")
    src = VEHICLES.read_text(encoding="utf-8")
    original = src

    # ── Insert shared helpers right after the existing formatPlate() (display fn) ──
    anchor = (
        "function formatPlate(raw: string): string {\n"
        "  const s = raw.replace(/\\s/g, '');\n"
        "  if (s.length <= 1)  return s;\n"
        "  if (s.length <= 4)  return s[0] + ' ' + s.slice(1);\n"
        "  return s[0] + ' ' + s.slice(1, 4) + ' ' + s.slice(4);\n"
        "}\n"
    )
    must_contain(src, anchor, VEHICLES, "formatPlate() helper")
    src = src.replace(anchor, anchor + NAME_HELPER + PLATE_HELPER)

    # ── Add live validation state next to the other form fields ────────────
    old_state = (
        "  const [fOwnerName,  setFOwnerName]  = useState('');\n"
        "  const [fPhone,      setFPhone]      = useState('');\n"
        "  const [fPlate,      setFPlate]      = useState('');\n"
    )
    must_contain(src, old_state, VEHICLES, "form state declarations")
    new_state = (
        "  const [fOwnerName,  setFOwnerName]  = useState('');\n"
        "  const [fPhone,      setFPhone]      = useState('');\n"
        "  const [fPlate,      setFPlate]      = useState('');\n"
        "  const [nameError,   setNameError]   = useState(false);\n"
        "  const [plateError,  setPlateError]  = useState(false);\n"
    )
    src = src.replace(old_state, new_state)

    # ── Reset the new error flags alongside the rest of the form ────────────
    old_reset = (
        "  const resetForm = () => {\n"
        "    setFOwnerName(''); setFPhone(''); setFPlate('');\n"
        "    setFMake(''); setFModel(''); setFCategory('PRIVATE_CAR');\n"
        "  };\n"
    )
    must_contain(src, old_reset, VEHICLES, "resetForm()")
    new_reset = (
        "  const resetForm = () => {\n"
        "    setFOwnerName(''); setFPhone(''); setFPlate('');\n"
        "    setFMake(''); setFModel(''); setFCategory('PRIVATE_CAR');\n"
        "    setNameError(false); setPlateError(false);\n"
        "  };\n"
    )
    src = src.replace(old_reset, new_reset)

    # ── handleRegister: validate 3-name + plate format before submitting ───
    old_handle_start = (
        "  const handleRegister = async () => {\n"
        "    if (!fOwnerName.trim() || !fPhone.trim() || !fPlate.trim()) {\n"
        "      Alert.alert('', 'Owner name, phone and plate number are required.'); return;\n"
        "    }\n"
        "    setSaving(true);\n"
        "    try {\n"
        "      await vehicleRegistryService.register({\n"
        "        ownerName:  fOwnerName.trim(),\n"
        "        ownerPhone: fPhone.trim(),\n"
        "        plateNumber: fPlate.trim().toUpperCase(),\n"
    )
    must_contain(src, old_handle_start, VEHICLES, "handleRegister() body")
    new_handle_start = (
        "  const handleRegister = async () => {\n"
        "    if (!fOwnerName.trim() || !fPhone.trim() || !fPlate.trim()) {\n"
        "      Alert.alert('', 'Owner name, phone and plate number are required.'); return;\n"
        "    }\n"
        "    if (!isThreeNames(fOwnerName)) {\n"
        "      setNameError(true);\n"
        "      Alert.alert('', 'Enter the owner\\'s full name as three names: first, middle, and surname.');\n"
        "      return;\n"
        "    }\n"
        "    const plateClean = fPlate.trim().toUpperCase().replace(/\\s/g, '');\n"
        "    if (!PLATE_RE.test(plateClean)) {\n"
        "      setPlateError(true);\n"
        "      Alert.alert('', 'Enter a valid plate number: T + 3 digits + 3 letters (e.g. T123ABC).');\n"
        "      return;\n"
        "    }\n"
        "    setSaving(true);\n"
        "    try {\n"
        "      await vehicleRegistryService.register({\n"
        "        ownerName:  fOwnerName.trim(),\n"
        "        ownerPhone: fPhone.trim(),\n"
        "        plateNumber: plateClean,\n"
    )
    src = src.replace(old_handle_start, new_handle_start)

    # ── Replace fLastRegisteredPlate assignment to use the cleaned value ───
    old_last_plate = "      setLastRegisteredPlate(fPlate.trim().toUpperCase());\n"
    must_contain(src, old_last_plate, VEHICLES, "setLastRegisteredPlate() call")
    src = src.replace(old_last_plate, "      setLastRegisteredPlate(plateClean);\n")

    # ── Replace the generic field-map rendering for Owner Name + Plate Number ──
    # The old version rendered ALL fields (including Owner Name and Plate
    # Number) from one generic array with no live validation. We pull those
    # two out into dedicated inputs with formatting/validation, and keep the
    # rest (phone, make, model) on the old generic path.
    old_fields_block = (
        "          {[\n"
        "            { label: 'Owner Full Name *', value: fOwnerName, setter: setFOwnerName, placeholder: 'e.g. Juma Ally Hassan' },\n"
        "            { label: 'Phone Number *',    value: fPhone,     setter: setFPhone,     placeholder: '+255 7XX XXX XXX', keyboardType: 'phone-pad' as any },\n"
        "            { label: 'Plate Number *',    value: fPlate,     setter: setFPlate,     placeholder: 'T 882 DXZ', autoCapitalize: 'characters' as any },\n"
        "            { label: 'Make (optional)',   value: fMake,      setter: setFMake,      placeholder: 'e.g. Toyota' },\n"
        "            { label: 'Model (optional)',  value: fModel,     setter: setFModel,     placeholder: 'e.g. Corolla' },\n"
        "          ].map(field => (\n"
        "            <View key={field.label} style={{ marginBottom: 12 }}>\n"
        "              <Text style={[S.inputLabel, { color: C.textSub }]}>{field.label}</Text>\n"
        "              <TextInput\n"
        "                style={[S.input, { color: C.text, borderColor: C.border, backgroundColor: C.bg }]}\n"
        "                value={field.value}\n"
        "                onChangeText={field.setter}\n"
        "                placeholder={field.placeholder}\n"
        "                placeholderTextColor={C.textMuted}\n"
        "                keyboardType={field.keyboardType}\n"
        "                autoCapitalize={field.autoCapitalize}\n"
        "              />\n"
        "            </View>\n"
        "          ))}\n"
    )
    must_contain(src, old_fields_block, VEHICLES, "generic form-fields render block")

    new_fields_block = (
        "          {/* Owner Full Name — auto-capitalize each word, require 3 names */}\n"
        "          <View style={{ marginBottom: 12 }}>\n"
        "            <Text style={[S.inputLabel, { color: C.textSub }]}>Owner Full Name *</Text>\n"
        "            <TextInput\n"
        "              style={[S.input, { color: C.text, backgroundColor: C.bg,\n"
        "                borderColor: nameError ? '#EF4444' : C.border }]}\n"
        "              value={fOwnerName}\n"
        "              onChangeText={(text) => {\n"
        "                const formatted = formatFullName(text);\n"
        "                setFOwnerName(formatted);\n"
        "                setNameError(formatted.length > 0 && !isThreeNames(formatted));\n"
        "              }}\n"
        "              placeholder=\"e.g. Juma Ally Hassan\"\n"
        "              placeholderTextColor={C.textMuted}\n"
        "              autoCapitalize=\"words\"\n"
        "            />\n"
        "            <Text style={[S.hintSmall, { color: nameError ? '#EF4444' : C.textMuted }]}>\n"
        "              Enter first, middle, and surname (e.g. Juma Ally Hassan)\n"
        "            </Text>\n"
        "          </View>\n"
        "\n"
        "          <View style={{ marginBottom: 12 }}>\n"
        "            <Text style={[S.inputLabel, { color: C.textSub }]}>Phone Number *</Text>\n"
        "            <TextInput\n"
        "              style={[S.input, { color: C.text, borderColor: C.border, backgroundColor: C.bg }]}\n"
        "              value={fPhone}\n"
        "              onChangeText={setFPhone}\n"
        "              placeholder=\"+255 7XX XXX XXX\"\n"
        "              placeholderTextColor={C.textMuted}\n"
        "              keyboardType=\"phone-pad\"\n"
        "            />\n"
        "          </View>\n"
        "\n"
        "          {/* Plate Number — same format/validation as attendant Vehicle Lookup */}\n"
        "          <View style={{ marginBottom: 12 }}>\n"
        "            <Text style={[S.inputLabel, { color: C.textSub }]}>Plate Number *</Text>\n"
        "            <TextInput\n"
        "              style={[S.input, { color: C.text, backgroundColor: C.bg,\n"
        "                borderColor: plateError ? '#EF4444' : C.border, letterSpacing: 2, fontWeight: '700' }]}\n"
        "              value={formatPlate(fPlate)}\n"
        "              onChangeText={(text) => {\n"
        "                const raw = text.replace(/\\s/g, '').toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 7);\n"
        "                setFPlate(raw);\n"
        "                setPlateError(raw.length > 0 && !isPartialPlateValid(raw));\n"
        "              }}\n"
        "              placeholder=\"T 000 AAA\"\n"
        "              placeholderTextColor={C.textMuted}\n"
        "              autoCapitalize=\"characters\"\n"
        "              autoCorrect={false}\n"
        "              maxLength={9}\n"
        "            />\n"
        "            <Text style={[S.hintSmall, { color: plateError ? '#EF4444' : C.textMuted }]}>\n"
        "              Format: T + 3 digits + 3 letters (e.g. T 566 GHH)\n"
        "            </Text>\n"
        "          </View>\n"
        "\n"
        "          {[\n"
        "            { label: 'Make (optional)',   value: fMake,      setter: setFMake,      placeholder: 'e.g. Toyota' },\n"
        "            { label: 'Model (optional)',  value: fModel,     setter: setFModel,     placeholder: 'e.g. Corolla' },\n"
        "          ].map(field => (\n"
        "            <View key={field.label} style={{ marginBottom: 12 }}>\n"
        "              <Text style={[S.inputLabel, { color: C.textSub }]}>{field.label}</Text>\n"
        "              <TextInput\n"
        "                style={[S.input, { color: C.text, borderColor: C.border, backgroundColor: C.bg }]}\n"
        "                value={field.value}\n"
        "                onChangeText={field.setter}\n"
        "                placeholder={field.placeholder}\n"
        "                placeholderTextColor={C.textMuted}\n"
        "              />\n"
        "            </View>\n"
        "          ))}\n"
    )
    src = src.replace(old_fields_block, new_fields_block)

    # ── Remove the SMS info note from the Register Vehicle form ────────────
    old_form_note = (
        "          <View style={S.infoNote}>\n"
        "            <Ionicons name=\"information-circle-outline\" size={16} color={SprintColors.green} />\n"
        "            <Text style={[S.infoNoteText, { color: C.textSub }]}>\n"
        "              An SMS confirmation will be sent to the owner&apos;s phone number.\n"
        "            </Text>\n"
        "          </View>\n"
        "\n"
    )
    must_contain(src, old_form_note, VEHICLES, "Register Vehicle form SMS info note")
    src = src.replace(old_form_note, "")

    # ── Remove the SMS note from the vehicle-registered success modal too ──
    old_success_note = (
        "            <View style={successStyles.noteRow}>\n"
        "              <Ionicons name=\"information-circle-outline\" size={16} color=\"#1EB53A\" />\n"
        "              <Text style={[successStyles.noteText, { color: C.textSub }]}>\n"
        "                The vehicle owner will receive an SMS when a parking bill is generated.\n"
        "              </Text>\n"
        "            </View>\n"
    )
    must_contain(src, old_success_note, VEHICLES, "vehicle-registered success modal SMS note")
    src = src.replace(old_success_note, "")

    # ── Add the small hint-text style used above ────────────────────────────
    old_input_style = (
        "    input:{ height:48, borderWidth:1.5, borderRadius:10, paddingHorizontal:14,\n"
        "      fontSize:15, marginBottom:2 },\n"
    )
    must_contain(src, old_input_style, VEHICLES, "input style definition")
    new_input_style = old_input_style + (
        "    hintSmall:{ fontSize:11, marginTop:5 },\n"
    )
    src = src.replace(old_input_style, new_input_style)

    if src == original:
        fail(f"No changes were made to {VEHICLES} — patch did not match.")
    VEHICLES.write_text(src, encoding="utf-8")
    print(f"✅ Patched {VEHICLES}")


def patch_admin() -> None:
    if not ADMIN.exists():
        fail(f"{ADMIN} not found.")
    src = ADMIN.read_text(encoding="utf-8")
    original = src

    # ── Insert the same name helper (admin.tsx doesn't have a plate field) ──
    anchor = (
        "const ROLE_COLORS: Record<string,string> = {\n"
        "  ATTENDANT: SprintColors.green, SUPERVISOR: '#1565C0',\n"
        "};\n"
    )
    must_contain(src, anchor, ADMIN, "ROLE_COLORS constant")
    src = src.replace(anchor, anchor + NAME_HELPER)

    # ── Add a nameError state next to the other Add Officer form state ─────
    old_state = "  const [newEmpId,  setNewEmpId]  = useState('');\n"
    must_contain(src, old_state, ADMIN, "newEmpId state declaration")
    src = src.replace(old_state, old_state + "  const [nameError,  setNameError]  = useState(false);\n")

    # ── Validate 3-name format in handleAdd before submitting ──────────────
    old_handle_add = (
        "  const handleAdd = async () => {\n"
        "    if (!newName.trim() || !newEmpId.trim()) return;\n"
        "    setSaving(true);\n"
        "    try {\n"
        "      await adminService.createOfficer({ fullName: newName.trim(),\n"
        "        employeeId: newEmpId.trim(), locationId: newLocId });\n"
        "      setShowAdd(false); setNewName(''); setNewEmpId(''); setNewLocId(null);\n"
        "      load();\n"
        "    } catch { /* silent */ }\n"
        "    finally { setSaving(false); }\n"
        "  };\n"
    )
    must_contain(src, old_handle_add, ADMIN, "handleAdd() body")
    new_handle_add = (
        "  const handleAdd = async () => {\n"
        "    if (!newName.trim() || !newEmpId.trim()) return;\n"
        "    if (!isThreeNames(newName)) {\n"
        "      setNameError(true);\n"
        "      return;\n"
        "    }\n"
        "    setSaving(true);\n"
        "    try {\n"
        "      await adminService.createOfficer({ fullName: newName.trim(),\n"
        "        employeeId: newEmpId.trim(), locationId: newLocId });\n"
        "      setShowAdd(false); setNewName(''); setNewEmpId(''); setNewLocId(null);\n"
        "      setNameError(false);\n"
        "      load();\n"
        "    } catch { /* silent */ }\n"
        "    finally { setSaving(false); }\n"
        "  };\n"
    )
    src = src.replace(old_handle_add, new_handle_add)

    # ── Replace the Full Name input with the formatted/validated version ───
    old_name_input = (
        "          <Text style={[S.inputLabel, { color: C.textSub }]}>{tr('officerName')}</Text>\n"
        "          <TextInput style={[S.input, { color: C.text, borderColor: C.border, backgroundColor: C.bg }]}\n"
        "            value={newName} onChangeText={setNewName} placeholder=\"e.g. Juma Ally\"\n"
        "            autoCapitalize=\"words\" placeholderTextColor={C.textMuted}/>\n"
    )
    must_contain(src, old_name_input, ADMIN, "officer name TextInput")
    new_name_input = (
        "          <Text style={[S.inputLabel, { color: C.textSub }]}>{tr('officerName')}</Text>\n"
        "          <TextInput\n"
        "            style={[S.input, { color: C.text, backgroundColor: C.bg,\n"
        "              borderColor: nameError ? '#EF4444' : C.border }]}\n"
        "            value={newName}\n"
        "            onChangeText={(text) => {\n"
        "              const formatted = formatFullName(text);\n"
        "              setNewName(formatted);\n"
        "              setNameError(formatted.length > 0 && !isThreeNames(formatted));\n"
        "            }}\n"
        "            placeholder=\"e.g. Juma Ally Hassan\"\n"
        "            autoCapitalize=\"words\"\n"
        "            placeholderTextColor={C.textMuted}\n"
        "          />\n"
        "          <Text style={[S.inputHintSmall, { color: nameError ? '#EF4444' : C.textSub }]}>\n"
        "            Enter first, middle, and surname (e.g. Juma Ally Hassan)\n"
        "          </Text>\n"
    )
    src = src.replace(old_name_input, new_name_input)

    # ── Add the small hint-text style ───────────────────────────────────────
    old_input_style = (
        "  input:{ height:48, borderWidth:1.5, borderRadius:10, paddingHorizontal:14,\n"
        "    fontSize:15, marginBottom:14 },\n"
    )
    must_contain(src, old_input_style, ADMIN, "input style definition")
    new_input_style = old_input_style + (
        "  inputHintSmall:{ fontSize:11, marginTop:-8, marginBottom:14 },\n"
    )
    src = src.replace(old_input_style, new_input_style)

    if src == original:
        fail(f"No changes were made to {ADMIN} — patch did not match.")
    ADMIN.write_text(src, encoding="utf-8")
    print(f"✅ Patched {ADMIN}")


def patch_lookup() -> None:
    if not LOOKUP.exists():
        fail(f"{LOOKUP} not found.")
    src = LOOKUP.read_text(encoding="utf-8")
    original = src

    # ── Upgrade the inline "SMS sent to owner" line into a proper info card ──
    old_success_text = (
        "            <Text style={[S.successSub,   { color: C.textSub }]}>\n"
        "              Parking bill issued successfully.\n"
        "              {vehicle?.ownerPhone ? ' SMS sent to owner.' : ''}\n"
        "            </Text>\n"
    )
    must_contain(src, old_success_text, LOOKUP, "bill-generated success modal subtext")
    new_success_block = (
        "            <Text style={[S.successSub,   { color: C.textSub }]}>\n"
        "              Parking bill issued successfully.\n"
        "            </Text>\n"
        "            {!!vehicle?.ownerPhone && (\n"
        "              <View style={S.smsNoteRow}>\n"
        "                <Ionicons name=\"information-circle-outline\" size={16} color={SprintColors.green} />\n"
        "                <Text style={[S.smsNoteText, { color: C.textSub }]}>\n"
        "                  An SMS confirmation has been sent to the owner&apos;s phone number.\n"
        "                </Text>\n"
        "              </View>\n"
        "            )}\n"
    )
    src = src.replace(old_success_text, new_success_block)

    # ── Add the smsNoteRow / smsNoteText styles next to successSub ─────────
    old_style_anchor = (
        "    successSub:      { fontSize: 13, textAlign: 'center', lineHeight: 20, marginBottom: 18 },\n"
    )
    must_contain(src, old_style_anchor, LOOKUP, "successSub style")
    new_style_anchor = old_style_anchor + (
        "    smsNoteRow:      { flexDirection: 'row', gap: 8, padding: 10, borderRadius: 10,\n"
        "      backgroundColor: 'rgba(30,181,58,0.06)', borderLeftWidth: 3,\n"
        "      borderLeftColor: SprintColors.green, marginBottom: 18, alignItems: 'flex-start', width: '100%' },\n"
        "    smsNoteText:     { flex: 1, fontSize: 12, lineHeight: 17 },\n"
    )
    src = src.replace(old_style_anchor, new_style_anchor)

    if src == original:
        fail(f"No changes were made to {LOOKUP} — patch did not match.")
    LOOKUP.write_text(src, encoding="utf-8")
    print(f"✅ Patched {LOOKUP}")


def patch_i18n() -> None:
    if not I18N.exists():
        fail(f"{I18N} not found.")
    src = I18N.read_text(encoding="utf-8")
    original = src

    old_line = "    adminPanel: 'Admin Panel', officers: 'Officers', addOfficer: 'Add Officer',\n"
    must_contain(src, old_line, I18N, "English adminPanel translation key")
    new_line = "    adminPanel: 'Supervisor Panel', officers: 'Officers', addOfficer: 'Add Officer',\n"
    src = src.replace(old_line, new_line)

    if src == original:
        fail(f"No changes were made to {I18N} — patch did not match.")
    I18N.write_text(src, encoding="utf-8")
    print(f"✅ Patched {I18N} (Admin Panel → Supervisor Panel)")


def main() -> None:
    if not MOBILE.is_dir():
        fail("mobile/ not found — run this script from the repo root.")

    patch_vehicles()
    patch_admin()
    patch_lookup()
    patch_i18n()

    # ── Commit ───────────────────────────────────────────────────────────
    subprocess.run(["git", "add", "-A"], check=True)
    result = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if result.returncode == 0:
        print("ℹ️  Nothing to commit.")
        return

    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            "feat(mobile): name auto-capitalize + 3-name validation on owner/officer "
            "forms, reuse lookup-screen plate format in vehicle registration, "
            "move SMS note to bill-generated success modal, rename Admin Panel "
            "to Supervisor Panel",
        ],
        check=True,
    )
    print("✅ Committed")
    print("\nNext: main is protected — push to a branch and open a PR:")
    print("    git checkout -b feat/form-validation-and-ui-fixes")
    print("    git push origin feat/form-validation-and-ui-fixes")


if __name__ == "__main__":
    main()

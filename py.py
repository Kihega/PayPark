#!/usr/bin/env python3
"""
ParkiPay — patch: SMS label rename + location dropdown selector
==================================================================
Fix 1 — SMS wording
--------------------
backend/src/routes/billing.js: renames the Swahili bill SMS's
"Namba ya Udhibiti" label to "Namba ya Malipo" (both the field label
and the matching lowercase reference in the payment-instruction
sentence). Nothing else changes — the underlying `controlNumber`
field/variable name, DB column, and English-language UI labels
("Control Number" in lookup.tsx/history.tsx) are untouched, since the
request was specifically about the SMS wording.

Fix 2 — Location picker UI
----------------------------
mobile/app/(app)/admin.tsx: replaces the two button-grid location
pickers (Add Officer form + Move Location sheet) — which just render
every DB location as a wrapped grid of chips — with a single reusable
`LocationSelect` component: a proper input-style field that shows the
selected location and opens a scrollable dropdown list on tap. This
scales cleanly as the location table grows, instead of an
ever-expanding wall of chips.

USAGE
-----
Run from the repository root (the folder containing `backend/` and
`mobile/`):

    python3 patch_sms_label_and_location_dropdown.py
"""
import os
import subprocess

ROOT = os.getcwd()


def path(*parts):
    return os.path.join(ROOT, *parts)


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def write(p, text):
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)


def require_in(text, needle, filename):
    if needle not in text:
        raise SystemExit(
            f"\n✗ Anchor text not found verbatim in {filename} — aborting to avoid "
            f"a bad patch (the file may already be patched or has diverged).\n"
            f"  Looking for:\n{needle[:200]}\n"
        )


def git_commit(message):
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    result = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT)
    if result.returncode == 0:
        print("  (no changes to commit — skipping)")
        return
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=ROOT, check=True)
    print(f"  ✓ committed: {message.splitlines()[0]}")


def check_repo():
    if not os.path.isdir(path("backend")) or not os.path.isdir(path("mobile")):
        raise SystemExit(
            "This doesn't look like the ParkiPay repo root "
            "(expected ./backend and ./mobile). Run from the repo root."
        )
    if not os.path.isdir(path(".git")):
        raise SystemExit("Not a git repository. Run this from inside your git checkout.")


# ═══════════════════════════════════════════════════════════════════════════
# STEP 1 — billing.js: "Namba ya Udhibiti" → "Namba ya Malipo"
# ═══════════════════════════════════════════════════════════════════════════
BILLING_OLD_BODY = """    `ParkiPay: Bili ya maegesho - ${locationName}\\n` +
    `Gari: ${plateNumber}\\n` +
    `Namba ya Udhibiti: ${controlNumber}\\n` +
    `Kiasi cha Kulipa: ${amountFmt}\\n` +
    `Muda wa Kutolewa: ${fmtDarEsSalaam(new Date(generatedAt))}\\n` +
    `Inaisha: ${fmtDarEsSalaam(new Date(expiresAt))}\\n` +
    `Lipa kupitia namba ya udhibiti hapo juu kabla ya muda kuisha. Asante kwa kutumia ParkiPay.`"""

BILLING_NEW_BODY = """    `ParkiPay: Bili ya maegesho - ${locationName}\\n` +
    `Gari: ${plateNumber}\\n` +
    `Namba ya Malipo: ${controlNumber}\\n` +
    `Kiasi cha Kulipa: ${amountFmt}\\n` +
    `Muda wa Kutolewa: ${fmtDarEsSalaam(new Date(generatedAt))}\\n` +
    `Inaisha: ${fmtDarEsSalaam(new Date(expiresAt))}\\n` +
    `Lipa kupitia namba ya malipo hapo juu kabla ya muda kuisha. Asante kwa kutumia ParkiPay.`"""


def step_01_sms_label():
    print("\n[1/2] backend/src/routes/billing.js — 'Namba ya Udhibiti' -> 'Namba ya Malipo'")
    p = path("backend/src/routes/billing.js")
    text = read(p)

    if "Namba ya Malipo" in text:
        print("  (already patched — skipping)")
        return

    require_in(text, BILLING_OLD_BODY, "billing.js (buildBillSms)")
    text = text.replace(BILLING_OLD_BODY, BILLING_NEW_BODY)

    assert "Namba ya Udhibiti" not in text
    assert "namba ya udhibiti" not in text
    assert "Namba ya Malipo" in text
    write(p, text)
    print(f"  patched {p}")
    git_commit("backend(billing): rename SMS label 'Namba ya Udhibiti' -> 'Namba ya Malipo'")


# ═══════════════════════════════════════════════════════════════════════════
# STEP 2 — admin.tsx: chip grid -> scrollable dropdown location select
# ═══════════════════════════════════════════════════════════════════════════
LOCATION_SELECT_COMPONENT = """
// ── Location dropdown (DB-driven, scrolls instead of wrapping into an
//    ever-growing grid of chips as more locations are added) ──────────────
function LocationSelect({
  locations, value, onSelect, placeholder, C, S,
}: {
  locations: Location[];
  value: number | null;
  onSelect: (id: number) => void;
  placeholder: string;
  C: any;
  S: any;
}) {
  const [open, setOpen] = useState(false);
  const selected = locations.find(l => l.id === value);

  return (
    <>
      <TouchableOpacity
        style={[S.input, S.selectField, { borderColor: C.border, backgroundColor: C.bg }]}
        onPress={() => setOpen(true)}
        activeOpacity={0.7}
      >
        <Text
          style={[S.selectFieldText, { color: selected ? C.text : C.textMuted }]}
          numberOfLines={1}
        >
          {selected ? selected.name : placeholder}
        </Text>
        <Ionicons name="chevron-down" size={18} color={C.textSub} />
      </TouchableOpacity>

      <Modal visible={open} transparent animationType="fade" onRequestClose={() => setOpen(false)}>
        <View style={S.selectModalCenter}>
          <Pressable style={StyleSheet.absoluteFill} onPress={() => setOpen(false)} />
          <View style={[S.selectDropdown, { backgroundColor: C.card }]}>
            <Text style={[S.selectDropdownTitle, { color: C.text }]}>{placeholder}</Text>
            <ScrollView
              style={S.selectDropdownScroll}
              showsVerticalScrollIndicator
              nestedScrollEnabled
              keyboardShouldPersistTaps="handled"
            >
              {locations.map(loc => (
                <TouchableOpacity
                  key={loc.id}
                  style={[S.selectOption, loc.id === value && S.selectOptionActive]}
                  onPress={() => { onSelect(loc.id); setOpen(false); }}
                >
                  <Text
                    style={[
                      S.selectOptionText,
                      { color: C.text },
                      loc.id === value && S.selectOptionTextActive,
                    ]}
                  >
                    {loc.name}
                  </Text>
                  {loc.id === value && (
                    <Ionicons name="checkmark" size={18} color={SprintColors.green} />
                  )}
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        </View>
      </Modal>
    </>
  );
}
"""

ADMIN_ANCHOR_BEFORE_DEFAULT_EXPORT = "const { width: W } = Dimensions.get('window');\nconst SIDEBAR_W    = W * 0.75;"

ADMIN_OLD_ADD_OFFICER_PICKER = """          <Text style={[S.inputLabel, { color: C.textSub }]}>{tr('selectLocation')}</Text>
          <View style={S.locGrid}>
            {locations.map(loc => (
              <TouchableOpacity key={loc.id}
                style={[S.locChip, newLocId === loc.id && S.locChipActive]}
                onPress={() => setNewLocId(loc.id)}>
                <Text style={[S.locChipText, newLocId === loc.id && { color:'#fff' }]}>
                  {loc.name}
                </Text>
              </TouchableOpacity>
            ))}
          </View>"""

ADMIN_NEW_ADD_OFFICER_PICKER = """          <Text style={[S.inputLabel, { color: C.textSub }]}>{tr('selectLocation')}</Text>
          <LocationSelect
            locations={locations}
            value={newLocId}
            onSelect={setNewLocId}
            placeholder={tr('selectLocation')}
            C={C}
            S={S}
          />"""

ADMIN_OLD_MOVE_PICKER = """          <Text style={[S.sheetTitle, { color: C.text }]}>
            {tr('moveLocation')}: {showMove?.fullName}
          </Text>
          <View style={S.locGrid}>
            {locations.map(loc => (
              <TouchableOpacity key={loc.id} style={S.locChip} onPress={() => handleMove(loc.id)}>
                <Text style={S.locChipText}>{loc.name}</Text>
              </TouchableOpacity>
            ))}
          </View>"""

ADMIN_NEW_MOVE_PICKER = """          <Text style={[S.sheetTitle, { color: C.text }]}>
            {tr('moveLocation')}: {showMove?.fullName}
          </Text>
          <Text style={[S.inputLabel, { color: C.textSub }]}>{tr('selectLocation')}</Text>
          <LocationSelect
            locations={locations}
            value={null}
            onSelect={handleMove}
            placeholder={tr('selectLocation')}
            C={C}
            S={S}
          />"""

ADMIN_OLD_LOC_STYLES = """  locGrid:{ flexDirection:'row', flexWrap:'wrap', gap:8, marginBottom:20 },
  locChip:{ paddingHorizontal:12, paddingVertical:7, borderRadius:20,
    backgroundColor:'rgba(30,181,58,0.08)', borderWidth:1.5,
    borderColor: SprintColors.green },
  locChipActive:{ backgroundColor: SprintColors.green },
  locChipText:{ fontSize: moderateScale(12), fontWeight:'600', color: SprintColors.green },"""

ADMIN_NEW_LOC_STYLES = """  // Location dropdown select
  selectField:{ flexDirection:'row', alignItems:'center', justifyContent:'space-between' },
  selectFieldText:{ fontSize: moderateScale(15), flex:1, marginRight:8 },
  selectModalCenter:{ flex:1, backgroundColor:'rgba(0,0,0,0.5)',
    alignItems:'center', justifyContent:'center', padding:24 },
  selectDropdown:{ width:'100%', maxWidth:420, maxHeight:'70%', borderRadius:16, padding:16,
    shadowColor:'#000', shadowOffset:{width:0,height:8}, shadowOpacity:0.2,
    shadowRadius:20, elevation:12 },
  selectDropdownTitle:{ fontSize: moderateScale(15), fontWeight:'800', marginBottom:10 },
  selectDropdownScroll:{ maxHeight:320 },
  selectOption:{ flexDirection:'row', alignItems:'center', justifyContent:'space-between',
    paddingVertical:12, paddingHorizontal:10, borderRadius:10 },
  selectOptionActive:{ backgroundColor:'rgba(30,181,58,0.08)' },
  selectOptionText:{ fontSize: moderateScale(14), fontWeight:'600' },
  selectOptionTextActive:{ color: SprintColors.green, fontWeight:'800' },"""


def step_02_location_dropdown():
    print("\n[2/2] mobile/app/(app)/admin.tsx — chip grid -> scrollable dropdown")
    p = path("mobile/app/(app)/admin.tsx")
    text = read(p)

    if "LocationSelect" in text:
        print("  (already patched — skipping)")
        return

    require_in(text, ADMIN_ANCHOR_BEFORE_DEFAULT_EXPORT, "admin.tsx (component insertion anchor)")
    text = text.replace(
        ADMIN_ANCHOR_BEFORE_DEFAULT_EXPORT,
        ADMIN_ANCHOR_BEFORE_DEFAULT_EXPORT + "\n" + LOCATION_SELECT_COMPONENT.rstrip("\n"),
        1,
    )

    require_in(text, ADMIN_OLD_ADD_OFFICER_PICKER, "admin.tsx (Add Officer location picker)")
    text = text.replace(ADMIN_OLD_ADD_OFFICER_PICKER, ADMIN_NEW_ADD_OFFICER_PICKER)

    require_in(text, ADMIN_OLD_MOVE_PICKER, "admin.tsx (Move Location picker)")
    text = text.replace(ADMIN_OLD_MOVE_PICKER, ADMIN_NEW_MOVE_PICKER)

    require_in(text, ADMIN_OLD_LOC_STYLES, "admin.tsx (locGrid/locChip styles)")
    text = text.replace(ADMIN_OLD_LOC_STYLES, ADMIN_NEW_LOC_STYLES)

    assert "locGrid" not in text and "locChip" not in text
    assert text.count("function LocationSelect") == 1
    assert text.count("<LocationSelect") == 2
    write(p, text)
    print(f"  patched {p}")
    git_commit(
        "mobile(admin): replace location chip-grid pickers with a scrollable "
        "dropdown select (Add Officer + Move Location)"
    )


# ═══════════════════════════════════════════════════════════════════════════
def main():
    check_repo()
    print("ParkiPay patch — SMS label rename + location dropdown selector")
    print("=" * 60)

    step_01_sms_label()
    step_02_location_dropdown()

    print("\n" + "=" * 60)
    print("✓ Done. Review with `git log --oneline` / `git show`.")
    print("  Push to a feature branch and open a PR (main is still protected).")


if __name__ == "__main__":
    main()

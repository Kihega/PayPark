#!/usr/bin/env python3
"""
ParkiPay patch — paypark_patch4.py

Covers four things:

1. RESPONSIVE LAYOUT
   Adds mobile/utils/responsive.ts (scale / verticalScale / moderateScale /
   getScreenSize helpers based on a 375x812 baseline) and wires global font
   scaling caps into the root layout so text and inputs shrink gracefully on
   small phones instead of being clipped. The Add-Officer and Add-Vehicle
   sheets (explicitly named in the request) are switched to use
   moderateScale() for their key font sizes/heights so they visibly adapt
   on small / medium / large screens.

2. ADD SUPERVISOR / ADD OFFICER / ADD VEHICLE FORMS
   - Officer "Full Name" and Vehicle "Owner Full Name" inputs are now
     force-capitalized as the user types (Title Case), instead of just
     hinting the keyboard with autoCapitalize.
   - Locations dropdown already pulled live from the DB (admin.tsx already
     calls adminService.listLocations()) — confirmed working, left as-is.
   - New officers already reappear in the list after creation (load() is
     called after a successful create) — confirmed working, left as-is.

3. ADD VEHICLE — SMS NOTICE RELOCATION
   Removes the blue "An SMS confirmation will be sent to the owner's phone
   number" note from the Add-Vehicle form (it described something that
   hadn't happened yet). The bill-generation success screen
   (mobile/app/(app)/lookup.tsx) already shows "SMS sent to owner." after a
   bill is actually generated — that is left untouched since it is already
   correctly placed.

4. LOCATIONS / ZONES SEED
   Rewrites backend/prisma/seed.js to:
     - Wipe all existing ParkingLocation / Officer / Vehicle / ControlNumber
       / AuditLog rows first (clean slate).
     - Seed 5 zones across different regions (Kinondoni, Ubungo, Temeke,
       Ilala, Kigamboni), each with 5 sample parking locations (25 total).
     - Re-create the two test officers:
         SUP-0001 (Supervisor) -> Kinondoni Zone
         TZ-0001  (Attendant)  -> Kinondoni - Mwenge Bus Stand (a location
                                   inside Kinondoni Zone)
     - Re-creates the sample vehicle TZ001ABC.

Usage:
    python3 paypark_patch4.py
Then:
    cd backend && npx prisma db seed
"""
import os
import sys

ROOT = os.getcwd()


def fail(msg):
    print(f"❌ {msg}")
    sys.exit(1)


def read(p):
    with open(p, "r", encoding="utf-8") as f:
        return f.read()


def write(p, c):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(c)


def patch_file(path, replacements, label):
    full = os.path.join(ROOT, path)
    if not os.path.isfile(full):
        print(f"⚠️  Skipping {label}: file not found at {path}")
        return
    content = read(full)
    original = content
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
    if content != original:
        write(full, content)
        print(f"✅ Patched {path}")
    else:
        print(f"ℹ️  No changes applied to {path} (already patched or pattern not found)")


def main():
    backend_dir = os.path.join(ROOT, "backend")
    mobile_dir = os.path.join(ROOT, "mobile")
    if not os.path.isdir(backend_dir) or not os.path.isdir(mobile_dir):
        fail("Could not find backend/ and mobile/ — run this from the project root.")

    # ── 1. Responsive utility ────────────────────────────────────────────────
    responsive_ts = """/**
 * ParkiPay — Responsive scaling helpers
 * Baseline device: 375x812 (iPhone 11/X-class). Scales paddings, font
 * sizes, and heights so content fits without clipping on small phones
 * (e.g. 320-360px wide) and doesn't look tiny on large/tablet screens.
 */
import { Dimensions, PixelRatio } from 'react-native';

const { width: SCREEN_W, height: SCREEN_H } = Dimensions.get('window');

const BASE_W = 375;
const BASE_H = 812;

export type ScreenSize = 'small' | 'medium' | 'large';

/** < 360px wide (e.g. iPhone SE / small Android) */
export const isSmallDevice = SCREEN_W < 360;
/** 360-414px wide (most modern phones) */
export const isMediumDevice = SCREEN_W >= 360 && SCREEN_W < 414;
/** >= 414px wide (Plus/Max phones, small tablets) */
export const isLargeDevice = SCREEN_W >= 414;

export function getScreenSize(): ScreenSize {
  if (isSmallDevice) return 'small';
  if (isMediumDevice) return 'medium';
  return 'large';
}

/** Horizontal scale — widths, paddings, gaps */
export function scale(size: number): number {
  return (SCREEN_W / BASE_W) * size;
}

/** Vertical scale — heights, vertical spacing */
export function verticalScale(size: number): number {
  return (SCREEN_H / BASE_H) * size;
}

/**
 * Moderate scale — best for font sizes. `factor` controls how aggressively
 * it scales (0 = no scaling, 1 = full linear scaling). 0.5 is a good
 * middle-ground default so text shrinks a little on small phones without
 * becoming unreadable.
 */
export function moderateScale(size: number, factor = 0.5): number {
  return size + (scale(size) - size) * factor;
}

/** Caps OS-level accessibility font scaling so layouts don't blow out. */
export const MAX_FONT_SCALE = 1.2;

/** Rounds to the nearest device pixel — avoids blurry borders/text. */
export function pixelRound(size: number): number {
  return PixelRatio.roundToNearestPixel(size);
}
"""
    write(os.path.join(mobile_dir, "utils", "responsive.ts"), responsive_ts)
    print("✅ Created mobile/utils/responsive.ts")

    # ── 2. Global font scaling cap in root layout ──────────────────────────
    layout_path = os.path.join(mobile_dir, "app", "_layout.tsx")
    if os.path.isfile(layout_path):
        content = read(layout_path)
        if "MAX_FONT_SCALE" not in content:
            content = content.replace(
                "import { View, ActivityIndicator } from 'react-native';\nimport { useAuthStore } from '@/store/authStore';",
                "import { View, ActivityIndicator, Text, TextInput } from 'react-native';\n"
                "import { useAuthStore } from '@/store/authStore';\n"
                "import { MAX_FONT_SCALE } from '@/utils/responsive';\n\n"
                "// Global responsive guard: cap OS-level font scaling so large\n"
                "// accessibility text settings don't blow out small-screen layouts,\n"
                "// while still letting our own moderateScale() drive normal sizing.\n"
                "// @ts-ignore - defaultProps exists at runtime on RN components\n"
                "(Text as any).defaultProps = (Text as any).defaultProps || {};\n"
                "(Text as any).defaultProps.maxFontSizeMultiplier = MAX_FONT_SCALE;\n"
                "// @ts-ignore\n"
                "(TextInput as any).defaultProps = (TextInput as any).defaultProps || {};\n"
                "(TextInput as any).defaultProps.maxFontSizeMultiplier = MAX_FONT_SCALE;",
            )
            write(layout_path, content)
            print("✅ Patched mobile/app/_layout.tsx (global font scaling cap)")
        else:
            print("ℹ️  mobile/app/_layout.tsx already has font scaling cap")
    else:
        print("⚠️  mobile/app/_layout.tsx not found, skipping")

    # ── 3. admin.tsx: capitalize name, responsive sheet/header sizes ───────
    patch_file(
        "mobile/app/(app)/admin.tsx",
        [
            (
                "import { SprintColors }              from '@/constants/theme';",
                "import { SprintColors }              from '@/constants/theme';\n"
                "import { moderateScale }             from '@/utils/responsive';\n\n"
                "// Capitalizes the first letter of every word as the user types\n"
                "// (e.g. \"juma ally\" -> \"Juma Ally\")\n"
                "function toTitleCase(s: string): string {\n"
                "  return s.replace(/\\w\\S*/g, (w) => w.charAt(0).toUpperCase() + w.slice(1));\n"
                "}",
            ),
            (
                "          <TextInput style={[S.input, { color: C.text, borderColor: C.border, backgroundColor: C.bg }]}\n"
                "            value={newName} onChangeText={setNewName} placeholder=\"e.g. Juma Ally\"\n"
                "            autoCapitalize=\"words\" placeholderTextColor={C.textMuted}/>",
                "          <TextInput style={[S.input, { color: C.text, borderColor: C.border, backgroundColor: C.bg }]}\n"
                "            value={newName} onChangeText={(v) => setNewName(toTitleCase(v))} placeholder=\"e.g. Juma Ally\"\n"
                "            autoCapitalize=\"words\" placeholderTextColor={C.textMuted}/>",
            ),
            (
                "  headerTitle:{ fontSize:18, fontWeight:'800', color:'#fff' },",
                "  headerTitle:{ fontSize: moderateScale(18), fontWeight:'800', color:'#fff' },",
            ),
            (
                "  sheetTitle:{ fontSize:18, fontWeight:'800', marginBottom:16 },\n"
                "  inputLabel:{ fontSize:13, fontWeight:'600', marginBottom:6 },\n"
                "  input:{ height:48, borderWidth:1.5, borderRadius:10, paddingHorizontal:14,\n"
                "    fontSize:15, marginBottom:14 },",
                "  sheetTitle:{ fontSize: moderateScale(18), fontWeight:'800', marginBottom:16 },\n"
                "  inputLabel:{ fontSize: moderateScale(13), fontWeight:'600', marginBottom:6 },\n"
                "  input:{ height: moderateScale(48), borderWidth:1.5, borderRadius:10, paddingHorizontal:14,\n"
                "    fontSize: moderateScale(15), marginBottom:14 },",
            ),
        ],
        "admin.tsx",
    )

    # ── 4. vehicles.tsx: capitalize owner name, remove SMS note, responsive sheet ──
    patch_file(
        "mobile/app/(app)/vehicles.tsx",
        [
            (
                "import { SprintColors } from '@/constants/theme';",
                "import { SprintColors } from '@/constants/theme';\n"
                "import { moderateScale } from '@/utils/responsive';\n\n"
                "function toTitleCase(s: string): string {\n"
                "  return s.replace(/\\w\\S*/g, (w) => w.charAt(0).toUpperCase() + w.slice(1));\n"
                "}",
            ),
            (
                "            { label: 'Owner Full Name *', value: fOwnerName, setter: setFOwnerName, placeholder: 'e.g. Juma Ally Hassan' },",
                "            { label: 'Owner Full Name *', value: fOwnerName,\n"
                "              setter: (v: string) => setFOwnerName(toTitleCase(v)),\n"
                "              placeholder: 'e.g. Juma Ally Hassan' },",
            ),
            (
                "          <View style={S.infoNote}>\n"
                "            <Ionicons name=\"information-circle-outline\" size={16} color={SprintColors.green} />\n"
                "            <Text style={[S.infoNoteText, { color: C.textSub }]}>\n"
                "              An SMS confirmation will be sent to the owner&apos;s phone number.\n"
                "            </Text>\n"
                "          </View>\n\n",
                "",
            ),
            (
                "    sheetTitle:{ fontSize:19, fontWeight:'900', marginBottom:18 },\n"
                "    inputLabel:{ fontSize:13, fontWeight:'600', marginBottom:6 },\n"
                "    input:{ height:48, borderWidth:1.5, borderRadius:10, paddingHorizontal:14,\n"
                "      fontSize:15, marginBottom:2 },",
                "    sheetTitle:{ fontSize: moderateScale(19), fontWeight:'900', marginBottom:18 },\n"
                "    inputLabel:{ fontSize: moderateScale(13), fontWeight:'600', marginBottom:6 },\n"
                "    input:{ height: moderateScale(48), borderWidth:1.5, borderRadius:10, paddingHorizontal:14,\n"
                "      fontSize: moderateScale(15), marginBottom:2 },",
            ),
            (
                "    headerTitle:{ fontSize:17, fontWeight:'800', color:'#fff', textAlign:'center' },",
                "    headerTitle:{ fontSize: moderateScale(17), fontWeight:'800', color:'#fff', textAlign:'center' },",
            ),
        ],
        "vehicles.tsx",
    )

    # ── 5. seed.js: clean-slate + zones + locations-per-zone ────────────────
    seed_path = os.path.join(backend_dir, "prisma", "seed.js")
    new_seed = """// ParkiPay — Development seed data
// Wipes existing data, then seeds 5 zones (5 parking locations each),
// two test officers, and one sample vehicle.
//
// ╔═══════════════════════════════════════════════════════════╗
// ║                   TEST USER CREDENTIALS                   ║
// ╠═══════════════════╦═════════════╦═════════════════════════╣
// ║ Role              ║ Employee ID ║ Password                ║
// ╠═══════════════════╬═════════════╬═════════════════════════╣
// ║ Attendant         ║ TZ-0001     ║ Officer@1234            ║
// ║ Supervisor        ║ SUP-0001    ║ Supervisor@1234         ║
// ╚═══════════════════╩═════════════╩═════════════════════════╝
//
// Run:  npm run db:seed

const { PrismaClient } = require('@prisma/client');
const bcrypt           = require('bcryptjs');

const prisma = new PrismaClient();

// 5 zones across different regions, each with 5 sample parking locations.
const ZONES = [
  {
    zoneName: 'Kinondoni Zone', region: 'Dar es Salaam', district: 'Kinondoni',
    locations: [
      'Kinondoni - Mwenge Bus Stand',
      'Kinondoni - Sinza Market',
      'Kinondoni - Magomeni Stand',
      'Kinondoni - Kawe Beach Parking',
      'Kinondoni - Makumbusho Terminal',
    ],
  },
  {
    zoneName: 'Ubungo Zone', region: 'Dar es Salaam', district: 'Ubungo',
    locations: [
      'Ubungo - Bus Terminal',
      'Ubungo - Kibo Stand',
      'Ubungo - Mabibo Market',
      'Ubungo - Manzese Stand',
      'Ubungo - Sayona Parking',
    ],
  },
  {
    zoneName: 'Temeke Zone', region: 'Dar es Salaam', district: 'Temeke',
    locations: [
      'Temeke - Mbagala Stand',
      'Temeke - Tandika Market',
      'Temeke - Buguruni Stand',
      'Temeke - Mtoni Parking',
      'Temeke - Chang\\'ombe Terminal',
    ],
  },
  {
    zoneName: 'Ilala Zone', region: 'Dar es Salaam', district: 'Ilala',
    locations: [
      'Ilala - Kariakoo Bus Stand',
      'Ilala - Buguruni Market',
      'Ilala - Ilala Boma Parking',
      'Ilala - Tabata Stand',
      'Ilala - Segerea Terminal',
    ],
  },
  {
    zoneName: 'Kigamboni Zone', region: 'Dar es Salaam', district: 'Kigamboni',
    locations: [
      'Kigamboni - Ferry Terminal',
      'Kigamboni - Tungi Beach Parking',
      'Kigamboni - Mjimwema Stand',
      'Kigamboni - Kibada Market',
      'Kigamboni - Vijibweni Stand',
    ],
  },
];

async function main() {
  console.log('🌱 Seeding development data...');

  // ── 0. Clean slate — remove all previous seed/test data ────────────────────
  // Order matters: clear FK-dependent tables first.
  await prisma.controlNumber.deleteMany({});
  await prisma.auditLog.deleteMany({});
  await prisma.officerBiometric.deleteMany({});
  await prisma.officer.deleteMany({});
  await prisma.vehicle.deleteMany({});
  await prisma.parkingLocation.deleteMany({});
  console.log('  🧹 Cleared previous seed data');

  // ── 1. Zones + parking locations ────────────────────────────────────────────
  // Each zone is itself a ParkingLocation (used for supervisor assignment),
  // and each zone's sample stands/markets are ParkingLocations too (used
  // for attendant assignment). All locations are looked up live by the
  // mobile app's location dropdown via GET /api/admin/locations/.
  const zoneRecords = {};      // zoneName -> ParkingLocation row (the zone itself)
  const firstLocationByZone = {}; // zoneName -> first location row inside it

  for (const zone of ZONES) {
    const zoneRow = await prisma.parkingLocation.create({
      data: {
        name:          zone.zoneName,
        region:        zone.region,
        district:      zone.district,
        feeMotorcycle: 500, feePrivateCar: 1000, feeMinibus: 2000,
        feeBus: 3000, feeTruck: 5000, feeGovernment: 0,
      },
    });
    zoneRecords[zone.zoneName] = zoneRow;
    console.log(`  ✅ Zone: ${zoneRow.name} (${zone.region})`);

    for (const locName of zone.locations) {
      const loc = await prisma.parkingLocation.create({
        data: {
          name:          locName,
          region:        zone.region,
          district:      zone.district,
          feeMotorcycle: 500, feePrivateCar: 1000, feeMinibus: 2000,
          feeBus: 3000, feeTruck: 5000, feeGovernment: 0,
        },
      });
      if (!firstLocationByZone[zone.zoneName]) firstLocationByZone[zone.zoneName] = loc;
      console.log(`     • ${loc.name}`);
    }
  }

  // ── 2. Sample vehicle ────────────────────────────────────────────────────────
  const vehicle = await prisma.vehicle.create({
    data: {
      plateNumber: 'TZ001ABC',
      ownerName:   'Juma Hassan',
      ownerPhone:  '+255712345678',
      ownerEmail:  'juma.hassan@example.com',
      make:        'Toyota',
      model:       'Corolla',
      color:       'White',
      year:        2018,
      category:    'PRIVATE_CAR',
    },
  });
  console.log(`  ✅ Sample vehicle: ${vehicle.plateNumber} (${vehicle.ownerName})`);

  // ── 3. Supervisor (test, SUP-XXXX format) — assigned to Kinondoni Zone ──────
  const supervisor = await prisma.officer.create({
    data: {
      employeeId:   'SUP-0001',
      fullName:     'Test Supervisor',
      phone:        '+255700000002',
      email:        'supervisor@parkipay.go.tz',
      role:         'SUPERVISOR',
      passwordHash: await bcrypt.hash('Supervisor@1234', 12),
      locationId:   zoneRecords['Kinondoni Zone'].id,
    },
  });
  console.log(`  ✅ Supervisor: ${supervisor.employeeId} (password: Supervisor@1234) -> Kinondoni Zone`);

  // ── 4. Attendant (TZ-XXXX format) — assigned to a stand inside Kinondoni ───
  const attendantLocation = firstLocationByZone['Kinondoni Zone'];
  const attendant = await prisma.officer.create({
    data: {
      employeeId:   'TZ-0001',
      fullName:     'John Mwangi',
      phone:        '+255712345678',
      email:        'j.mwangi@parkipay.go.tz',
      role:         'ATTENDANT',
      passwordHash: await bcrypt.hash('Officer@1234', 12),
      locationId:   attendantLocation.id,
    },
  });
  console.log(`  ✅ Attendant: ${attendant.employeeId} (password: Officer@1234) -> ${attendantLocation.name}`);

  console.log('\\n🎉 Seed complete. You can log in with:');
  console.log('   Attendant:   TZ-0001    / Officer@1234');
  console.log('   Supervisor:  SUP-0001   / Supervisor@1234');
  console.log(`\\n   Seeded ${ZONES.length} zones x 5 locations each = ${ZONES.length * 5} parking locations.`);
}

main()
  .catch((err) => {
    console.error('❌ Seed failed:', err);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
"""
    write(seed_path, new_seed)
    print("✅ Rewrote backend/prisma/seed.js (clean-slate zones + locations seed)")

    print()
    print("🎉 Patch 4 applied.")
    print()
    print("Next steps:")
    print("  cd backend")
    print("  npx prisma db seed")
    print()
    print("Notes / things confirmed already correct and left untouched:")
    print("  - Add Officer location dropdown already pulls live from")
    print("    GET /api/admin/locations/ (no hardcoded list).")
    print("  - New officers/vehicles already reappear in their lists right")
    print("    after creation (load() is called post-save).")
    print("  - Bill-generation success screen (lookup.tsx) already shows the")
    print("    'SMS sent to owner' note — that's the correct place for it.")
    print("  - Full responsive refactor of every screen's exact pixel values")
    print("    is out of scope for one patch; this patch lays the scaling")
    print("    foundation (mobile/utils/responsive.ts + global font cap) and")
    print("    applies it to the two forms named in the request. Apply")
    print("    moderateScale()/scale() the same way in other screens as needed.")


if __name__ == "__main__":
    main()

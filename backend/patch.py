#!/usr/bin/env python3
"""
Patch: seed.js — support new TZ-XXXX / SUP-XXXX login ID format

Context: the login screen now requires IDs in the form TZ-XXXX (attendant)
or SUP-XXXX (supervisor). The backend route (/api/auth/login/) doesn't
care about ID format — it just looks up whatever string is sent — so the
real gap is that no seeded officer actually has a TZ-XXXX employeeId, and
the one SUP-XXXX row (SUP-0001) is missing passwordHash, which crashes
the seed before it finishes.

This patch:
  1. Fixes OfficerRole enum mismatches — schema.prisma defines
     FIELD_OFFICER / SUPERVISOR / ADMIN, not ATTENDANT. (ATTENDANT would
     throw a PrismaClientValidationError, same shape as the earlier
     passwordHash bug.)
  2. Adds passwordHash to the SUP-0001 supervisor block.
  3. Adds a new TZ-0001 officer (role: FIELD_OFFICER) so the new ID
     format has something real to authenticate against locally.
  4. Leaves ADMIN001 / OFF001 (legacy IDs) untouched — your memory note
     says attendant IDs must keep the TZ-XXXX shape going forward, but
     doesn't say to delete the legacy rows, so this patch is additive
     only and won't break anything already relying on ADMIN001/OFF001.

Run from the repo root (the dir containing prisma/seed.js):
    python3 patch_seed_login_format.py
"""
import re
import subprocess
import sys
from pathlib import Path

SEED_PATH = Path("prisma/seed.js")


def fail(msg: str) -> None:
    print(f"❌ {msg}")
    sys.exit(1)


def main() -> None:
    if not SEED_PATH.exists():
        fail(f"{SEED_PATH} not found. Run this from the backend project root.")

    src = SEED_PATH.read_text(encoding="utf-8")
    original = src

    # ── 1. Fix the broken SUP-0001 block: add passwordHash ──────────────────
    broken_supervisor = re.search(
        r"  // ── Supervisor \(test\) ──.*?\n"
        r"  const supervisor = await prisma\.officer\.upsert\(\{\n"
        r"    where:  \{ employeeId: 'SUP-0001' \},\n"
        r"    update: \{\},\n"
        r"    create: \{\n"
        r"      employeeId:   'SUP-0001',\n"
        r"      fullName:     'Test Supervisor',\n"
        r"      phone:        '\+255700000002',\n"
        r"      email:        'supervisor@parkipay\.go\.tz',\n"
        r"      role:         'SUPERVISOR',\n"
        r"      locationId:   dar\.id,\n"
        r"    \},\n"
        r"  \}\);\n"
        r"  console\.log\(`  ✅ Supervisor: \$\{supervisor\.employeeId\} \(\$\{supervisor\.fullName\}\)`\);\n",
        src,
    )
    if not broken_supervisor:
        fail("Could not find the SUP-0001 block — aborting, no changes made.")

    fixed_supervisor = (
        "  // ── Supervisor (test, SUP-XXXX format) ───────────────────────────────────\n"
        "  const supervisor = await prisma.officer.upsert({\n"
        "    where:  { employeeId: 'SUP-0001' },\n"
        "    update: {},\n"
        "    create: {\n"
        "      employeeId:   'SUP-0001',\n"
        "      fullName:     'Test Supervisor',\n"
        "      phone:        '+255700000002',\n"
        "      email:        'supervisor@parkipay.go.tz',\n"
        "      role:         'SUPERVISOR',\n"
        "      passwordHash: await bcrypt.hash('Supervisor@1234', 12),\n"
        "      locationId:   dar.id,\n"
        "    },\n"
        "  });\n"
        "  console.log(`  ✅ Supervisor: ${supervisor.employeeId} (password: Supervisor@1234)`);\n"
    )
    src = src.replace(broken_supervisor.group(0), fixed_supervisor)

    # ── 2. Add a new TZ-0001 attendant block right after the supervisor ────
    #     role must be FIELD_OFFICER per schema.prisma's OfficerRole enum —
    #     ATTENDANT is not a valid value and would crash the same way.
    insertion_point = fixed_supervisor
    new_attendant_block = (
        "\n  // ── Attendant (test, TZ-XXXX format) ─────────────────────────────────────\n"
        "  const attendant = await prisma.officer.upsert({\n"
        "    where:  { employeeId: 'TZ-0001' },\n"
        "    update: {},\n"
        "    create: {\n"
        "      employeeId:   'TZ-0001',\n"
        "      fullName:     'Test Attendant',\n"
        "      phone:        '+255700000004',\n"
        "      email:        'attendant@parkipay.go.tz',\n"
        "      role:         'FIELD_OFFICER',\n"
        "      passwordHash: await bcrypt.hash('Attendant@1234', 12),\n"
        "      locationId:   dar.id,\n"
        "    },\n"
        "  });\n"
        "  console.log(`  ✅ Attendant: ${attendant.employeeId} (password: Attendant@1234)`);\n"
    )
    src = src.replace(insertion_point, insertion_point + new_attendant_block)

    # ── 3. Update the closing summary console.log block ────────────────────
    old_summary = re.search(
        r"  console\.log\('\\n🎉 Seed complete\. You can log in with:'\);\n"
        r"  console\.log\('   Admin:         ADMIN001   / Admin@1234'\);\n"
        r"  console\.log\('   Field Officer: OFF001     / Officer@1234'\);\n",
        src,
    )
    if not old_summary:
        fail("Could not find closing summary block — aborting, no changes made.")
    new_summary = (
        "  console.log('\\n🎉 Seed complete. You can log in with:');\n"
        "  console.log('   Admin (legacy):    ADMIN001   / Admin@1234');\n"
        "  console.log('   Field Off (legacy):OFF001     / Officer@1234');\n"
        "  console.log('   Supervisor:        SUP-0001   / Supervisor@1234');\n"
        "  console.log('   Attendant:         TZ-0001    / Attendant@1234');\n"
    )
    src = src.replace(old_summary.group(0), new_summary)

    # ── 4. Update the credentials banner comment at the top ────────────────
    old_banner = (
        "// ╔═══════════════════════════════════════════════════════════╗\n"
        "// ║                   TEST USER CREDENTIALS                   ║\n"
        "// ╠═══════════════════╦═════════════╦═════════════════════════╣\n"
        "// ║ Role              ║ Employee ID ║ Password                ║\n"
        "// ╠═══════════════════╬═════════════╬═════════════════════════╣\n"
        "// ║ Admin             ║ ADMIN001    ║ Admin@1234              ║\n"
        "// ║ Field Officer     ║ OFF001      ║ Officer@1234            ║\n"
        "// ╚═══════════════════╩═════════════╩═════════════════════════╝\n"
    )
    new_banner = (
        "// ╔═══════════════════════════════════════════════════════════╗\n"
        "// ║                   TEST USER CREDENTIALS                   ║\n"
        "// ╠═══════════════════╦═════════════╦═════════════════════════╣\n"
        "// ║ Role              ║ Employee ID ║ Password                ║\n"
        "// ╠═══════════════════╬═════════════╬═════════════════════════╣\n"
        "// ║ Admin (legacy)    ║ ADMIN001    ║ Admin@1234              ║\n"
        "// ║ Field Off (legacy)║ OFF001      ║ Officer@1234            ║\n"
        "// ║ Supervisor        ║ SUP-0001    ║ Supervisor@1234         ║\n"
        "// ║ Attendant         ║ TZ-0001     ║ Attendant@1234          ║\n"
        "// ╚═══════════════════╩═════════════╩═════════════════════════╝\n"
    )
    if old_banner not in src:
        fail("Could not find credentials banner comment — aborting, no changes made.")
    src = src.replace(old_banner, new_banner)

    if src == original:
        fail("No changes were made — patch did not match expected source.")

    SEED_PATH.write_text(src, encoding="utf-8")
    print(f"✅ Patched {SEED_PATH}")

    # ── Commit ───────────────────────────────────────────────────────────
    subprocess.run(["git", "add", str(SEED_PATH)], check=True)
    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            "fix(seed): add passwordHash to SUP-0001, seed TZ-0001 attendant "
            "for new login ID format, keep legacy ADMIN001/OFF001 intact",
        ],
        check=True,
    )
    print("✅ Committed")


if __name__ == "__main__":
    main()


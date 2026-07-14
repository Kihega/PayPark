#!/usr/bin/env python3
"""
ParkiPay — patch: drop the registration SMS, keep only the bill SMS
======================================================================
Vehicle registration used to send its own SMS ("Gari lako
limesajiliwa...") in addition to the bill SMS sent later when a bill
is generated — two messages per vehicle lifecycle, and the
registration one had a silent-failure problem (see below). This patch
removes it entirely: registration just creates the record now, and
the bill SMS (already sent from billing.js, with the full amount /
control number / expiry) becomes the only SMS ParkiPay ever sends.

WHY THE REGISTRATION SMS WASN'T RELIABLY REACHING OWNERS
------------------------------------------------------------
admin.js awaited sendSMS() and returned `smsSent: true/false` in the
API response — but nothing in the mobile app (vehicles.tsx) ever read
that field. So if a send failed, the officer still saw "Vehicle
registered" with no indication the SMS didn't go out. Different
officers entering phone numbers in different formats (with/without
+255, spaces, leading 0) made this worse before number normalization
existed. Removing this SMS removes the whole failure class — the
only SMS ParkiPay sends now is the bill SMS, using the same
validated/normalized number, with visible server-side logging
(`[SMS] Meseji POST /sms/send -> HTTP ...`) if it ever fails.

WHAT THIS PATCH DOES
----------------------
1. backend/src/routes/admin.js — removes the SMS send from vehicle
   registration (`POST /api/admin/vehicles/`). The endpoint still
   validates + normalizes + stores ownerPhone exactly as before; it
   just no longer texts the owner at this step. Drops the now-unused
   `sendSMS` import so ESLint's no-unused-vars doesn't flag it in CI.
2. mobile/app/(app)/vehicles.tsx — updates a stale doc comment that
   referenced "with SMS to owner" on the registration screen (no
   functional UI change was needed — the mobile app never displayed
   anything about the registration SMS in the first place).

USAGE
-----
Run from the repository root (the folder containing `backend/` and
`mobile/`):

    python3 patch_remove_registration_sms.py
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
# STEP 1 — admin.js: drop the registration SMS
# ═══════════════════════════════════════════════════════════════════════════
ADMIN_OLD_IMPORTS = """const { sendSMS } = require('../lib/sms');
const { isValidTzMobile, normalizeTzMobile } = require('../lib/phone');
const { authenticate } = require('../middleware/auth');"""

ADMIN_NEW_IMPORTS = """const { isValidTzMobile, normalizeTzMobile } = require('../lib/phone');
const { authenticate } = require('../middleware/auth');"""

ADMIN_OLD_HANDLER_TAIL = """    // Invalidate any cached lookup for this plate
    await redis.cacheDel(`vehicle:${plateNumber}`);

    // Send SMS to owner with registration confirmation
    const smsText =
      `ParkiPay: Gari lako (${plateNumber}) limesajiliwa kwenye mfumo wa maegesho. ` +
      `Utapokea SMS yenye maelezo kamili ya bili kila utakapotozwa maegesho. Asante!`;
    const smsResult = await sendSMS(ownerPhone, smsText);
    if (!smsResult.success) {
      console.warn('[Admin] Vehicle registered but SMS failed:', smsResult.error);
    }

    res.status(201).json({ ...vehicle, smsSent: smsResult.success });"""

ADMIN_NEW_HANDLER_TAIL = """    // Invalidate any cached lookup for this plate
    await redis.cacheDel(`vehicle:${plateNumber}`);

    // No SMS here by design — ParkiPay sends exactly one SMS per bill
    // (see backend/src/routes/billing.js), not a separate registration
    // confirmation. Keeping it to a single message avoids the owner
    // getting two texts, and removes the silent-failure gap where a
    // failed registration SMS previously went unnoticed by the officer.
    res.status(201).json(vehicle);"""


def step_01_admin_js():
    print("\n[1/2] backend/src/routes/admin.js — drop registration SMS")
    p = path("backend/src/routes/admin.js")
    text = read(p)

    if "sendSMS" not in text:
        print("  (already patched — skipping)")
        return

    require_in(text, ADMIN_OLD_IMPORTS, "admin.js (imports)")
    text = text.replace(ADMIN_OLD_IMPORTS, ADMIN_NEW_IMPORTS)

    require_in(text, ADMIN_OLD_HANDLER_TAIL, "admin.js (registration handler tail)")
    text = text.replace(ADMIN_OLD_HANDLER_TAIL, ADMIN_NEW_HANDLER_TAIL)

    assert "sendSMS" not in text, "sendSMS should be fully removed from admin.js"
    assert "smsSent" not in text
    write(p, text)
    print(f"  patched {p}")
    git_commit(
        "backend(admin): stop sending a registration SMS — the bill SMS is now the "
        "only message ParkiPay sends per vehicle"
    )


# ═══════════════════════════════════════════════════════════════════════════
# STEP 2 — vehicles.tsx: stale doc-comment cleanup
# ═══════════════════════════════════════════════════════════════════════════
VEHICLES_OLD_COMMENT = " * Lists all registered vehicles, allows adding new ones (with SMS to owner)"
VEHICLES_NEW_COMMENT = " * Lists all registered vehicles, allows adding new ones"


def step_02_vehicles_tsx():
    print("\n[2/2] mobile/app/(app)/vehicles.tsx — update stale doc comment")
    p = path("mobile/app/(app)/vehicles.tsx")
    text = read(p)

    if VEHICLES_OLD_COMMENT not in text:
        print("  (already patched or comment not found — skipping)")
        return

    text = text.replace(VEHICLES_OLD_COMMENT, VEHICLES_NEW_COMMENT)
    write(p, text)
    print(f"  patched {p}")
    git_commit("mobile(vehicles): update doc comment — registration no longer sends an SMS")


# ═══════════════════════════════════════════════════════════════════════════
def main():
    check_repo()
    print("ParkiPay patch — remove registration SMS (bill SMS only)")
    print("=" * 60)

    step_01_admin_js()
    step_02_vehicles_tsx()

    print("\n" + "=" * 60)
    print("✓ Done. Review with `git log --oneline` / `git show`.")
    print("  Push to a feature branch and open a PR (main is still protected).")
    print("\n  Net effect: ParkiPay now sends exactly one SMS per vehicle —")
    print("  the full bill SMS from billing.js — instead of a registration")
    print("  text plus a separate bill text.")


if __name__ == "__main__":
    main()

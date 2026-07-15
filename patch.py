#!/usr/bin/env python3
"""
ParkiPay — patch: approved sender ID + remove CI auto-merge
===============================================================
Covers 4 requested fixes; #2 and #3 needed verification, not code
changes (see notes below).

Fix 1 — use the approved 'PARKIPAY' sender ID
------------------------------------------------
Your Meseji sender ID request for "PARKIPAY" has been approved. This
switches the default in backend/src/config/index.js and
backend/.env.example from the fallback 'MESEJI' sender to 'PARKIPAY'.
(You can still override with the MESEJI_SENDER_ID env var on Render —
this just changes what happens when that var is unset.)

Fix 2 — only one SMS per bill (already true, verified not changed)
----------------------------------------------------------------------
Checked: `sendSMS(` has exactly one call site in the whole backend —
backend/src/routes/billing.js. The registration-time SMS was already
removed in an earlier patch. This script re-asserts that invariant
and fails loudly if it's ever violated again, but makes no file
changes for this item since it's already correct.

Fix 3 — end-to-end connectivity audit (verified, no changes needed)
-------------------------------------------------------------------
Traced the full chain and confirmed every hop lines up:
  mobile lookup.tsx
    -> billingService.generate(plate, locationId)          [services/api.ts]
    -> POST {API_BASE_URL}/api/billing/generate/            [constants/api.ts]
  backend app.js: app.use('/api/billing/', billing route)
  billing.js: router.post('/generate/', ...)
    body validated against { plate_number, location_id }    (matches mobile's payload)
    -> buildBillSms() -> sendSMS() -> lib/sms.js
    -> POST https://meseji.co.tz/api/v1/sms/send
       header: x-api-key: <MESEJI_API_KEY>
       body:   { sender_id, message, contacts: "255XXXXXXXXX" }
No mismatches found (route paths, field names, and the Meseji
request shape all check out). sendSMS() is intentionally
fire-and-forget from billing.js (`.catch()`, not awaited) so bill
generation doesn't wait on SMS latency — that's by design, not a bug.
No code change was needed for this item.

Fix 4 — remove CI auto-merge, go back to manual PR + manual merge
----------------------------------------------------------------------
Removes the `promote-to-main` job entirely from both
.github/workflows/backend-ci.yml and mobile-ci.yml. CI now stops
after lint/security-audit/test (backend) or lint/type-check/test
(mobile) — nothing touches `main` automatically anymore. The
`pull_request: branches: [develop, main]` trigger added earlier is
KEPT on purpose: it means when you manually open a develop -> main PR
in the browser, the same checks run again on that PR itself, so
you'll see green checks right there before you click merge yourself.
Also removes the now-unused GH_PAT requirement noted in each
workflow's header comment, since nothing in these files calls `gh`
anymore.

USAGE
-----
Run from the repository root (the folder containing `backend/`,
`mobile/`, and `.github/`):

    python3 patch_sender_id_and_manual_merge.py
"""
import os
import re
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
# STEP 1 — approved 'PARKIPAY' sender ID
# ═══════════════════════════════════════════════════════════════════════════
CONFIG_OLD = """    // 'MESEJI' is the pre-approved default sender every account gets.
    // Switch to 'ParkiPay' once that sender ID is requested + approved
    // (POST /sms/request-sender-id in the Meseji dashboard/API).
    senderId: process.env.MESEJI_SENDER_ID || 'MESEJI',"""

CONFIG_NEW = """    // 'PARKIPAY' was requested via POST /sms/request-sender-id and has
    // since been approved in the Meseji dashboard — safe to use as the
    // default. Still overridable via MESEJI_SENDER_ID if that ever changes.
    senderId: process.env.MESEJI_SENDER_ID || 'PARKIPAY',"""

ENV_OLD = """# 'MESEJI' is the pre-approved default sender ID. Switch to 'ParkiPay' once
# that custom sender ID has been requested + approved in the dashboard.
MESEJI_SENDER_ID=MESEJI"""

ENV_NEW = """# 'PARKIPAY' is the approved sender ID for this account (approved via
# the Meseji dashboard's sender-ID request flow).
MESEJI_SENDER_ID=PARKIPAY"""

SMS_JS_OLD = """ * Optional env vars:
 *   MESEJI_SENDER_ID → Sender name shown on the recipient's phone.
 *                       Defaults to 'MESEJI', the pre-approved
 *                       default sender every account gets. A custom
 *                       sender ID (e.g. 'ParkiPay') must be requested
 *                       via POST /sms/request-sender-id and approved
 *                       in the Meseji dashboard before it can be used
 *                       here — set MESEJI_SENDER_ID once it's live."""

SMS_JS_NEW = """ * Optional env vars:
 *   MESEJI_SENDER_ID → Sender name shown on the recipient's phone.
 *                       Defaults to 'PARKIPAY', this account's
 *                       approved sender ID. Override with
 *                       MESEJI_SENDER_ID if you ever need to send
 *                       under a different (also-approved) sender."""


def step_01_sender_id():
    print("\n[1/4] Use approved 'PARKIPAY' sender ID as the default")

    p = path("backend/src/config/index.js")
    text = read(p)
    if "'PARKIPAY'" in text:
        print(f"  {p} already patched — skipping")
    else:
        require_in(text, CONFIG_OLD, "backend/src/config/index.js")
        text = text.replace(CONFIG_OLD, CONFIG_NEW)
        write(p, text)
        print(f"  patched {p}")

    p = path("backend/.env.example")
    text = read(p)
    if "MESEJI_SENDER_ID=PARKIPAY" in text:
        print(f"  {p} already patched — skipping")
    else:
        require_in(text, ENV_OLD, "backend/.env.example")
        text = text.replace(ENV_OLD, ENV_NEW)
        write(p, text)
        print(f"  patched {p}")

    p = path("backend/src/lib/sms.js")
    text = read(p)
    if "approved sender ID" in text:
        print(f"  {p} already patched — skipping")
    else:
        require_in(text, SMS_JS_OLD, "backend/src/lib/sms.js")
        text = text.replace(SMS_JS_OLD, SMS_JS_NEW)
        write(p, text)
        print(f"  patched {p}")

    git_commit("backend: switch default Meseji sender ID to the approved 'PARKIPAY'")


# ═══════════════════════════════════════════════════════════════════════════
# STEP 2 — verify exactly one sendSMS call site (no file changes)
# ═══════════════════════════════════════════════════════════════════════════
def step_02_verify_single_sms():
    print("\n[2/4] Verify only one sendSMS(...) call site exists (bill SMS only)")
    call_sites = []
    for dirpath, _, filenames in os.walk(path("backend/src")):
        for fn in filenames:
            if not fn.endswith(".js"):
                continue
            fp = os.path.join(dirpath, fn)
            text = read(fp)
            for i, line in enumerate(text.splitlines(), 1):
                if re.search(r"\bsendSMS\s*\(", line) and "async function sendSMS" not in line:
                    call_sites.append(f"{os.path.relpath(fp, ROOT)}:{i}")

    print(f"  sendSMS() call sites found: {call_sites}")
    if len(call_sites) != 1 or "billing.js" not in call_sites[0]:
        raise SystemExit(
            "\n✗ Expected exactly one sendSMS() call site, in billing.js. "
            f"Found: {call_sites}\n"
            "  Something re-introduced a second SMS send (e.g. a registration "
            "SMS) — please investigate before proceeding."
        )
    print("  ✓ Confirmed: exactly one SMS send site (billing.js) — no changes needed.")


# ═══════════════════════════════════════════════════════════════════════════
# STEP 3 — connectivity audit (no file changes, informational only)
# ═══════════════════════════════════════════════════════════════════════════
def step_03_connectivity_audit():
    print("\n[3/4] End-to-end connectivity audit (mobile <-> backend <-> Meseji)")
    checks = [
        ("mobile/services/api.ts", "/api/billing/generate/"),
        ("backend/src/app.js", "/api/billing/"),
        ("backend/src/routes/billing.js", "router.post('/generate/'"),
        ("backend/src/routes/billing.js", "plate_number"),
        ("backend/src/routes/billing.js", "location_id"),
        ("backend/src/lib/sms.js", "x-api-key"),
        ("backend/src/lib/sms.js", "/sms/send"),
    ]
    ok = True
    for rel, needle in checks:
        p = path(rel)
        if not os.path.exists(p):
            print(f"  ✗ missing file: {rel}")
            ok = False
            continue
        text = read(p)
        status = "✓" if needle in text else "✗"
        if needle not in text:
            ok = False
        print(f"  {status} {rel} contains {needle!r}")

    if not ok:
        raise SystemExit(
            "\n✗ Connectivity audit found a mismatch — see ✗ lines above. "
            "Not safe to assume mobile <-> backend <-> Meseji wiring is intact; "
            "please investigate before deploying."
        )
    print("  ✓ mobile -> backend -> Meseji wiring verified consistent. No changes needed.")


# ═══════════════════════════════════════════════════════════════════════════
# STEP 4 — remove CI auto-merge; manual PR + manual merge only
# ═══════════════════════════════════════════════════════════════════════════
BACKEND_OLD_HEADER = """# =============================================================================
# ParkiPay — Backend CI
#
# Runs on every push / PR that touches backend/** on the develop branch.
# Pipeline:  lint  →  security-audit  →  test  →  merge-to-main
#
# Required secrets  (Settings → Secrets → Actions):
#   GH_PAT   Personal Access Token — scopes: repo, workflow
# ============================================================================="""

BACKEND_NEW_HEADER = """# =============================================================================
# ParkiPay — Backend CI
#
# Runs on every push / PR that touches backend/** on develop, and on any
# PR targeting main (so a manually-opened develop -> main PR shows these
# same checks before you merge it yourself).
# Pipeline:  lint  →  security-audit  →  test
#
# No job in this workflow touches `main` — PRs into main are opened and
# merged manually once all checks are green.
# ============================================================================="""

BACKEND_OLD_MERGE_JOB = """
  # ── Promote develop → main via PR + auto-merge (ruleset-compliant) ───────
  promote-to-main:
    name: Promote develop → main (PR + auto-merge)
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/develop'
    needs: [lint, security-audit, test]
    permissions:
      contents: read
      pull-requests: write

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Open (or reuse) develop → main PR and enable auto-merge
        env:
          GH_TOKEN: ${{ secrets.GH_PAT }}
        run: |
          number=$(gh pr list --base main --head develop --state open --json number --jq '.[0].number // empty')

          if [ -z "$number" ]; then
            if gh pr create \\
              --base main --head develop \\
              --title "chore: promote develop → main" \\
              --body "Automated promotion — backend CI passed on develop @ ${{ github.sha }}."
            then
              number=$(gh pr list --base main --head develop --state open --json number --jq '.[0].number // empty')
            else
              echo "gh pr create failed (likely a race with mobile-ci's promote job) — re-checking..."
              number=$(gh pr list --base main --head develop --state open --json number --jq '.[0].number // empty')
            fi
          fi

          if [ -z "$number" ]; then
            echo "::error::Could not find or create a develop → main PR"
            exit 1
          fi

          echo "Using PR #$number"
          gh pr merge "$number" --auto --merge
"""

MOBILE_OLD_HEADER = """# =============================================================================
# ParkiPay — Mobile CI
#
# Runs on every push / PR that touches mobile/** on the develop branch.
# Pipeline:  lint  →  type-check  →  test  →  merge-to-main
#
# Required secrets  (Settings → Secrets → Actions):
#   GH_PAT   Personal Access Token — scopes: repo, workflow
# ============================================================================="""

MOBILE_NEW_HEADER = """# =============================================================================
# ParkiPay — Mobile CI
#
# Runs on every push / PR that touches mobile/** on develop, and on any
# PR targeting main (so a manually-opened develop -> main PR shows these
# same checks before you merge it yourself).
# Pipeline:  lint  →  type-check  →  test
#
# No job in this workflow touches `main` — PRs into main are opened and
# merged manually once all checks are green.
# ============================================================================="""

MOBILE_OLD_MERGE_JOB = """
  # ── Promote develop → main via PR + auto-merge (ruleset-compliant) ───────
  promote-to-main:
    name: Promote develop → main (PR + auto-merge)
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/develop'
    needs: [lint, type-check, test]
    permissions:
      contents: read
      pull-requests: write

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Open (or reuse) develop → main PR and enable auto-merge
        env:
          GH_TOKEN: ${{ secrets.GH_PAT }}
        run: |
          number=$(gh pr list --base main --head develop --state open --json number --jq '.[0].number // empty')

          if [ -z "$number" ]; then
            if gh pr create \\
              --base main --head develop \\
              --title "chore: promote develop → main" \\
              --body "Automated promotion — mobile CI passed on develop @ ${{ github.sha }}."
            then
              number=$(gh pr list --base main --head develop --state open --json number --jq '.[0].number // empty')
            else
              echo "gh pr create failed (likely a race with backend-ci's promote job) — re-checking..."
              number=$(gh pr list --base main --head develop --state open --json number --jq '.[0].number // empty')
            fi
          fi

          if [ -z "$number" ]; then
            echo "::error::Could not find or create a develop → main PR"
            exit 1
          fi

          echo "Using PR #$number"
          gh pr merge "$number" --auto --merge
"""


def step_04_remove_ci_automerge():
    print("\n[4/4] Remove CI auto-merge job — manual PR + manual merge only")

    p = path(".github/workflows/backend-ci.yml")
    text = read(p)
    if "promote-to-main" not in text:
        print(f"  {p} already has no promote-to-main job — skipping")
    else:
        require_in(text, BACKEND_OLD_HEADER, "backend-ci.yml (header)")
        text = text.replace(BACKEND_OLD_HEADER, BACKEND_NEW_HEADER)
        require_in(text, BACKEND_OLD_MERGE_JOB, "backend-ci.yml (promote-to-main job)")
        text = text.replace(BACKEND_OLD_MERGE_JOB, "")
        text = text.rstrip("\n") + "\n"
        assert "promote-to-main" not in text
        assert "gh pr" not in text
        write(p, text)
        print(f"  patched {p}")

    p = path(".github/workflows/mobile-ci.yml")
    text = read(p)
    if "promote-to-main" not in text:
        print(f"  {p} already has no promote-to-main job — skipping")
    else:
        require_in(text, MOBILE_OLD_HEADER, "mobile-ci.yml (header)")
        text = text.replace(MOBILE_OLD_HEADER, MOBILE_NEW_HEADER)
        require_in(text, MOBILE_OLD_MERGE_JOB, "mobile-ci.yml (promote-to-main job)")
        text = text.replace(MOBILE_OLD_MERGE_JOB, "")
        text = text.rstrip("\n") + "\n"
        assert "promote-to-main" not in text
        assert "gh pr" not in text
        write(p, text)
        print(f"  patched {p}")

    git_commit(
        "ci: remove auto-merge job — develop->main PRs are now opened and "
        "merged manually once checks are green"
    )


# ═══════════════════════════════════════════════════════════════════════════
def main():
    check_repo()
    print("ParkiPay patch — approved sender ID + remove CI auto-merge")
    print("=" * 60)

    step_01_sender_id()
    step_02_verify_single_sms()
    step_03_connectivity_audit()
    step_04_remove_ci_automerge()

    print("\n" + "=" * 60)
    print("✓ Done. Review with `git log --oneline` / `git show`.")
    print("  Push to a feature branch and open a PR (main is still protected).")
    print("\n  Reminder: also set MESEJI_SENDER_ID=PARKIPAY on Render's env vars")
    print("  (this patch only changes the code-level default/fallback).")
    print("  GH_PAT is no longer required by these workflows — you can remove")
    print("  that secret if nothing else in the repo still uses it.")


if __name__ == "__main__":
    main()

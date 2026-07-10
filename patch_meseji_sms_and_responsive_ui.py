#!/usr/bin/env python3
"""
ParkiPay — combined patch script
=================================
Feature 1: Replace Twilio/Africa's Talking with Meseji SMS
  - New backend/src/lib/phone.js (+ mobile utils/phone.ts) for TZ
    mobile-number validation/normalization.
  - Rewritten backend/src/lib/sms.js calling Meseji's API.
  - backend/src/config/index.js + backend/.env.example cleaned of all
    Twilio / Africa's Talking references, MESEJI_* added.
  - billing.js sends a full Swahili SMS bill (plate, control number,
    amount, issued/expiry time) on every bill generation.
  - admin.js validates + normalizes owner phone to TZ format on
    vehicle registration.

Feature 2: Responsive mobile UI fixes
  - mobile/constants/api.ts: removes the stale fallback API URL.
  - mobile/app/(app)/vehicles.tsx: live TZ phone validation + makes
    the "Register Vehicle" sheet scrollable/keyboard-aware so nothing
    is cut off/hidden on medium or small screens.
  - mobile/app/(app)/admin.tsx: makes the "Add Officer" and
    "Move Location" sheets scrollable/keyboard-aware for the same
    reason.

USAGE
-----
Run this from the repository root (the folder containing `backend/`
and `mobile/`):

    python3 patch_meseji_sms_and_responsive_ui.py

The script is idempotent-safe: each step verifies its anchor text is
present verbatim before touching a file, and aborts loudly instead of
guessing if something doesn't match (e.g. the file was already
patched, or has diverged). It creates one git commit per logical
change, exactly like every other patch applied to this project so
far. No backup files are created — each step is a clean git commit,
so `git revert`/`git reset` is your rollback path if needed.

MESEJI API CONTRACT (confirmed from https://meseji.co.tz/docs)
----------------------------------------------------------------
  Base URL:  https://meseji.co.tz/api/v1
  Auth:      header  x-api-key: <your_api_key>   (NOT "Bearer ...")
  Send SMS:  POST /sms/send
    Body:    { "sender_id": "MESEJI", "message": "...",
               "contacts": "255744963858, 255712345678" }
             ('contacts' is a single comma-separated string of
             255XXXXXXXXX numbers — NOT a JSON array — and one call
             can batch-send to many recipients at once.)
    Response (2xx): { "batch_id": "...", "total_recipients": N,
                       "estimated_cost": N, "status": "queued" }
  Batch stats: GET /sms/stats/:batch_id (auth required)
    Response: { "batch_id","total_sent","successful","failed",
                 "success_rate" }
  Sender IDs: the account ships with a pre-approved default sender
    "MESEJI". A custom sender ID (e.g. "ParkiPay") must be requested
    via POST /sms/request-sender-id and approved before use — until
    then, sends using an unapproved sender_id will be rejected, so
    this integration defaults to "MESEJI" and lets MESEJI_SENDER_ID
    override it once you have an approved custom ID.
"""
import os
import re
import subprocess
import sys

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


def git(*args):
    subprocess.run(["git", *args], cwd=ROOT, check=True)


def git_commit(message):
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"], cwd=ROOT
    )
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
# STEP 1 — backend/src/lib/phone.js  (new file)
# ═══════════════════════════════════════════════════════════════════════════
BACKEND_PHONE_JS = """/**
 * ParkiPay — Tanzania mobile number helpers
 *
 * Accepted input formats (spaces/dashes are ignored):
 *   0712345678        (local, 10 digits)
 *   255712345678      (country code, no plus, 12 digits)
 *   +255712345678     (E.164, 12 digits after the +)
 *
 * Valid TZ mobile prefixes are 06 and 07 (all operators — Vodacom,
 * Tigo/Mixx by Yas, Airtel, Halotel, TTCL, Zantel — were consolidated
 * onto the 06/07 ranges after the Feb 2024 TCRA renumbering).
 */

const TZ_MOBILE_RE = /^255[67]\\d{8}$/;

/** Strips spaces, dashes, and a leading '+'. */
function cleanDigits(raw) {
  return String(raw ?? '').replace(/[\\s-]/g, '').replace(/^\\+/, '');
}

/**
 * Normalises any accepted TZ mobile format to '255XXXXXXXXX'.
 * Returns null if the input is not a valid Tanzanian mobile number.
 */
function normalizeTzMobile(raw) {
  let digits = cleanDigits(raw);

  if (digits.startsWith('0') && digits.length === 10) {
    digits = '255' + digits.slice(1);
  }

  return TZ_MOBILE_RE.test(digits) ? digits : null;
}

/** True if `raw` is a valid Tanzanian mobile number in any accepted format. */
function isValidTzMobile(raw) {
  return normalizeTzMobile(raw) !== null;
}

module.exports = { normalizeTzMobile, isValidTzMobile, TZ_MOBILE_RE };
"""


def step_01_backend_phone_util():
    print("\n[1/7] backend/src/lib/phone.js — TZ mobile validation util")
    p = path("backend/src/lib/phone.js")
    if os.path.exists(p):
        print("  (already exists — leaving untouched)")
        return
    write(p, BACKEND_PHONE_JS)
    assert BACKEND_PHONE_JS.count("{") == BACKEND_PHONE_JS.count("}")
    print(f"  created {p}")
    git_commit("backend: add shared Tanzania mobile-number validation/normalization util")


# ═══════════════════════════════════════════════════════════════════════════
# STEP 2 — backend/src/lib/sms.js (rewrite) + config/index.js + .env.example
# ═══════════════════════════════════════════════════════════════════════════
BACKEND_SMS_JS = """/**
 * ParkiPay — SMS via Meseji (https://meseji.co.tz/docs)
 *
 * Required env var:
 *   MESEJI_API_KEY   → API key from the Meseji dashboard (starts
 *                       with 'zs_'); sent as the `x-api-key` header.
 * Optional env vars:
 *   MESEJI_SENDER_ID → Sender name shown on the recipient's phone.
 *                       Defaults to 'MESEJI', the pre-approved
 *                       default sender every account gets. A custom
 *                       sender ID (e.g. 'ParkiPay') must be requested
 *                       via POST /sms/request-sender-id and approved
 *                       in the Meseji dashboard before it can be used
 *                       here — set MESEJI_SENDER_ID once it's live.
 *   MESEJI_BASE_URL  → Override the API host (defaults to Meseji's
 *                       production API, https://meseji.co.tz/api/v1).
 */
const https = require('https');
const cfg   = require('../config');
const { normalizeTzMobile } = require('./phone');

const MESEJI = {
  baseUrl:    cfg.meseji.baseUrl || 'https://meseji.co.tz/api/v1',
  sendPath:   '/sms/send',
  statsPath:  '/sms/stats', // + '/:batch_id'
  authHeader: 'x-api-key',  // raw key, no "Bearer" prefix
};

async function meseji(method, path, apiKey, body) {
  return new Promise((resolve) => {
    let url;
    try {
      // NOTE: new URL(path, base) treats a path starting with '/' as
      // absolute and DISCARDS base's own path (e.g. the '/api/v1' in
      // MESEJI.baseUrl) — so build the full string ourselves instead
      // of relying on WHATWG relative-URL resolution here.
      const base = MESEJI.baseUrl.replace(/\\/+$/, '');
      url = new URL(base + path);
    } catch (e) {
      resolve({ ok: false, error: `invalid_base_url: ${e.message}` });
      return;
    }

    const payload = body ? JSON.stringify(body) : null;
    const options = {
      hostname: url.hostname,
      path:     url.pathname + url.search,
      method,
      headers: {
        'Content-Type':        'application/json',
        [MESEJI.authHeader]:   apiKey,
        ...(payload ? { 'Content-Length': Buffer.byteLength(payload) } : {}),
      },
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        console.log(`[SMS] Meseji ${method} ${path} → HTTP ${res.statusCode}: ${data.slice(0, 400)}`);
        let json = null;
        try { json = data ? JSON.parse(data) : null; } catch { /* non-JSON body */ }
        resolve({ ok: res.statusCode >= 200 && res.statusCode < 300, statusCode: res.statusCode, json });
      });
    });

    req.on('error', (err) => {
      console.error('[SMS] Network error:', err.message);
      resolve({ ok: false, error: err.message });
    });

    if (payload) req.write(payload);
    req.end();
  });
}

/**
 * Sends one SMS to one or more Tanzanian mobile numbers in a single
 * Meseji batch call (per the documented /sms/send contract, which
 * takes a comma-separated string of recipients, not an array).
 */
async function sendSMS(to, message) {
  const apiKey = cfg.meseji.apiKey;

  if (!apiKey) {
    console.warn('[SMS] Meseji API key not configured — SMS skipped.');
    console.warn('[SMS] Set MESEJI_API_KEY on Render (see backend/.env.example).');
    return { success: false, error: 'not_configured' };
  }

  const recipients = (Array.isArray(to) ? to : [to])
    .map(normalizeTzMobile)
    .filter(Boolean);

  if (recipients.length === 0) {
    console.warn(`[SMS] No valid Tanzanian mobile number(s) in: ${JSON.stringify(to)}`);
    return { success: false, error: 'invalid_recipient' };
  }

  console.log(`[SMS] Sending to ${recipients.join(', ')} via Meseji (sender: ${cfg.meseji.senderId})...`);

  const result = await meseji('POST', MESEJI.sendPath, apiKey, {
    sender_id: cfg.meseji.senderId,
    message,
    contacts: recipients.join(', '),
  });

  if (result.ok && result.json?.batch_id) {
    console.log(`[SMS] ✅ Queued (batch_id=${result.json.batch_id}, status=${result.json.status})`);
    return {
      success: true,
      batchId: result.json.batch_id,
      status: result.json.status,
      estimatedCost: result.json.estimated_cost,
    };
  }

  const err = result.json?.message ?? result.json?.error ?? result.error ?? 'unknown_error';
  console.error(`[SMS] ❌ Send failed: HTTP ${result.statusCode ?? '—'} — ${err}`);
  return { success: false, error: err, httpStatus: result.statusCode };
}

/**
 * Optional: check delivery status/success rate for a previously sent
 * batch (GET /sms/stats/:batch_id). Handy for debugging from a shell
 * or an admin tool — not called automatically anywhere yet.
 */
async function getBatchStats(batchId) {
  const apiKey = cfg.meseji.apiKey;
  if (!apiKey) return { success: false, error: 'not_configured' };

  const result = await meseji('GET', `${MESEJI.statsPath}/${encodeURIComponent(batchId)}`, apiKey);
  if (result.ok && result.json) {
    return { success: true, ...result.json };
  }
  return { success: false, error: result.json?.message ?? result.error ?? 'unknown_error' };
}

module.exports = { sendSMS, getBatchStats };
"""


def patch_config_index(text: str) -> str:
    # Remove the Africa's Talking block (no-op if already removed)
    text = re.sub(
        r"\n  // ── Africa's Talking ──────────────────────────────────\n"
        r"  africasTalking: \{[^}]*\},\n",
        "\n",
        text,
    )

    if "meseji:" not in text:
        marker = "  // ── Resend Email ──────────────────────────────────────"
        require_in(text, marker, "backend/src/config/index.js")
        meseji_block = (
            "  // ── Meseji SMS (https://meseji.co.tz/docs) ─────────────\n"
            "  meseji: {\n"
            "    apiKey: process.env.MESEJI_API_KEY || '',\n\n"
            "    // 'MESEJI' is the pre-approved default sender every account gets.\n"
            "    // Switch to 'ParkiPay' once that sender ID is requested + approved\n"
            "    // (POST /sms/request-sender-id in the Meseji dashboard/API).\n"
            "    senderId: process.env.MESEJI_SENDER_ID || 'MESEJI',\n\n"
            "    baseUrl: process.env.MESEJI_BASE_URL || 'https://meseji.co.tz/api/v1',\n"
            "  },\n\n"
        )
        text = text.replace(marker, meseji_block + marker)

    text = text.replace("  required('AT_API_KEY');\n", "  required('MESEJI_API_KEY');\n")
    return text


def patch_env_example(text: str) -> str:
    text = re.sub(
        r"# ── Africa's Talking \(legacy — kept for reference\) ───────────────────────────\n"
        r"AT_USERNAME=sandbox\n"
        r"AT_API_KEY=replace-with-your-africastalking-api-key\n"
        r"AT_SENDER_ID=ParkiPay\n"
        r"AT_SANDBOX=True\n\n",
        "",
        text,
    )

    if "MESEJI_API_KEY" not in text:
        twilio_block = re.search(
            r"# ── Twilio \(active SMS provider\) ──────────────────────────────────────────────\n"
            r"(?:.*\n)*?"
            r"TWILIO_PHONE_NUMBER=\+12345678900\n\n",
            text,
        )
        require_in(text, "# ── Twilio", "backend/.env.example")
        if not twilio_block:
            raise SystemExit("Could not locate the full Twilio block in .env.example — aborting.")
        meseji_env = (
            "# ── Meseji (active SMS provider — https://meseji.co.tz/docs) ─────────────────\n"
            "# Dashboard: https://meseji.co.tz → Developer Settings → generate an API key\n"
            "# (sent as the x-api-key header, not Authorization/Bearer).\n"
            "MESEJI_API_KEY=zs_replace-with-your-meseji-api-key\n"
            "# 'MESEJI' is the pre-approved default sender ID. Switch to 'ParkiPay' once\n"
            "# that custom sender ID has been requested + approved in the dashboard.\n"
            "MESEJI_SENDER_ID=MESEJI\n"
            "MESEJI_BASE_URL=https://meseji.co.tz/api/v1\n\n"
        )
        text = text[:twilio_block.start()] + meseji_env + text[twilio_block.end():]
    return text


def step_02_meseji_sms():
    print("\n[2/7] backend/src/lib/sms.js — Meseji SMS provider")
    sms_path = path("backend/src/lib/sms.js")
    write(sms_path, BACKEND_SMS_JS)
    assert BACKEND_SMS_JS.count("{") == BACKEND_SMS_JS.count("}")
    print(f"  rewrote {sms_path}")

    config_path = path("backend/src/config/index.js")
    config_text = patch_config_index(read(config_path))
    assert "africasTalking" not in config_text
    assert "meseji:" in config_text
    assert "AT_API_KEY" not in config_text
    write(config_path, config_text)
    print(f"  patched {config_path}")

    env_path = path("backend/.env.example")
    env_text = patch_env_example(read(env_path))
    assert "TWILIO" not in env_text
    assert "AT_API_KEY" not in env_text
    assert "MESEJI_API_KEY" in env_text
    write(env_path, env_text)
    print(f"  patched {env_path}")

    git_commit(
        "backend: replace Twilio/Africa's Talking with Meseji SMS provider\n\n"
        "- Rewrites backend/src/lib/sms.js to call Meseji's /sms/send API (x-api-key auth)\n"
        "- Removes all Twilio + Africa's Talking config/env references\n"
        "- Adds MESEJI_API_KEY / MESEJI_SENDER_ID / MESEJI_BASE_URL config\n"
        "- Normalizes recipient numbers via the new TZ phone util before sending"
    )


# ═══════════════════════════════════════════════════════════════════════════
# STEP 3 — billing.js: full Swahili SMS bill message
# ═══════════════════════════════════════════════════════════════════════════
BILLING_OLD_SMS_BLOCK = """    // ── 7. SMS to vehicle owner (if registered) ───────────────────────────
    if (vehicle?.ownerPhone) {
      const { sendSMS } = require('../lib/sms');
      const startTime = new Date(bill.generatedAt);
      const endTime   = new Date(bill.expiresAt);
      const fmt = (d) => d.toTimeString().slice(0, 8); // HH:MM:SS

      const smsText =
        `Habari ndugu ${vehicle.ownerName},\\n` +
        `Nambari yako ya malipo ya maegesho ya ${location.name} ni ${bill.controlNumber}.\\n` +
        `Muda wa kuanza: ${fmt(startTime)}\\n` +
        `Muda wa kuisha: ${fmt(endTime)}`;

      sendSMS(vehicle.ownerPhone, smsText).catch((e) =>
        console.error('[Billing] SMS fire-and-forget error:', e.message));
    }
"""

BILLING_NEW_SMS_BLOCK = """    // ── 7. SMS to vehicle owner (if registered + valid TZ number) ─────────
    if (vehicle?.ownerPhone && isValidTzMobile(vehicle.ownerPhone)) {
      const { sendSMS } = require('../lib/sms');
      const smsText = buildBillSms({
        ownerName:     vehicle.ownerName,
        plateNumber:   bill.plateNumber,
        controlNumber: bill.controlNumber,
        amountDue:     bill.amountDue,
        locationName:  location.name,
        generatedAt:   bill.generatedAt,
        expiresAt:     bill.expiresAt,
      });

      sendSMS(vehicle.ownerPhone, smsText).catch((e) =>
        console.error('[Billing] SMS fire-and-forget error:', e.message));
    } else if (vehicle?.ownerPhone) {
      console.warn(`[Billing] Skipped SMS — invalid TZ mobile number on file: ${vehicle.ownerPhone}`);
    }
"""

BILLING_IMPORT_OLD = "const {\n  generateControlNumber,\n  getActiveBillForPlate,\n} = require('../lib/controlNumber');\n"
BILLING_IMPORT_NEW = (
    "const {\n  generateControlNumber,\n  getActiveBillForPlate,\n} = require('../lib/controlNumber');\n"
    "const { isValidTzMobile } = require('../lib/phone');\n"
)

BILLING_HELPER_FN = '''
// ── Swahili SMS bill formatter ────────────────────────────────────────────
// Dar es Salaam is UTC+3 year-round (no DST), so a fixed-offset format
// avoids depending on the server's local timezone/ICU data.
function fmtDarEsSalaam(date) {
  const d = new Date(date.getTime() + 3 * 60 * 60 * 1000); // shift to EAT
  const pad = (n) => String(n).padStart(2, '0');
  const day   = pad(d.getUTCDate());
  const month = pad(d.getUTCMonth() + 1);
  const year  = d.getUTCFullYear();
  const hh    = pad(d.getUTCHours());
  const mm    = pad(d.getUTCMinutes());
  return `${day}/${month}/${year} ${hh}:${mm}`;
}

function buildBillSms({ ownerName, plateNumber, controlNumber, amountDue, locationName, generatedAt, expiresAt }) {
  const amountFmt = `TZS ${Number(amountDue).toLocaleString('en-US')}`;
  return (
    `ParkiPay: Bili ya maegesho - ${locationName}\\n` +
    `Gari: ${plateNumber}\\n` +
    `Namba ya Udhibiti: ${controlNumber}\\n` +
    `Kiasi cha Kulipa: ${amountFmt}\\n` +
    `Muda wa Kutolewa: ${fmtDarEsSalaam(new Date(generatedAt))}\\n` +
    `Inaisha: ${fmtDarEsSalaam(new Date(expiresAt))}\\n` +
    `Lipa kupitia namba ya udhibiti hapo juu kabla ya muda kuisha. Asante kwa kutumia ParkiPay.`
  );
}
'''


def step_03_billing_sms():
    print("\n[3/7] backend/src/routes/billing.js — full Swahili bill SMS")
    p = path("backend/src/routes/billing.js")
    text = read(p)

    if "buildBillSms" in text:
        print("  (already patched — skipping)")
        return

    require_in(text, BILLING_OLD_SMS_BLOCK, "billing.js")
    text = text.replace(BILLING_OLD_SMS_BLOCK, BILLING_NEW_SMS_BLOCK)

    require_in(text, BILLING_IMPORT_OLD, "billing.js")
    text = text.replace(BILLING_IMPORT_OLD, BILLING_IMPORT_NEW)

    anchor = "const router = Router();"
    require_in(text, anchor, "billing.js")
    text = text.replace(anchor, BILLING_HELPER_FN.strip("\n") + "\n\n" + anchor, 1)

    assert "buildBillSms" in text
    assert "isValidTzMobile" in text
    assert text.count("{") == text.count("}")
    write(p, text)
    print(f"  patched {p}")
    git_commit(
        "backend(billing): send full Swahili bill SMS "
        "(plate, control number, amount, issued/expiry time)"
    )


# ═══════════════════════════════════════════════════════════════════════════
# STEP 4 — admin.js: TZ phone validation on vehicle registration
# ═══════════════════════════════════════════════════════════════════════════
ADMIN_OLD_IMPORT = "const { sendSMS } = require('../lib/sms');\nconst { authenticate } = require('../middleware/auth');\n"
ADMIN_NEW_IMPORT = (
    "const { sendSMS } = require('../lib/sms');\n"
    "const { isValidTzMobile, normalizeTzMobile } = require('../lib/phone');\n"
    "const { authenticate } = require('../middleware/auth');\n"
)

ADMIN_OLD_SCHEMA = """const RegisterVehicleSchema = z.object({
  plateNumber: z.string().min(3).max(15),
  ownerName:   z.string().min(2),
  ownerPhone:  z.string().min(10).max(15),
  make:        z.string().optional().default(''),
  model:       z.string().optional().default(''),
  category:    z.enum(['MOTORCYCLE','PRIVATE_CAR','MINIBUS','BUS','TRUCK','GOVERNMENT'])
                 .optional().default('PRIVATE_CAR'),
});"""

ADMIN_NEW_SCHEMA = """const RegisterVehicleSchema = z.object({
  plateNumber: z.string().min(3).max(15),
  ownerName:   z.string().min(2),
  ownerPhone:  z.string().min(10).max(15).refine(isValidTzMobile, {
    message: 'ownerPhone must be a valid Tanzanian mobile number (e.g. 07XXXXXXXX, 06XXXXXXXX, or +255XXXXXXXXX).',
  }),
  make:        z.string().optional().default(''),
  model:       z.string().optional().default(''),
  category:    z.enum(['MOTORCYCLE','PRIVATE_CAR','MINIBUS','BUS','TRUCK','GOVERNMENT'])
                 .optional().default('PRIVATE_CAR'),
});"""

ADMIN_OLD_REGISTER = """    const { plateNumber: rawPlate, ownerName, ownerPhone, make, model, category } = parsed.data;
    const plateNumber = rawPlate.trim().toUpperCase().replace(/\\s+/g, '');

    const existing = await prisma.vehicle.findUnique({ where: { plateNumber } });
    if (existing)
      return res.status(409).json({ error: 'duplicate', detail: `Plate ${plateNumber} is already registered.` });

    const vehicle = await prisma.vehicle.create({
      data: { plateNumber, ownerName, ownerPhone, make: make ?? '', model: model ?? '', category },
    });

    // Invalidate any cached lookup for this plate
    await redis.cacheDel(`vehicle:${plateNumber}`);

    // Send SMS to owner with registration confirmation
    const smsText =
      `ParkiPay: Gari lako (${plateNumber}) limesajiliwa kwenye mfumo wa maegesho. ` +
      `Ukipata faini utapokea ujumbe mwingine. Asante!`;
    const smsResult = await sendSMS(ownerPhone, smsText);
    if (!smsResult.success) {
      console.warn('[Admin] Vehicle registered but SMS failed:', smsResult.error);
    }

    res.status(201).json({ ...vehicle, smsSent: smsResult.success });"""

ADMIN_NEW_REGISTER = """    const { plateNumber: rawPlate, ownerName, ownerPhone: rawPhone, make, model, category } = parsed.data;
    const plateNumber = rawPlate.trim().toUpperCase().replace(/\\s+/g, '');
    const ownerPhone  = normalizeTzMobile(rawPhone); // always store the canonical 255XXXXXXXXX form

    const existing = await prisma.vehicle.findUnique({ where: { plateNumber } });
    if (existing)
      return res.status(409).json({ error: 'duplicate', detail: `Plate ${plateNumber} is already registered.` });

    const vehicle = await prisma.vehicle.create({
      data: { plateNumber, ownerName, ownerPhone, make: make ?? '', model: model ?? '', category },
    });

    // Invalidate any cached lookup for this plate
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


def step_04_admin_phone_validation():
    print("\n[4/7] backend/src/routes/admin.js — TZ phone validation on registration")
    p = path("backend/src/routes/admin.js")
    text = read(p)

    if "isValidTzMobile" in text:
        print("  (already patched — skipping)")
        return

    for old, label in (
        (ADMIN_OLD_IMPORT, "import block"),
        (ADMIN_OLD_SCHEMA, "RegisterVehicleSchema"),
        (ADMIN_OLD_REGISTER, "register handler"),
    ):
        require_in(text, old, f"admin.js ({label})")

    text = text.replace(ADMIN_OLD_IMPORT, ADMIN_NEW_IMPORT)
    text = text.replace(ADMIN_OLD_SCHEMA, ADMIN_NEW_SCHEMA)
    text = text.replace(ADMIN_OLD_REGISTER, ADMIN_NEW_REGISTER)

    assert "isValidTzMobile" in text and "normalizeTzMobile" in text
    assert text.count("{") == text.count("}")
    write(p, text)
    print(f"  patched {p}")
    git_commit("backend(admin): validate + normalize owner phone to TZ mobile format on vehicle registration")


# ═══════════════════════════════════════════════════════════════════════════
# STEP 5 — mobile/constants/api.ts: remove stale fallback URL
# ═══════════════════════════════════════════════════════════════════════════
def step_05_stale_api_url():
    print("\n[5/7] mobile/constants/api.ts — remove stale fallback API URL")
    p = path("mobile/constants/api.ts")
    text = read(p)
    old = "const PRODUCTION_API_URL = 'https://paypark-backend-6kc4.onrender.com';"
    new = "const PRODUCTION_API_URL = 'https://paypark-8huj.onrender.com';"

    if old not in text:
        if "paypark-8huj.onrender.com" in text:
            print("  (already patched — skipping)")
            return
        raise SystemExit("Stale URL constant not found verbatim — aborting.")

    text = text.replace(old, new)
    assert "paypark-backend-6kc4" not in text
    write(p, text)
    print(f"  patched {p}")
    git_commit("mobile: remove stale fallback API URL (paypark-backend-6kc4 -> paypark-8huj)")


# ═══════════════════════════════════════════════════════════════════════════
# STEP 6 — mobile/utils/phone.ts (new) + vehicles.tsx (validation + responsive)
# ═══════════════════════════════════════════════════════════════════════════
MOBILE_PHONE_TS = """/**
 * ParkiPay — Tanzania mobile number helpers (mobile app)
 *
 * Mirrors backend/src/lib/phone.js so validation feels identical
 * whether it's caught client-side (live red-border feedback) or
 * server-side.
 *
 * Accepted input formats (spaces/dashes ignored):
 *   0712345678        (local, 10 digits)
 *   255712345678      (country code, no plus)
 *   +255712345678     (E.164)
 *
 * Valid TZ mobile prefixes are 06 and 07 (all operators were
 * consolidated onto these ranges after the Feb 2024 TCRA renumbering).
 */

const TZ_MOBILE_RE = /^255[67]\\d{8}$/;

function cleanDigits(raw: string): string {
  return String(raw ?? '').replace(/[\\s-]/g, '').replace(/^\\+/, '');
}

/** Normalises any accepted TZ mobile format to '255XXXXXXXXX', or null if invalid. */
export function normalizeTzMobile(raw: string): string | null {
  let digits = cleanDigits(raw);

  if (digits.startsWith('0') && digits.length === 10) {
    digits = '255' + digits.slice(1);
  }

  return TZ_MOBILE_RE.test(digits) ? digits : null;
}

/** True if `raw` is a complete, valid Tanzanian mobile number. */
export function isValidTzMobile(raw: string): boolean {
  return normalizeTzMobile(raw) !== null;
}

/**
 * True if `raw` COULD still become a valid number as the user keeps
 * typing (used for live red-border feedback, same UX pattern as the
 * plate-number field). Only rejects characters/positions that can
 * never be valid, e.g. a 3rd digit that isn't 6 or 7 after a leading 0.
 */
export function isPartialTzMobileValid(raw: string): boolean {
  const digits = cleanDigits(raw);
  if (digits.length === 0) return true;

  // Accept either local (0...) or international (255...) entry paths
  if (digits[0] === '0') {
    if (digits.length >= 2 && !/[67]/.test(digits[1])) return false;
    return digits.length <= 10;
  }
  if (digits.startsWith('255') || '255'.startsWith(digits)) {
    const rest = digits.slice(3);
    if (rest.length >= 1 && !/[67]/.test(rest[0])) return false;
    return digits.length <= 12;
  }
  return false;
}

/** Pretty-prints a normalized '255XXXXXXXXX' number as '+255 7XX XXX XXX'. */
export function formatTzMobileDisplay(normalized: string): string {
  if (!TZ_MOBILE_RE.test(normalized)) return normalized;
  const local = normalized.slice(3); // 9 digits, e.g. 712345678
  return `+255 ${local.slice(0, 3)} ${local.slice(3, 6)} ${local.slice(6)}`;
}
"""


def step_06_vehicles_phone_and_responsive():
    print("\n[6/7] mobile/utils/phone.ts + vehicles.tsx — TZ phone validation + responsive sheet")

    phone_ts_path = path("mobile/utils/phone.ts")
    if not os.path.exists(phone_ts_path):
        write(phone_ts_path, MOBILE_PHONE_TS)
        print(f"  created {phone_ts_path}")
    else:
        print(f"  {phone_ts_path} already exists — leaving untouched")

    p = path("mobile/app/(app)/vehicles.tsx")
    text = read(p)

    if "isPartialTzMobileValid" in text:
        print("  vehicles.tsx already patched — skipping")
        git_commit("mobile: add TZ mobile number validation util (mirrors backend/src/lib/phone.js)")
        return

    old_rn_import = """import {
  ActivityIndicator, Alert, FlatList, Modal, Pressable,
  SafeAreaView, StyleSheet, Text, TextInput,
  TouchableOpacity, View,
} from 'react-native';"""
    new_rn_import = """import {
  ActivityIndicator, Alert, FlatList, KeyboardAvoidingView, Modal, Platform,
  Pressable, SafeAreaView, ScrollView, StyleSheet, Text, TextInput,
  TouchableOpacity, View,
} from 'react-native';"""
    require_in(text, old_rn_import, "vehicles.tsx (RN import)")
    text = text.replace(old_rn_import, new_rn_import)

    old_util_import = "import { moderateScale } from '@/utils/responsive';"
    new_util_import = (
        "import { moderateScale } from '@/utils/responsive';\n"
        "import { isPartialTzMobileValid, isValidTzMobile } from '@/utils/phone';"
    )
    require_in(text, old_util_import, "vehicles.tsx (responsive import)")
    text = text.replace(old_util_import, new_util_import)

    old_state = """  const [nameError,   setNameError]   = useState(false);
  const [plateError,  setPlateError]  = useState(false);"""
    new_state = """  const [nameError,   setNameError]   = useState(false);
  const [plateError,  setPlateError]  = useState(false);
  const [phoneError,  setPhoneError]  = useState(false);"""
    require_in(text, old_state, "vehicles.tsx (state)")
    text = text.replace(old_state, new_state)

    old_reset = """  const resetForm = () => {
    setFOwnerName(''); setFPhone(''); setFPlate('');
    setFMake(''); setFModel(''); setFCategory('PRIVATE_CAR');
    setNameError(false); setPlateError(false);
  };"""
    new_reset = """  const resetForm = () => {
    setFOwnerName(''); setFPhone(''); setFPlate('');
    setFMake(''); setFModel(''); setFCategory('PRIVATE_CAR');
    setNameError(false); setPlateError(false); setPhoneError(false);
  };"""
    require_in(text, old_reset, "vehicles.tsx (resetForm)")
    text = text.replace(old_reset, new_reset)

    old_submit_check = """    if (!isThreeNames(fOwnerName)) {
      setNameError(true);
      Alert.alert('', 'Enter the owner\\'s full name as three names: first, middle, and surname.');
      return;
    }
    const plateClean = fPlate.trim().toUpperCase().replace(/\\s/g, '');"""
    new_submit_check = """    if (!isThreeNames(fOwnerName)) {
      setNameError(true);
      Alert.alert('', 'Enter the owner\\'s full name as three names: first, middle, and surname.');
      return;
    }
    if (!isValidTzMobile(fPhone)) {
      setPhoneError(true);
      Alert.alert('', 'Enter a valid Tanzanian mobile number (e.g. 07XXXXXXXX, 06XXXXXXXX, or +255XXXXXXXXX).');
      return;
    }
    const plateClean = fPlate.trim().toUpperCase().replace(/\\s/g, '');"""
    require_in(text, old_submit_check, "vehicles.tsx (submit validation)")
    text = text.replace(old_submit_check, new_submit_check)

    old_phone_input = """          <View style={{ marginBottom: 12 }}>
            <Text style={[S.inputLabel, { color: C.textSub }]}>Phone Number *</Text>
            <TextInput
              style={[S.input, { color: C.text, borderColor: C.border, backgroundColor: C.bg }]}
              value={fPhone}
              onChangeText={setFPhone}
              placeholder="+255 7XX XXX XXX"
              placeholderTextColor={C.textMuted}
              keyboardType="phone-pad"
            />
          </View>"""
    new_phone_input = """          <View style={{ marginBottom: 12 }}>
            <Text style={[S.inputLabel, { color: C.textSub }]}>Phone Number *</Text>
            <TextInput
              style={[S.input, { color: C.text, backgroundColor: C.bg,
                borderColor: phoneError ? '#EF4444' : C.border }]}
              value={fPhone}
              onChangeText={(text) => {
                setFPhone(text);
                setPhoneError(text.trim().length > 0 && !isPartialTzMobileValid(text));
              }}
              placeholder="07XX XXX XXX"
              placeholderTextColor={C.textMuted}
              keyboardType="phone-pad"
              maxLength={13}
            />
            <Text style={[S.hintSmall, { color: phoneError ? '#EF4444' : C.textMuted }]}>
              Format: 07XXXXXXXX, 06XXXXXXXX, or +255XXXXXXXXX
            </Text>
          </View>"""
    require_in(text, old_phone_input, "vehicles.tsx (phone input)")
    text = text.replace(old_phone_input, new_phone_input)

    old_sheet_open = """      <Modal visible={showAdd} transparent animationType="slide" onRequestClose={() => setShowAdd(false)}>
        <Pressable style={S.backdrop} onPress={() => setShowAdd(false)} />
        <View style={[S.sheet, { backgroundColor: C.card }]}>
          <View style={S.sheetHandle} />
          <Text style={[S.sheetTitle, { color: C.text }]}>Register Vehicle</Text>"""
    new_sheet_open = """      <Modal visible={showAdd} transparent animationType="slide" onRequestClose={() => setShowAdd(false)}>
        <Pressable style={S.backdrop} onPress={() => setShowAdd(false)} />
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
          style={S.sheetKav}
          pointerEvents="box-none"
        >
        <View style={[S.sheet, { backgroundColor: C.card }]}>
          <View style={S.sheetHandle} />
          <ScrollView
            keyboardShouldPersistTaps="handled"
            showsVerticalScrollIndicator={false}
            contentContainerStyle={{ paddingBottom: 8 }}
          >
          <Text style={[S.sheetTitle, { color: C.text }]}>Register Vehicle</Text>"""
    require_in(text, old_sheet_open, "vehicles.tsx (sheet open)")
    text = text.replace(old_sheet_open, new_sheet_open)

    old_sheet_close = """          <TouchableOpacity style={[S.saveBtn, saving && { opacity: 0.6 }]}
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
      </Modal>"""
    new_sheet_close = """          <TouchableOpacity style={[S.saveBtn, saving && { opacity: 0.6 }]}
            onPress={handleRegister} disabled={saving}>
            {saving
              ? <ActivityIndicator color="#fff" />
              : <>
                  <Ionicons name="checkmark-circle-outline" size={18} color="#fff" />
                  <Text style={S.saveBtnText}>Register Vehicle</Text>
                </>
            }
          </TouchableOpacity>
          </ScrollView>
        </View>
        </KeyboardAvoidingView>
      </Modal>"""
    require_in(text, old_sheet_close, "vehicles.tsx (sheet close)")
    text = text.replace(old_sheet_close, new_sheet_close)

    old_sheet_style = """    sheet:{ borderTopLeftRadius:24, borderTopRightRadius:24, padding:24, paddingBottom:40,
      maxHeight:'92%' },"""
    new_sheet_style = """    sheetKav:{ justifyContent:'flex-end' },
    sheet:{ borderTopLeftRadius:24, borderTopRightRadius:24, padding:24, paddingBottom:24,
      maxHeight:'85%' },"""
    require_in(text, old_sheet_style, "vehicles.tsx (sheet style)")
    text = text.replace(old_sheet_style, new_sheet_style)

    assert text.count("<ScrollView") == text.count("</ScrollView>")
    assert text.count("<KeyboardAvoidingView") == 1
    assert text.count("</KeyboardAvoidingView>") == 1
    write(p, text)
    print(f"  patched {p}")
    git_commit(
        "mobile(vehicles): validate TZ phone format live + make Register sheet "
        "scrollable/keyboard-aware for small screens"
    )


# ═══════════════════════════════════════════════════════════════════════════
# STEP 7 — admin.tsx: responsive scrollable sheets
# ═══════════════════════════════════════════════════════════════════════════
def step_07_admin_responsive():
    print("\n[7/7] mobile/app/(app)/admin.tsx — responsive scrollable sheets")
    p = path("mobile/app/(app)/admin.tsx")
    text = read(p)

    if "sheetKav" in text:
        print("  (already patched — skipping)")
        return

    old_import = """import {
  ActivityIndicator, Animated, Dimensions, FlatList, Modal,
  Platform, Pressable, SafeAreaView, StatusBar, StyleSheet,
  Text, TextInput, TouchableOpacity, View,
} from 'react-native';"""
    new_import = """import {
  ActivityIndicator, Animated, Dimensions, FlatList, KeyboardAvoidingView, Modal,
  Platform, Pressable, SafeAreaView, ScrollView, StatusBar, StyleSheet,
  Text, TextInput, TouchableOpacity, View,
} from 'react-native';"""
    require_in(text, old_import, "admin.tsx (RN import)")
    text = text.replace(old_import, new_import)

    old_add_open = """      <Modal visible={showAdd} transparent animationType="slide" onRequestClose={() => setShowAdd(false)}>
        <Pressable style={S.backdrop} onPress={() => setShowAdd(false)}/>
        <View style={[S.sheet, { backgroundColor: C.card }]}>
          <Text style={[S.sheetTitle, { color: C.text }]}>{tr('addOfficer')}</Text>"""
    new_add_open = """      <Modal visible={showAdd} transparent animationType="slide" onRequestClose={() => setShowAdd(false)}>
        <Pressable style={S.backdrop} onPress={() => setShowAdd(false)}/>
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
          style={S.sheetKav}
          pointerEvents="box-none"
        >
        <View style={[S.sheet, { backgroundColor: C.card }]}>
          <ScrollView
            keyboardShouldPersistTaps="handled"
            showsVerticalScrollIndicator={false}
            contentContainerStyle={{ paddingBottom: 8 }}
          >
          <Text style={[S.sheetTitle, { color: C.text }]}>{tr('addOfficer')}</Text>"""
    require_in(text, old_add_open, "admin.tsx (Add Officer sheet open)")
    text = text.replace(old_add_open, new_add_open)

    old_add_close = """          <TouchableOpacity style={[S.saveBtn, saving && { opacity:0.6 }]}
            onPress={handleAdd} disabled={saving}>
            {saving ? <ActivityIndicator color="#fff"/> :
              <Text style={S.saveBtnText}>{tr('save')}</Text>}
          </TouchableOpacity>
        </View>
      </Modal>"""
    new_add_close = """          <TouchableOpacity style={[S.saveBtn, saving && { opacity:0.6 }]}
            onPress={handleAdd} disabled={saving}>
            {saving ? <ActivityIndicator color="#fff"/> :
              <Text style={S.saveBtnText}>{tr('save')}</Text>}
          </TouchableOpacity>
          </ScrollView>
        </View>
        </KeyboardAvoidingView>
      </Modal>"""
    require_in(text, old_add_close, "admin.tsx (Add Officer sheet close)")
    text = text.replace(old_add_close, new_add_close)

    old_move = """      <Modal visible={!!showMove} transparent animationType="slide" onRequestClose={() => setShowMove(null)}>
        <Pressable style={S.backdrop} onPress={() => setShowMove(null)}/>
        <View style={[S.sheet, { backgroundColor: C.card }]}>
          <Text style={[S.sheetTitle, { color: C.text }]}>
            {tr('moveLocation')}: {showMove?.fullName}
          </Text>
          <View style={S.locGrid}>
            {locations.map(loc => (
              <TouchableOpacity key={loc.id} style={S.locChip} onPress={() => handleMove(loc.id)}>
                <Text style={S.locChipText}>{loc.name}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      </Modal>"""
    new_move = """      <Modal visible={!!showMove} transparent animationType="slide" onRequestClose={() => setShowMove(null)}>
        <Pressable style={S.backdrop} onPress={() => setShowMove(null)}/>
        <View style={[S.sheet, { backgroundColor: C.card }]}>
          <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 8 }}>
          <Text style={[S.sheetTitle, { color: C.text }]}>
            {tr('moveLocation')}: {showMove?.fullName}
          </Text>
          <View style={S.locGrid}>
            {locations.map(loc => (
              <TouchableOpacity key={loc.id} style={S.locChip} onPress={() => handleMove(loc.id)}>
                <Text style={S.locChipText}>{loc.name}</Text>
              </TouchableOpacity>
            ))}
          </View>
          </ScrollView>
        </View>
      </Modal>"""
    require_in(text, old_move, "admin.tsx (Move Location sheet)")
    text = text.replace(old_move, new_move)

    old_sheet_style = """  backdrop:{ flex:1, backgroundColor:'rgba(0,0,0,0.5)' },
  sheet:{ borderTopLeftRadius:20, borderTopRightRadius:20, padding:24, paddingBottom:40 },"""
    new_sheet_style = """  backdrop:{ flex:1, backgroundColor:'rgba(0,0,0,0.5)' },
  sheetKav:{ justifyContent:'flex-end' },
  sheet:{ borderTopLeftRadius:20, borderTopRightRadius:20, padding:24, paddingBottom:24,
    maxHeight:'85%' },"""
    require_in(text, old_sheet_style, "admin.tsx (sheet style)")
    text = text.replace(old_sheet_style, new_sheet_style)

    assert text.count("<ScrollView") == text.count("</ScrollView>") == 2
    assert text.count("<KeyboardAvoidingView") == 1
    assert text.count("</KeyboardAvoidingView>") == 1
    write(p, text)
    print(f"  patched {p}")
    git_commit(
        "mobile(admin): make Add Officer + Move Location sheets "
        "scrollable/keyboard-aware for small screens"
    )


# ═══════════════════════════════════════════════════════════════════════════
def main():
    check_repo()
    print("ParkiPay patch — Meseji SMS + responsive UI fixes")
    print("=" * 60)

    step_01_backend_phone_util()
    step_02_meseji_sms()
    step_03_billing_sms()
    step_04_admin_phone_validation()
    step_05_stale_api_url()
    step_06_vehicles_phone_and_responsive()
    step_07_admin_responsive()

    print("\n" + "=" * 60)
    print("✓ All steps complete. Review with `git log --oneline` / `git show`.")
    print("  Remember: `main` is protected — push this to a feature branch")
    print("  and open a PR rather than pushing directly.")
    print("\n  Still to do manually:")
    print("  - Set MESEJI_API_KEY on Render (from Meseji dashboard → Developer Settings)")
    print("  - Request + approve a 'ParkiPay' sender ID in the Meseji dashboard, then")
    print("    set MESEJI_SENDER_ID=ParkiPay on Render (defaults to 'MESEJI' until then)")
    print("  - Send one real bill and check the Render logs for a line like")
    print("    '[SMS] Meseji POST /sms/send → HTTP 200: {\"batch_id\":...}'")
    print("    to confirm it queued successfully.")


if __name__ == "__main__":
    main()

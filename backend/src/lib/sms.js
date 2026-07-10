/**
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
      const base = MESEJI.baseUrl.replace(/\/+$/, '');
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

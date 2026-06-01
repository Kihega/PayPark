/**
 * ParkiPay — SMS via Twilio REST API (no SDK, pure Node.js https)
 *
 * Required env vars:
 *   TWILIO_ACCOUNT_SID   → AC... from Twilio Console
 *   TWILIO_AUTH_TOKEN    → Auth Token from Twilio Console
 *   TWILIO_PHONE_NUMBER  → your Twilio number e.g. +12345678900
 *
 * Trial account limitation: can only send to VERIFIED numbers.
 * Verify numbers at: https://console.twilio.com/us1/develop/phone-numbers/manage/verified
 */
const https = require('https');
const cfg   = require('../config');

/** Normalise TZ number → E.164 (+255XXXXXXXXX) */
function normalise(num) {
  const s = String(num).replace(/\s+/g, '').replace(/^0/, '255');
  return s.startsWith('+') ? s : `+${s}`;
}

async function sendSMS(to, message) {
  const { accountSid, authToken, phoneNumber } = cfg.twilio;

  if (!accountSid || !authToken || !phoneNumber) {
    console.warn('[SMS] Twilio credentials not configured — SMS skipped.');
    console.warn('[SMS] Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER on Render.');
    return { success: false, error: 'not_configured' };
  }

  const recipients = (Array.isArray(to) ? to : [to]).map(normalise);
  const results    = [];

  for (const recipient of recipients) {
    console.log(`[SMS] Sending to ${recipient} via Twilio...`);

    const body = new URLSearchParams({
      To:   recipient,
      From: phoneNumber,
      Body: message,
    }).toString();

    const result = await new Promise((resolve) => {
      const options = {
        hostname: 'api.twilio.com',
        path:     `/2010-04-01/Accounts/${accountSid}/Messages.json`,
        method:   'POST',
        headers:  {
          'Content-Type':   'application/x-www-form-urlencoded',
          'Content-Length': Buffer.byteLength(body),
          'Authorization':  'Basic ' + Buffer.from(`${accountSid}:${authToken}`).toString('base64'),
        },
      };

      const req = https.request(options, (res) => {
        let data = '';
        res.on('data', chunk => { data += chunk; });
        res.on('end', () => {
          console.log(`[SMS] HTTP ${res.statusCode}: ${data.slice(0, 300)}`);
          try {
            const json = JSON.parse(data);
            if (res.statusCode === 201 && json.sid) {
              console.log(`[SMS] ✅ Sent! SID=${json.sid} status=${json.status}`);
              resolve({ success: true, messageId: json.sid });
            } else {
              const err = json.message ?? json.code ?? 'unknown';
              console.error(`[SMS] ❌ Failed: ${err}`);

              // Human-readable hints for common Twilio error codes
              const hints = {
                21408: 'Permission to send to this region is not enabled — enable Tanzania in Twilio Console → Messaging → Settings → Geo Permissions',
                21610: 'Recipient has opted out (unsubscribed)',
                21211: 'Invalid To phone number — check format (+255XXXXXXXXX)',
                21214: 'To number is not verified — verify it in Twilio Console (trial accounts only)',
                20003: 'Authentication error — check TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN',
                21608: 'Twilio trial accounts can only send to verified numbers — verify +255611380091 in Twilio Console',
              };
              const code = json.code;
              if (hints[code]) console.warn(`[SMS] Hint (${code}): ${hints[code]}`);

              resolve({ success: false, error: err, code });
            }
          } catch {
            resolve({ success: false, error: 'parse_error' });
          }
        });
      });

      req.on('error', (err) => {
        console.error('[SMS] Network error:', err.message);
        resolve({ success: false, error: err.message });
      });

      req.write(body);
      req.end();
    });

    results.push(result);
  }

  // Return first result (usually single recipient)
  return results[0] ?? { success: false, error: 'no_recipients' };
}

module.exports = { sendSMS };

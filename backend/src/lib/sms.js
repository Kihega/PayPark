/**
 * ParkiPay — SMS helper (Africa's Talking)
 *
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │  SETUP REQUIRED (after deployment):                                 │
 * │  1. Register at https://account.africastalking.com                  │
 * │  2. For SANDBOX testing:                                            │
 * │     • AT_USERNAME=sandbox                                           │
 * │     • AT_API_KEY=<sandbox key from AT dashboard>                    │
 * │     • AT_SANDBOX=True                                               │
 * │     • Add YOUR phone number to the sandbox test numbers list        │
 * │       in the AT dashboard (Simulator → SMS → Test Accounts)        │
 * │  3. For PRODUCTION (live SMS to any number):                        │
 * │     • AT_USERNAME=<your app username>                               │
 * │     • AT_API_KEY=<live API key>                                     │
 * │     • AT_SANDBOX=False                                              │
 * │     • AT_SENDER_ID=ParkiPay  (request from AT if needed)           │
 * └─────────────────────────────────────────────────────────────────────┘
 */
const cfg = require('../config');

async function sendSMS(to, message) {
  const { username, apiKey, senderId, sandbox } = cfg.africasTalking;

  if (!apiKey) {
    console.warn('[SMS] AT_API_KEY not configured — SMS skipped.');
    return { success: false, error: 'not_configured' };
  }

  // Normalise phone → E.164  (+255...)
  const normalise = (num) => {
    const s = String(num).replace(/\s+/g, '').replace(/^0/, '+255');
    return s.startsWith('+') ? s : `+${s}`;
  };

  const recipients = (Array.isArray(to) ? to : [to]).map(normalise);
  console.log(`[SMS] Sending to ${recipients.join(',')} (sandbox=${sandbox})`);

  try {
    const AfricasTalking = require('africastalking');
    const at = AfricasTalking({ username, apiKey });

    const payload = {
      to:      recipients,
      message,
    };
    // Only add `from` in production (sandbox ignores / rejects custom sender IDs)
    if (!sandbox && senderId) payload.from = senderId;

    const result = await at.SMS.send(payload);
    console.log('[SMS] API response:', JSON.stringify(result?.SMSMessageData?.Recipients));

    const recipients_res = result?.SMSMessageData?.Recipients ?? [];
    const success = recipients_res.some(r => r.status === 'Success');

    if (success) {
      return { success: true, messageId: recipients_res[0]?.messageId };
    }
    const codes = recipients_res.map(r => r.statusCode).join(',');
    console.error('[SMS] Delivery failed. Status codes:', codes);
    return { success: false, error: codes || 'unknown' };
  } catch (e) {
    console.error('[SMS] Exception:', e.message);
    return { success: false, error: e.message };
  }
}

module.exports = { sendSMS };

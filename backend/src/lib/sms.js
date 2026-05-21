/**
 * ParkiPay — SMS helper (Africa's Talking)
 * Returns { success, messageId?, error? }
 */
const cfg = require('../config');

async function sendSMS(to, message) {
  const { username, apiKey, senderId, sandbox } = cfg.africasTalking;
  if (!apiKey) {
    console.warn('[SMS] AT_API_KEY not set — skipping SMS');
    return { success: false, error: 'not_configured' };
  }
  try {
    const AfricasTalking = require('africastalking');
    const at = AfricasTalking({ username, apiKey });
    const result = await at.SMS.send({
      to:   Array.isArray(to) ? to : [to],
      message,
      from: sandbox ? '' : senderId,
    });
    const recipient = result?.SMSMessageData?.Recipients?.[0];
    if (recipient?.status === 'Success') {
      return { success: true, messageId: recipient.messageId };
    }
    return { success: false, error: recipient?.statusCode ?? 'unknown' };
  } catch (e) {
    console.error('[SMS] Send error:', e.message);
    return { success: false, error: e.message };
  }
}

module.exports = { sendSMS };

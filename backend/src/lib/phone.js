/**
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

const TZ_MOBILE_RE = /^255[67]\d{8}$/;

/** Strips spaces, dashes, and a leading '+'. */
function cleanDigits(raw) {
  return String(raw ?? '').replace(/[\s-]/g, '').replace(/^\+/, '');
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

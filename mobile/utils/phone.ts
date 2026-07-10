/**
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

const TZ_MOBILE_RE = /^255[67]\d{8}$/;

function cleanDigits(raw: string): string {
  return String(raw ?? '').replace(/[\s-]/g, '').replace(/^\+/, '');
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

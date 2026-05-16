// ParkiPay — Audit log helper (mirrors log_action() in Django)
const prisma = require('./prisma');

/**
 * Write an audit log entry. Never throws — audit failure must not break main flow.
 *
 * @param {object|null} officer   — Officer object (or null for anonymous)
 * @param {string}      action    — One of the action strings below
 * @param {object}      opts
 */
async function logAction(officer, action, opts = {}) {
  const { plateNumber = '', controlNumber = '', result = '', req = null, ...extra } = opts;

  let ipAddress = null;
  let userAgent = '';
  if (req) {
    const forwarded = req.headers['x-forwarded-for'];
    ipAddress = forwarded ? forwarded.split(',')[0].trim() : req.ip;
    userAgent = (req.headers['user-agent'] || '').slice(0, 300);
  }

  try {
    await prisma.auditLog.create({
      data: {
        officerId:     officer?.id ?? null,
        action,
        plateNumber,
        controlNumber,
        result,
        ipAddress,
        userAgent,
        extra,
      },
    });
  } catch (_) {
    // Intentionally swallowed
  }
}

// Mirror of Django AuditLog.Action choices
logAction.ACTIONS = {
  LOGIN_SUCCESS:           'LOGIN_SUCCESS',
  LOGIN_FAILURE:           'LOGIN_FAILURE',
  LOGIN_LOCKED:            'LOGIN_LOCKED',
  LOGOUT:                  'LOGOUT',
  TOKEN_REFRESH:           'TOKEN_REFRESH',
  BILL_GENERATED:          'BILL_GENERATED',
  BILL_DUPLICATE_BLOCKED:  'BILL_DUPLICATE_BLOCKED',
  VEHICLE_LOOKUP:          'VEHICLE_LOOKUP',
  PLATE_NOT_FOUND:         'PLATE_NOT_FOUND',
};

module.exports = logAction;

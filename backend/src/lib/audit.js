// ParkiPay — Audit log helper
// Every significant action (login, logout, bill generation, duplicate attempt)
// is written here. Failures are intentionally swallowed — audit errors must
// never disrupt the main request flow.
const prisma = require('./prisma');

const ACTIONS = {
  LOGIN_SUCCESS:          'LOGIN_SUCCESS',
  LOGIN_FAILURE:          'LOGIN_FAILURE',
  LOGIN_LOCKED:           'LOGIN_LOCKED',
  LOGOUT:                 'LOGOUT',
  TOKEN_REFRESH:          'TOKEN_REFRESH',
  BILL_GENERATED:         'BILL_GENERATED',
  BILL_DUPLICATE_BLOCKED: 'BILL_DUPLICATE_BLOCKED',
  VEHICLE_LOOKUP:         'VEHICLE_LOOKUP',
  PLATE_NOT_FOUND:        'PLATE_NOT_FOUND',
};

/**
 * Write an audit log entry.
 *
 * @param {object|null} officer   Prisma Officer row, or null for anonymous events
 * @param {string}      action    One of the ACTIONS constants
 * @param {object}      opts
 * @param {string}      [opts.plateNumber]
 * @param {string}      [opts.controlNumber]
 * @param {string}      [opts.result]
 * @param {object}      [opts.req]   Express request (for IP + user-agent)
 */
async function logAction(officer, action, opts = {}) {
  const { plateNumber = '', controlNumber = '', result = '', req = null, ...extra } = opts;

  let ipAddress = null;
  let userAgent = '';
  if (req) {
    const forwarded = req.headers['x-forwarded-for'];
    ipAddress = forwarded ? forwarded.split(',')[0].trim() : (req.ip || null);
    userAgent = String(req.headers['user-agent'] || '').slice(0, 300);
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
  } catch (_err) {
    // Intentionally swallowed — audit failures must not break the main flow
  }
}

logAction.ACTIONS = ACTIONS;

module.exports = logAction;

jest.setTimeout(30000);

// ParkiPay — Auth route integration tests
// Stack: Jest + Supertest against the real Express app
// DB:    PostgreSQL test instance (see backend-ci.yml for service setup)
//
// Login is ID-only (no password) — see src/routes/auth.js header comment.
// Test user: TEST-0001 / role ATTENDANT (created in beforeAll, cleaned up
// in afterAll).

const request = require('supertest');
const bcrypt  = require('bcryptjs');
const app     = require('../src/app');
const prisma  = require('../src/lib/prisma');

const TEST_EMPLOYEE_ID = 'TEST-0001';

let testOfficer;
let loginTokens; // { access, refresh } — reused across describe blocks

// ── Setup / teardown ──────────────────────────────────────────────────────────

beforeAll(async () => {
  // Clean up any leftover state from a previous run
  await prisma.auditLog.deleteMany({});
  await prisma.blacklistedToken.deleteMany({});
  await prisma.controlNumber.deleteMany({});
  await prisma.officer.deleteMany({ where: { employeeId: TEST_EMPLOYEE_ID } });

  testOfficer = await prisma.officer.create({
    data: {
      employeeId:   TEST_EMPLOYEE_ID,
      fullName:     'Test Officer',
      role:         'ATTENDANT',
      // passwordHash is still a required DB column even though login no
      // longer checks it — kept here only to satisfy the schema.
      passwordHash: await bcrypt.hash('unused', 12),
    },
  });
});

afterAll(async () => {
  await prisma.auditLog.deleteMany({});
  await prisma.blacklistedToken.deleteMany({});
  await prisma.officer.deleteMany({ where: { employeeId: TEST_EMPLOYEE_ID } });
  await prisma.$disconnect();
});

// ── POST /api/auth/login/ ─────────────────────────────────────────────────────

describe('POST /api/auth/login/', () => {
  it('returns 200 with access + refresh tokens and officer profile for a known employee_id', async () => {
    const res = await request(app)
      .post('/api/auth/login/')
      .send({ employee_id: TEST_EMPLOYEE_ID });

    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('access');
    expect(res.body).toHaveProperty('refresh');
    expect(res.body.officer).toMatchObject({
      employeeId: TEST_EMPLOYEE_ID,
      role:       'ATTENDANT',
    });
    // Store tokens for subsequent tests
    loginTokens = { access: res.body.access, refresh: res.body.refresh };
  });

  it('returns 401 for unknown employee_id', async () => {
    const res = await request(app)
      .post('/api/auth/login/')
      .send({ employee_id: 'NOBODY-9999' });

    expect(res.status).toBe(401);
    expect(res.body.error).toBe('invalid_credentials');
  });

  it('returns 401 for an inactive officer', async () => {
    await prisma.officer.update({
      where: { employeeId: TEST_EMPLOYEE_ID },
      data:  { isActive: false },
    });

    const res = await request(app)
      .post('/api/auth/login/')
      .send({ employee_id: TEST_EMPLOYEE_ID });

    expect(res.status).toBe(401);
    expect(res.body.error).toBe('invalid_credentials');

    // Restore for subsequent tests
    await prisma.officer.update({
      where: { employeeId: TEST_EMPLOYEE_ID },
      data:  { isActive: true },
    });
  });

  it('returns 400 when employee_id is missing from the body', async () => {
    const res = await request(app)
      .post('/api/auth/login/')
      .send({});

    expect(res.status).toBe(400);
    expect(res.body.error).toBe('validation_error');
  });
});

// ── GET /api/auth/me/ ─────────────────────────────────────────────────────────

describe('GET /api/auth/me/', () => {
  beforeAll(async () => {
    // Make sure we have fresh tokens in case the inactive-officer test ran first
    const res = await request(app)
      .post('/api/auth/login/')
      .send({ employee_id: TEST_EMPLOYEE_ID });
    loginTokens = { access: res.body.access, refresh: res.body.refresh };
  });

  it('returns officer profile with a valid access token', async () => {
    const res = await request(app)
      .get('/api/auth/me/')
      .set('Authorization', `Bearer ${loginTokens.access}`);

    expect(res.status).toBe(200);
    expect(res.body.employeeId).toBe(TEST_EMPLOYEE_ID);
    // Sensitive fields must NOT be present
    expect(res.body).not.toHaveProperty('passwordHash');
  });

  it('returns 401 with no Authorization header', async () => {
    const res = await request(app).get('/api/auth/me/');
    expect(res.status).toBe(401);
  });

  it('returns 401 with a malformed token', async () => {
    const res = await request(app)
      .get('/api/auth/me/')
      .set('Authorization', 'Bearer not-a-real-token');
    expect(res.status).toBe(401);
  });
});

// ── POST /api/auth/logout/ ────────────────────────────────────────────────────

describe('POST /api/auth/logout/', () => {
  it('blacklists the refresh token and returns 200', async () => {
    // Login fresh to get tokens we can safely blacklist
    const loginRes = await request(app)
      .post('/api/auth/login/')
      .send({ employee_id: TEST_EMPLOYEE_ID });

    const { access, refresh } = loginRes.body;

    const res = await request(app)
      .post('/api/auth/logout/')
      .set('Authorization', `Bearer ${access}`)
      .send({ refresh });

    expect(res.status).toBe(200);
    expect(res.body.detail).toMatch(/logged out/i);
  });

  it('returns 400 when refresh token is missing from body', async () => {
    const res = await request(app)
      .post('/api/auth/logout/')
      .set('Authorization', `Bearer ${loginTokens.access}`)
      .send({});

    expect(res.status).toBe(400);
    expect(res.body.error).toBe('refresh_required');
  });
});

// ── GET /api/health/ ──────────────────────────────────────────────────────────

describe('GET /api/health/', () => {
  it('returns 200 with status ok', async () => {
    const res = await request(app).get('/api/health/');
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('ok');
    expect(res.body.service).toBe('ParkiPay API');
  });
});

// ── 404 ───────────────────────────────────────────────────────────────────────

describe('Unknown routes', () => {
  it('returns 404 for unregistered endpoints', async () => {
    const res = await request(app).get('/api/does-not-exist/');
    expect(res.status).toBe(404);
    expect(res.body.error).toBe('not_found');
  });
});

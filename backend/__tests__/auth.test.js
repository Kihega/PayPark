// ParkiPay — Auth route tests
const request = require('supertest');
const bcrypt  = require('bcryptjs');
const app     = require('../src/app');
const prisma  = require('../src/lib/prisma');

let testOfficer;

beforeAll(async () => {
  // Clean slate
  await prisma.auditLog.deleteMany();
  await prisma.controlNumber.deleteMany();
  await prisma.blacklistedToken.deleteMany();
  await prisma.officer.deleteMany({ where: { employeeId: 'TEST001' } });

  testOfficer = await prisma.officer.create({
    data: {
      employeeId:   'TEST001',
      fullName:     'Test Officer',
      role:         'FIELD_OFFICER',
      passwordHash: await bcrypt.hash('TestPass@1', 12),
    },
  });
});

afterAll(async () => {
  await prisma.officer.deleteMany({ where: { employeeId: 'TEST001' } });
  await prisma.$disconnect();
});

describe('POST /api/auth/login/', () => {
  it('returns 200 with access + refresh + officer on valid credentials', async () => {
    const res = await request(app)
      .post('/api/auth/login/')
      .send({ employee_id: 'TEST001', password: 'TestPass@1' });
    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('access');
    expect(res.body).toHaveProperty('refresh');
    expect(res.body.officer.employeeId).toBe('TEST001');
  });

  it('returns 401 on wrong password', async () => {
    const res = await request(app)
      .post('/api/auth/login/')
      .send({ employee_id: 'TEST001', password: 'WrongPass' });
    expect(res.status).toBe(401);
    expect(res.body.error).toBe('invalid_credentials');
  });

  it('returns 401 for unknown employee_id', async () => {
    const res = await request(app)
      .post('/api/auth/login/')
      .send({ employee_id: 'NOBODY', password: 'anything' });
    expect(res.status).toBe(401);
  });
});

describe('GET /api/auth/me/', () => {
  it('returns officer profile with valid access token', async () => {
    const loginRes = await request(app)
      .post('/api/auth/login/')
      .send({ employee_id: 'TEST001', password: 'TestPass@1' });

    const res = await request(app)
      .get('/api/auth/me/')
      .set('Authorization', `Bearer ${loginRes.body.access}`);

    expect(res.status).toBe(200);
    expect(res.body.employeeId).toBe('TEST001');
  });

  it('returns 401 with no token', async () => {
    const res = await request(app).get('/api/auth/me/');
    expect(res.status).toBe(401);
  });
});

describe('POST /api/auth/logout/', () => {
  it('blacklists refresh token and returns 200', async () => {
    const loginRes = await request(app)
      .post('/api/auth/login/')
      .send({ employee_id: 'TEST001', password: 'TestPass@1' });

    const res = await request(app)
      .post('/api/auth/logout/')
      .set('Authorization', `Bearer ${loginRes.body.access}`)
      .send({ refresh: loginRes.body.refresh });

    expect(res.status).toBe(200);
  });
});

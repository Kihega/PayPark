#!/usr/bin/env python3
"""
ParkiPay — consolidated fix script
====================================

Context: a prior migration ("collapse_roles") simplified OfficerRole to
just ATTENDANT / SUPERVISOR and the login flow to ID-only (no password
field, see src/routes/auth.js header comment: "v2: employee-ID only, no
password"). The route, seed, schema, and mobile client are all already
consistent with this — verified by grep across the whole tree.

The ONE real remaining inconsistency is backend/__tests__/auth.test.js,
which still tests the OLD contract:
  - sends a `password` field the route never reads
  - expects `role: 'FIELD_OFFICER'` (enum value no longer exists)
  - expects a `remaining_attempts` field that login never returns
  - expects 401 "wrong password" behaviour that doesn't exist anymore
This test currently fails against the live code, which is exactly the
kind of thing that causes "did everything ship correctly?" confusion
in CI.

This script:
  1. Rewrites auth.test.js to match the real ID-only login contract.
  2. Deletes leftover *.bak / *.bak2 / *.bak3 files from earlier patch
     sessions (mobile/services/api.ts.bak[2], login.tsx.bak* if present).
  3. Generates a clean root-level README.md.
  4. Commits everything as one commit (no backup files are created —
     git history is the backup).

Run from the REPO ROOT (the directory containing backend/ and mobile/):
    python3 fix_tests_and_readme.py
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT          = Path(".")
BACKEND       = ROOT / "backend"
MOBILE        = ROOT / "mobile"
TEST_FILE     = BACKEND / "__tests__" / "auth.test.js"
README_PATH   = ROOT / "README.md"


def fail(msg: str) -> None:
    print(f"❌ {msg}")
    sys.exit(1)


def require_dir(path: Path, what: str) -> None:
    if not path.is_dir():
        fail(f"{path} not found — run this script from the repo root ({what}).")


# ── 1. Rewrite auth.test.js to match the real ID-only contract ─────────────

NEW_AUTH_TEST = """jest.setTimeout(30000);

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
"""


def fix_auth_test() -> bool:
    if not TEST_FILE.exists():
        print(f"⚠️  {TEST_FILE} not found — skipping test fix.")
        return False

    current = TEST_FILE.read_text(encoding="utf-8")
    if "FIELD_OFFICER" not in current and "remaining_attempts" not in current:
        print(f"ℹ️  {TEST_FILE} already matches the current contract — no change needed.")
        return False

    TEST_FILE.write_text(NEW_AUTH_TEST, encoding="utf-8")
    print(f"✅ Rewrote {TEST_FILE} to match the ID-only login contract")
    return True


# ── 2. Remove leftover .bak clutter from earlier patch sessions ────────────

BAK_GLOBS = ["*.bak", "*.bak2", "*.bak3", "*.bak_patch*"]


def remove_bak_files() -> list[Path]:
    removed = []
    for base in (BACKEND, MOBILE):
        if not base.is_dir():
            continue
        for pattern in BAK_GLOBS:
            for p in base.rglob(pattern):
                if "node_modules" in p.parts:
                    continue
                p.unlink()
                removed.append(p)
    for p in removed:
        print(f"🗑️  Removed stray file: {p}")
    if not removed:
        print("ℹ️  No .bak clutter found.")
    return removed


# ── 3. Generate README.md ───────────────────────────────────────────────────

README_CONTENT = """# ParkiPay

Government parking management system for Tanzania. Field attendants issue
digital parking bills against a vehicle's number plate; supervisors manage
officers, locations, and the vehicle registry.

## Stack

| Layer      | Technology                                   |
|------------|-----------------------------------------------|
| Mobile app | React Native (Expo) + TypeScript              |
| Backend    | Node.js + Express                              |
| ORM        | Prisma                                         |
| Database   | PostgreSQL (Supabase)                          |
| Cache      | Redis (Upstash)                                |
| SMS        | Twilio (active) / Africa's Talking (legacy)    |
| Email      | Resend                                         |
| Deploy     | Render (backend) · EAS / Expo Go (mobile)      |

## Repository layout

```
backend/   Express API, Prisma schema + migrations, seed data, tests
mobile/    Expo app (attendant + supervisor screens)
```

## Domain conventions

- **Attendant** employee IDs: `TZ-XXXX` (e.g. `TZ-0001`)
- **Supervisor** employee IDs: `SUP-XXXX` (e.g. `SUP-0001`)
- **Vehicle plates** (Tanzania format): `T` + 3 digits + 3 letters (e.g. `T123ABC`)
- **Officer roles** (`OfficerRole` enum): `ATTENDANT`, `SUPERVISOR` — these
  are the only two valid values. Earlier drafts of this project used
  `ADMIN` / `FIELD_OFFICER`; that enum was collapsed and those values no
  longer exist anywhere in the schema, routes, or mobile client.

## Authentication

Login is **employee-ID only** — there is currently no password check on
`POST /api/auth/login/`. The officer just needs to exist, be active, and
match the employee ID sent from the app. This is a known, intentional
simplification for the current phase; see `backend/src/routes/auth.js`
for the exact contract before changing it.

## Getting started

### 1. Backend

```bash
cd backend
npm install
cp .env.example .env   # fill in DATABASE_URL, SECRET_KEY, etc.
npm run db:push        # or: npm run db:migrate (in CI / prod)
npm run db:seed
npm run dev             # nodemon, http://localhost:8000
```

Seeded test accounts after `npm run db:seed`:

| Role       | Employee ID | Notes                          |
|------------|-------------|---------------------------------|
| Attendant  | `TZ-0001`   | role `ATTENDANT`                |
| Supervisor | `SUP-0001`  | role `SUPERVISOR`               |

Login only needs the employee ID (see Authentication above) — any
password value sent by an older client build is simply ignored.

Health check: `GET http://localhost:8000/api/health/`

### 2. Mobile app

```bash
cd mobile
npm install
cp .env.example .env   # see comments inside for which line to uncomment
npx expo start
```

`mobile/.env.example` walks through four scenarios for `EXPO_PUBLIC_API_URL`:

- **Android emulator** — leave it commented out (auto-detects `10.0.2.2:8000`)
- **iOS simulator** — leave it commented out (auto-detects `localhost:8000`)
- **Physical device (USB/Wi-Fi)** — set it to your computer's LAN IP,
  e.g. `http://192.168.1.42:8000`. This is the single most common cause
  of a confusing **"Endpoint not found"** error on a real phone: the
  request goes to localhost-on-the-phone instead of your dev machine,
  hits something else entirely (or nothing), and the 404 you see may not
  even be coming from this backend.
- **Render (staging/production)** — point at your deployed Render URL.
  Note Render's free tier sleeps after 15 minutes idle; the first request
  after a sleep can take 30–50 seconds to wake up.

## Useful backend scripts

| Command              | What it does                                |
|-----------------------|----------------------------------------------|
| `npm run dev`         | Start API with nodemon (auto-restart)        |
| `npm start`           | Start API (production mode)                  |
| `npm run db:push`     | Push schema to DB without a migration file   |
| `npm run db:migrate`  | Apply migrations (`prisma migrate deploy`)   |
| `npm run db:seed`     | Seed test officers/location/vehicle          |
| `npm run db:studio`   | Open Prisma Studio (visual DB browser)        |
| `npm test`            | Run Jest + Supertest integration tests       |
| `npm run lint`        | ESLint over `src/`                            |

## API surface

| Method | Path                              | Auth        | Purpose                          |
|--------|------------------------------------|-------------|------------------------------------|
| GET    | `/api/health/`                     | none        | Liveness + DB connectivity check  |
| POST   | `/api/auth/login/`                 | none        | Log in with `employee_id`          |
| POST   | `/api/auth/refresh/`               | none        | Rotate access token                |
| POST   | `/api/auth/logout/`                | none        | Blacklist refresh token             |
| GET    | `/api/auth/me/`                    | Bearer      | Current officer profile            |
| GET    | `/api/vehicles/lookup/`            | Bearer      | Look up a vehicle by plate         |
| GET    | `/api/vehicles/locations/`         | Bearer      | List parking locations             |
| POST   | `/api/vehicles/ocr-plate/`         | Bearer      | OCR a plate from a photo           |
| POST   | `/api/billing/generate/`           | Bearer      | Issue a parking bill                |
| GET    | `/api/billing/history/`            | Bearer      | Officer's billing history           |
| GET    | `/api/billing/stats/`              | Bearer      | Billing stats                       |
| GET    | `/api/billing/active-bill/`        | Bearer      | Check for an active bill on a plate |
| GET    | `/api/billing/:cn/status/`         | Bearer      | Bill status by control number       |
| GET    | `/api/admin/officers/`             | Supervisor  | List officers                       |
| POST   | `/api/admin/officers/`             | Supervisor  | Create an officer                   |
| DELETE | `/api/admin/officers/:id/`         | Supervisor  | Remove an officer                   |
| PATCH  | `/api/admin/officers/:id/location/`| Supervisor  | Reassign officer's location         |
| GET    | `/api/admin/locations/`            | Supervisor  | List parking locations              |
| GET    | `/api/admin/vehicles/`             | Supervisor  | List registered vehicles            |
| POST   | `/api/admin/vehicles/`             | Supervisor  | Register a vehicle (SMS owner)      |
| DELETE | `/api/admin/vehicles/:id/`         | Supervisor  | Remove a vehicle from the registry  |

All routes are mounted with a **trailing slash** (e.g. `/api/auth/login/`,
not `/api/auth/login`) — the mobile client's `api.ts` already matches this,
but keep it in mind if you add a new endpoint or test one manually with
curl/Postman.

## Deployment

- **Backend**: Render, via `backend/Dockerfile`. `RENDER_DEPLOY_HOOK_URL`
  (set as a GitHub Secret) lets CI trigger a deploy after merging to `main`.
- **Database**: Supabase Postgres — use the **transaction pooler** port
  `6543` for `DATABASE_URL`, not the direct `5432` port.
- **Redis**: Upstash, TLS connection string (`rediss://`).
- `main` is protected by a GitHub ruleset — changes must go through a pull
  request; direct pushes to `main` will be rejected even from CI.

## Troubleshooting

**"Endpoint not found" on login** — almost always one of:
1. The backend you're hitting doesn't have the route at all (stale deploy,
   or local server running old code — restart it after pulling).
2. `EXPO_PUBLIC_API_URL` in `mobile/.env` doesn't point at a server that's
   actually running (wrong LAN IP, backend not started, wrong port).
3. The DB hasn't been seeded yet, so even a *correct* request 401s — but
   if you're seeing a literal 404 JSON body (`{"error":"not_found",...}`),
   that's the route-matching 404 in `backend/src/app.js`, not an auth
   failure, which means it's (1) or (2), not missing seed data.

**Seed crashes with `Argument passwordHash is missing`** — every officer
row requires a `passwordHash` even though login doesn't check it yet
(the column is still required by the schema). Add one with
`await bcrypt.hash('SomePassword', 12)` in any new seed block.

**Seed crashes with an invalid enum value** — `OfficerRole` only accepts
`ATTENDANT` or `SUPERVISOR`. If you see `ADMIN` or `FIELD_OFFICER`
anywhere in a seed or patch script, it's stale; update it to the current
two values.
"""


def write_readme() -> None:
    README_PATH.write_text(README_CONTENT, encoding="utf-8")
    print(f"✅ Wrote {README_PATH}")


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    require_dir(BACKEND, "expected backend/ subfolder")
    require_dir(MOBILE, "expected mobile/ subfolder")

    changed_test = fix_auth_test()
    removed_baks = remove_bak_files()
    write_readme()

    if not (changed_test or removed_baks):
        print("ℹ️  Only README.md was added/updated.")

    # ── Commit ───────────────────────────────────────────────────────────
    subprocess.run(["git", "add", "-A"], check=True)
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
    )
    if result.returncode == 0:
        print("ℹ️  Nothing to commit (working tree already matches).")
        return

    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            "fix(tests): align auth.test.js with ID-only login contract; "
            "chore: remove stray .bak files; docs: add README",
        ],
        check=True,
    )
    print("✅ Committed")
    print("\nNext step: push to a feature branch and open a PR — `main` is")
    print("protected and rejects direct pushes:")
    print("    git checkout -b fix/auth-tests-and-readme")
    print("    git push origin fix/auth-tests-and-readme")


if __name__ == "__main__":
    main()

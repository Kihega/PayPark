# ParkiPay

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

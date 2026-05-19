# ParkiPay 🅿️

**Government Parking Fee Collection System — Tanzania**

A mobile-first system that digitises and standardises parking fee collection across
government parking areas, with a global **duplicate-billing prevention engine** at its core.

---

## ⚠️ Tech Stack Correction

The original README incorrectly described the backend as Django. The actual implementation is:

| Layer       | Technology                                  |
|-------------|---------------------------------------------|
| **Backend** | **Node.js 20 + Express 4**                  |
| **ORM**     | **Prisma 5** (type-safe PostgreSQL client)  |
| **Auth**    | **jsonwebtoken** — access + refresh tokens with rotation & DB blacklist |
| **Validation** | **Zod**                                  |
| **Security**| Helmet · CORS · express-rate-limit          |
| **Testing** | Jest + Supertest                            |
| Mobile      | React Native 0.81 + Expo SDK 54             |
| Navigation  | Expo Router (file-based)                    |
| State       | Zustand                                     |
| API Client  | Axios                                       |
| Token Store | expo-secure-store                           |
| Database    | PostgreSQL (Supabase)                       |
| SMS         | Africa's Talking                            |
| Email       | Resend                                      |
| Deploy      | Render (API) · EAS Build (mobile)           |
| CI/CD       | GitHub Actions                              |

---

## Project Structure

```
parkipay/
├── backend/
│   ├── src/
│   │   ├── app.js              # Express app factory
│   │   ├── server.js           # HTTP server entry point
│   │   ├── config/index.js     # Central config from env vars
│   │   ├── lib/
│   │   │   ├── prisma.js       # Singleton Prisma client
│   │   │   ├── jwt.js          # Token sign / verify / blacklist
│   │   │   ├── audit.js        # Audit log helper
│   │   │   └── controlNumber.js# CN generation + duplicate check
│   │   ├── middleware/
│   │   │   ├── auth.js         # Bearer token middleware + role guards
│   │   │   └── errorHandler.js # Global Express error handler
│   │   └── routes/
│   │       ├── health.js       # GET /api/health/
│   │       ├── auth.js         # Login / refresh / logout / me
│   │       ├── vehicles.js     # Plate lookup + locations list
│   │       └── billing.js      # Generate CN + history + status
│   ├── prisma/
│   │   ├── schema.prisma       # Database schema
│   │   └── seed.js             # Dev seed (test users + sample data)
│   ├── __tests__/
│   │   └── auth.test.js        # Jest + Supertest auth suite
│   ├── .env.example            # Environment variable template
│   ├── Dockerfile              # Production image (Node 20 Alpine)
│   ├── docker-compose.yml      # Local dev (API + local Postgres)
│   ├── entrypoint.sh           # Docker entrypoint
│   └── package.json
│
└── mobile/
    ├── app/
    │   ├── index.tsx           # Splash / loading screen
    │   ├── (auth)/login.tsx    # Login screen
    │   └── (app)/home.tsx      # Authenticated home
    ├── constants/
    │   ├── theme.ts            # TATURA colours & typography
    │   └── api.ts              # API base URL & routes
    ├── hooks/useAuth.ts        # Login / logout hook
    ├── services/api.ts         # Axios client + JWT refresh interceptor
    └── package.json
```

---

## Test Users

| Role          | Employee ID | Password       |
|---------------|-------------|----------------|
| Admin         | `ADMIN001`  | `Admin@1234`   |
| Field Officer | `OFF001`    | `Officer@1234` |

> Run `npm run db:seed` after migrations to create these accounts.

---

## Backend Setup

### Prerequisites
- Node.js 20+
- Docker & Docker Compose (for local DB)
- A Supabase project **or** use the bundled local Postgres via docker-compose

### Local Development (Docker — recommended)

```bash
cd backend

# 1. Copy env file and fill in values
cp .env.example .env

# 2. Start API + local Postgres
docker-compose up --build

# API is live at http://localhost:8000
```

### Local Development (without Docker)

```bash
cd backend

# 1. Install dependencies
npm install

# 2. Copy and fill in .env
cp .env.example .env
# Set DATABASE_URL to your Supabase or local Postgres connection string

# 3. Generate Prisma client
npm run db:generate

# 4. Run migrations
npm run db:migrate

# 5. Seed test data (creates ADMIN001 + OFF001)
npm run db:seed

# 6. Start dev server with hot reload
npm run dev
```

### API Endpoints

| Method | Endpoint                    | Auth | Description              |
|--------|-----------------------------|------|--------------------------|
| GET    | `/api/health/`              | No   | Health check             |
| POST   | `/api/auth/login/`          | No   | Officer login            |
| POST   | `/api/auth/refresh/`        | No   | Refresh JWT pair         |
| POST   | `/api/auth/logout/`         | Yes  | Logout + blacklist token |
| GET    | `/api/auth/me/`             | Yes  | Officer profile          |
| GET    | `/api/vehicles/lookup/`     | Yes  | Plate number lookup      |
| GET    | `/api/vehicles/locations/`  | Yes  | Active parking locations |
| POST   | `/api/billing/generate/`    | Yes  | Generate control number  |
| GET    | `/api/billing/history/`     | Yes  | Today's bill history     |
| GET    | `/api/billing/:cn/status/`  | Yes  | Bill status by CN        |

### Run Tests

```bash
cd backend
npm test              # run all tests
npm run test:coverage # with coverage report
```

---

## Mobile Setup

```bash
cd mobile
npm install
cp .env.example .env   # set EXPO_PUBLIC_API_URL=http://localhost:8000

# Expo Go (physical device or emulator)
npm start

# Android emulator
npm run android

# iOS simulator (macOS only)
npm run ios
```

---

## Sprint Roadmap

| Sprint | Focus                                              | Status      |
|--------|----------------------------------------------------|-------------|
| 0      | Project setup, DB schema, health check, env vars   | ✅ Done     |
| 1      | Officer auth (login/logout/JWT), login screen      | ✅ Done     |
| 2      | Vehicle plate verification, registry lookup        | 🔜 Next     |
| 3      | Control number generation, duplicate prevention    | 📋 Planned  |
| 4      | SMS / Email notifications                          | 📋 Planned  |
| 5      | Billing history, admin reporting                   | 📋 Planned  |
| 6      | Testing, security audit, production deploy         | 📋 Planned  |

---

*ParkiPay — © 2026 Government of Tanzania*

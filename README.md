# ParkiPay 🅿️

**Government Parking Fee Collection System — Tanzania**

A mobile-first system that digitises and standardises parking fee collection across government parking areas, with a global **duplicate-billing prevention engine** at its core.

---

## Project Structure

```
parkipay/
├── backend/              # Django REST API
│   ├── core/             # Project settings, URLs, exceptions
│   ├── apps/
│   │   ├── accounts/     # Officer auth, roles, audit log
│   │   ├── vehicles/     # Vehicle registry, parking locations
│   │   ├── billing/      # Control numbers, duplicate prevention
│   │   └── notifications/# SMS (Africa's Talking) + Email (Resend)
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── requirements.txt
│   └── .env.example
│
└── mobile/               # React Native + Expo app
    ├── app/
    │   ├── index.tsx     # Splash / loading screen
    │   ├── (auth)/       # Login screen
    │   └── (app)/        # Authenticated screens
    ├── constants/
    │   ├── theme.ts      # TATURA colours & typography
    │   └── api.ts        # API base URL & routes
    ├── store/
    │   └── authStore.ts  # Zustand auth state
    └── services/
        └── api.ts        # Axios client with JWT refresh
```

---

## Backend Setup

### Prerequisites
- Python 3.12+
- Docker & Docker Compose
- Supabase project (PostgreSQL)
- Redis (included in docker-compose)

### Local Development

```bash
cd backend

# 1. Copy and fill in environment variables
cp .env.example .env
# Edit .env with your Supabase DATABASE_URL, SECRET_KEY, etc.

# 2. Run with Docker Compose
docker-compose up --build

# OR without Docker:
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser  # employee_id = "ADMIN001"
python manage.py runserver
```

### API Endpoints (Sprint 0 & 1)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/health/` | No | Health check |
| POST | `/api/auth/login/` | No | Officer login |
| POST | `/api/auth/refresh/` | No | Refresh JWT |
| POST | `/api/auth/logout/` | Yes | Logout + blacklist |
| GET | `/api/auth/me/` | Yes | Officer profile |

---

## Mobile Setup

### Prerequisites
- Node.js 20+
- Expo CLI: `npm install -g expo`
- Android Studio / Xcode (for emulator)

```bash
cd mobile

# 1. Install dependencies
npm install

# 2. Set API URL (optional — defaults to localhost:8000)
# Create .env: EXPO_PUBLIC_API_URL=http://your-backend-url

# 3. Run on Android
npm run android

# 4. Run on Expo Go
npm start
```

---

## Sprint Roadmap

| Sprint | Focus | Status |
|--------|-------|--------|
| 0 | Project setup, DB schemas, health check, env vars | ✅ Done |
| 1 | Officer auth (login/logout/JWT), login screen | ✅ Done |
| 2 | Vehicle plate verification, registry lookup | 🔜 Next |
| 3 | Control number generation, duplicate prevention | 📋 Planned |
| 4 | SMS / Email notifications | 📋 Planned |
| 5 | Billing history, admin reporting | 📋 Planned |
| 6 | Testing, security audit, production deploy | 📋 Planned |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Mobile | React Native 0.81 + Expo SDK 54 |
| Navigation | Expo Router (file-based) |
| State | Zustand |
| API Client | Axios + React Query |
| Token Storage | expo-secure-store |
| Backend | Django 5.1 + DRF |
| Auth | SimpleJWT + token blacklisting |
| Tasks | Celery + Redis |
| Database | PostgreSQL (Supabase) |
| SMS | Africa's Talking |
| Email | Resend |
| Deploy | Render (API) + EAS Build (mobile) |

---

*ParkiPay — © 2026 Government of Tanzania*

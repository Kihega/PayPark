"""
ParkiPay — Base Django Settings
Shared across all environments. Never import this directly; import local.py
or production.py instead.
"""
from datetime import timedelta
from pathlib import Path

from decouple import Csv, config

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ── Security ──────────────────────────────────────────────────────────────────
SECRET_KEY = config(
    "SECRET_KEY",
    default="unsafe-dev-key"
)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv(),
                       default="localhost,127.0.0.1")

# ── Apps ──────────────────────────────────────────────────────────────────────
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_celery_beat",
]

LOCAL_APPS = [
    "apps.accounts",
    "apps.vehicles",
    "apps.billing",
    "apps.notifications",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ── Middleware ─────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"
WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"

# ── Templates ─────────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL = config("DATABASE_URL", default="sqlite:///tmp/build.db")


def _parse_db_url(url: str) -> dict:
    """
    Parse DATABASE_URL into a Django DATABASES dict.
    Supports:
      postgresql://user:pass@host:port/dbname
      sqlite:///path/to/db.sqlite3  (CI / local fallback)
    """
    if url.startswith("sqlite"):
        path = url.split(
            "sqlite:///", 1)[1] if ":///" in url else url.split("sqlite://", 1)[1]
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / path if not path.startswith("/") else path,
        }

    # PostgreSQL
    rest = url.split("://", 1)[1]          # user:pass@host:port/name
    userinfo, hostinfo = rest.rsplit("@", 1)
    user, password = userinfo.split(":", 1)
    hostport, dbname = hostinfo.split("/", 1)
    dbname = dbname.split("?")[0]
    if ":" in hostport:
        host, port = hostport.split(":", 1)
    else:
        host, port = hostport, "5432"

    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": dbname,
        "USER": user,
        "PASSWORD": password,
        "HOST": host,
        "PORT": port,
        "CONN_MAX_AGE": 60,
        "OPTIONS": {"sslmode": "require"},
    }


DATABASES = {"default": _parse_db_url(DATABASE_URL)}

# ── Custom Auth ───────────────────────────────────────────────────────────────
AUTH_USER_MODEL = "accounts.Officer"
AUTHENTICATION_BACKENDS = [
    "apps.accounts.backends.EmployeeIDBackend",
]

# ── Password Validation ───────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── Django REST Framework ─────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "20/min",
        "user": "60/min",
        "login": "5/min",
    },
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
}

# ── JWT ───────────────────────────────────────────────────────────────────────
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=config("JWT_ACCESS_TOKEN_LIFETIME_MINUTES",
                       cast=int, default=60)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=config("JWT_REFRESH_TOKEN_LIFETIME_DAYS", cast=int, default=7)
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "TOKEN_OBTAIN_SERIALIZER": "apps.accounts.serializers.ParkiPayTokenObtainSerializer",
}

# ── Celery ────────────────────────────────────────────────────────────────────
CELERY_BROKER_URL = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Africa/Dar_es_Salaam"

# ── Internationalisation ──────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Dar_es_Salaam"
USE_I18N = True
USE_TZ = True

# ── Static Files ──────────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ── Default PK ────────────────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── App-specific config ───────────────────────────────────────────────────────
CONTROL_NUMBER_VALIDITY_HOURS = config(
    "CONTROL_NUMBER_VALIDITY_HOURS", cast=int, default=5)
MAX_FAILED_LOGIN_ATTEMPTS = config(
    "MAX_FAILED_LOGIN_ATTEMPTS", cast=int, default=5)
LOCKOUT_DURATION_MINUTES = config(
    "LOCKOUT_DURATION_MINUTES", cast=int, default=15)

# ── Notifications ─────────────────────────────────────────────────────────────
AT_USERNAME = config("AT_USERNAME", default="sandbox")
AT_API_KEY = config("AT_API_KEY", default="")
AT_SENDER_ID = config("AT_SENDER_ID", default="ParkiPay")
AT_SANDBOX = config("AT_SANDBOX", cast=bool, default=True)

RESEND_API_KEY = config("RESEND_API_KEY", default="")
EMAIL_FROM = config("EMAIL_FROM", default="noreply@parkipay.go.tz")

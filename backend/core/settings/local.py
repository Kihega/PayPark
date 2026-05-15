"""ParkiPay — Local Development Settings"""
from .base import *  # noqa

DEBUG = True

# Allow all hosts in local dev
ALLOWED_HOSTS = ["*"]

# CORS: allow Expo dev server
CORS_ALLOW_ALL_ORIGINS = True

# Django Debug Toolbar (optional — install separately)
# INSTALLED_APPS += ["debug_toolbar"]

# Verbose logging in development
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "apps": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
    },
}

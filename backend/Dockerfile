# ── ParkiPay Backend Dockerfile ───────────────────────────────────────────────
FROM python:3.12-slim AS base

# Non-root user for security
RUN groupadd -r parkipay && useradd -r -g parkipay parkipay

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .
ENV SECRET_KEY=dummysecret
# Static files
RUN mkdir -p staticfiles && \
    DJANGO_ENV=local python manage.py collectstatic --noinput || true

# Correct ownership
RUN chown -R parkipay:parkipay /app

USER parkipay

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]

# ── ParkiPay Backend — Production Docker Image ───────────────────────────────

# ── Stage 1: Install dependencies + Generate Prisma ──────────────────────────
FROM node:20-alpine AS deps

WORKDIR /app

# Prisma requires openssl
RUN apk add --no-cache openssl

# Copy package files
COPY package*.json ./

# Copy Prisma schema before install
COPY prisma ./prisma

# Install dependencies (includes Prisma CLI)
RUN npm ci

# Generate Prisma client
RUN npx prisma generate

# Remove dev dependencies for production
RUN npm prune --omit=dev


# ── Stage 2: Runtime image ───────────────────────────────────────────────────
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# Prisma runtime dependency
RUN apk add --no-cache openssl

# Create non-root user
RUN addgroup -S parkipay \
    && adduser -S parkipay -G parkipay


# Copy production dependencies
COPY --from=deps /app/node_modules ./node_modules

# Copy Prisma generated client
COPY --from=deps /app/node_modules/.prisma ./node_modules/.prisma


# Copy application files
COPY prisma ./prisma
COPY src ./src
COPY package*.json ./
COPY entrypoint.sh ./entrypoint.sh


# Permissions
RUN chmod +x ./entrypoint.sh \
    && chown -R parkipay:parkipay /app


USER parkipay


EXPOSE 8000


ENTRYPOINT ["./entrypoint.sh"]

# ── ParkiPay Backend — Production Image ──────────────────────────────────────

# ── Stage 1: Install production dependencies ──────────────────────────────────
FROM node:20-alpine AS deps
WORKDIR /app

# openssl required by Prisma's query engine
RUN apk add --no-cache openssl

# Copy package files
COPY package*.json ./

# IMPORTANT: Copy prisma BEFORE npm ci
COPY prisma ./prisma

# Install dependencies
RUN npm ci --omit=dev

# ── Stage 2: Generate Prisma client ───────────────────────────────────────────
FROM deps AS builder

# Regenerate Prisma client explicitly
RUN npx prisma generate

# ── Stage 3: Final runtime image ─────────────────────────────────────────────
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

# openssl needed at runtime by Prisma
RUN apk add --no-cache openssl

# Non-root user for security
RUN addgroup -S parkipay && adduser -S parkipay -G parkipay

# Copy only what is needed to run
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/node_modules/.prisma ./node_modules/.prisma

COPY prisma ./prisma
COPY src ./src
COPY package*.json ./
COPY entrypoint.sh ./entrypoint.sh

RUN chmod +x ./entrypoint.sh && chown -R parkipay:parkipay /app

USER parkipay

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]

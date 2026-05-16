# ── ParkiPay Backend — Node 20 Alpine ────────────────────────────────────────
FROM node:20-alpine AS base
WORKDIR /app

# Install OS deps needed by Prisma
RUN apk add --no-cache openssl

# ── Dependencies ──────────────────────────────────────────────────────────────
FROM base AS deps
COPY package*.json ./
RUN npm ci --omit=dev

# ── Build / generate Prisma client ────────────────────────────────────────────
FROM deps AS builder
COPY prisma ./prisma
RUN npx prisma generate

# ── Final image ───────────────────────────────────────────────────────────────
FROM base AS runner
ENV NODE_ENV=production

# Create non-root user
RUN addgroup -S parkipay && adduser -S parkipay -G parkipay

COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/node_modules/.prisma ./node_modules/.prisma
COPY prisma   ./prisma
COPY src      ./src
COPY entrypoint.sh ./entrypoint.sh

RUN chown -R parkipay:parkipay /app
USER parkipay

EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]

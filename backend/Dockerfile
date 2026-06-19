# ── ParkiPay Backend — Production Image ─────────────────────────────────────

FROM node:20-alpine AS deps

WORKDIR /app

RUN apk add --no-cache openssl

COPY package*.json ./
COPY prisma ./prisma

RUN npm ci



RUN npm prune --omit=dev


# ── Runtime stage ────────────────────────────────────────────────────────────
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

RUN apk add --no-cache openssl

RUN addgroup -S parkipay \
    && adduser -S parkipay -G parkipay

COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/node_modules/.prisma ./node_modules/.prisma

COPY prisma ./prisma
COPY src ./src
COPY package*.json ./
COPY entrypoint.sh ./entrypoint.sh

RUN chmod +x ./entrypoint.sh \
    && chown -R parkipay:parkipay /app

USER parkipay

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]

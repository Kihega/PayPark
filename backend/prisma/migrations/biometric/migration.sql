-- ParkiPay biometric migration
-- Safe to run multiple times (CREATE TABLE IF NOT EXISTS + INSERT ... ON CONFLICT DO NOTHING)

CREATE TABLE IF NOT EXISTS officer_biometrics (
  id           SERIAL       PRIMARY KEY,
  officer_id   INTEGER      NOT NULL UNIQUE REFERENCES officers(id) ON DELETE CASCADE,
  token        VARCHAR(128) NOT NULL UNIQUE,
  device_hint  VARCHAR(64)  NOT NULL DEFAULT 'device',
  is_active    BOOLEAN      NOT NULL DEFAULT TRUE,
  created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_officer_biometrics_token
  ON officer_biometrics(token) WHERE is_active = TRUE;

-- ── Seed: insert a test biometric row for the first officer (idempotent) ──────
-- The token below is a placeholder; the real flow generates it on the device.
-- Remove this block (or replace token) before deploying to production.
INSERT INTO officer_biometrics (officer_id, token, device_hint, is_active)
SELECT
  o.id,
  'seed_token_replace_me_64chars_aabbccddeeff00112233445566778899aabb',
  'seed_device',
  FALSE          -- disabled by default so it cannot be used until device enrols
FROM officers o
ORDER BY o.id
LIMIT 1
ON CONFLICT (officer_id) DO NOTHING;

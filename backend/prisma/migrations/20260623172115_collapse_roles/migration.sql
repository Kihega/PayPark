-- Collapse OfficerRole: remove ADMIN, rename FIELD_OFFICER -> ATTENDANT
-- Run with DIRECT_URL (migrations require the direct, non-pooled connection).

-- 1. Move any existing ADMIN officers to SUPERVISOR before the enum changes.
UPDATE "officers" SET "role" = 'SUPERVISOR' WHERE "role" = 'ADMIN';

-- 2. Rename FIELD_OFFICER -> ATTENDANT in place.
ALTER TYPE "OfficerRole" RENAME VALUE 'FIELD_OFFICER' TO 'ATTENDANT';

-- 3. Rebuild the enum type without ADMIN (Postgres can't drop enum values
--    directly, so the type is recreated and the column re-pointed at it).
ALTER TYPE "OfficerRole" RENAME TO "OfficerRole_old";
CREATE TYPE "OfficerRole" AS ENUM ('ATTENDANT', 'SUPERVISOR');
ALTER TABLE "officers"
  ALTER COLUMN "role" DROP DEFAULT,
  ALTER COLUMN "role" TYPE "OfficerRole" USING ("role"::text::"OfficerRole"),
  ALTER COLUMN "role" SET DEFAULT 'ATTENDANT';
DROP TYPE "OfficerRole_old";

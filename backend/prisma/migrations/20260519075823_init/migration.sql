-- CreateEnum
CREATE TYPE "OfficerRole" AS ENUM ('FIELD_OFFICER', 'SUPERVISOR', 'ADMIN');

-- CreateEnum
CREATE TYPE "VehicleCategory" AS ENUM ('MOTORCYCLE', 'PRIVATE_CAR', 'MINIBUS', 'BUS', 'TRUCK', 'GOVERNMENT');

-- CreateEnum
CREATE TYPE "BillStatus" AS ENUM ('ACTIVE', 'EXPIRED', 'PAID');

-- CreateTable
CREATE TABLE "officers" (
    "id" SERIAL NOT NULL,
    "employee_id" TEXT NOT NULL,
    "full_name" TEXT NOT NULL,
    "phone" TEXT NOT NULL DEFAULT '',
    "email" TEXT NOT NULL DEFAULT '',
    "role" "OfficerRole" NOT NULL DEFAULT 'FIELD_OFFICER',
    "password_hash" TEXT NOT NULL,
    "location_id" INTEGER,
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "failed_login_attempts" INTEGER NOT NULL DEFAULT 0,
    "locked_until" TIMESTAMP(3),
    "last_login" TIMESTAMP(3),
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "officers_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "audit_logs" (
    "id" SERIAL NOT NULL,
    "officer_id" INTEGER,
    "action" TEXT NOT NULL,
    "plate_number" TEXT NOT NULL DEFAULT '',
    "control_number" TEXT NOT NULL DEFAULT '',
    "result" TEXT NOT NULL DEFAULT '',
    "ip_address" TEXT,
    "user_agent" TEXT NOT NULL DEFAULT '',
    "extra" JSONB NOT NULL DEFAULT '{}',
    "timestamp" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "audit_logs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "parking_locations" (
    "id" SERIAL NOT NULL,
    "name" TEXT NOT NULL,
    "region" TEXT NOT NULL,
    "district" TEXT NOT NULL DEFAULT '',
    "address" TEXT NOT NULL DEFAULT '',
    "latitude" DECIMAL(10,7),
    "longitude" DECIMAL(10,7),
    "fee_motorcycle" DECIMAL(10,2) NOT NULL DEFAULT 500,
    "fee_private_car" DECIMAL(10,2) NOT NULL DEFAULT 1000,
    "fee_minibus" DECIMAL(10,2) NOT NULL DEFAULT 2000,
    "fee_bus" DECIMAL(10,2) NOT NULL DEFAULT 3000,
    "fee_truck" DECIMAL(10,2) NOT NULL DEFAULT 5000,
    "fee_government" DECIMAL(10,2) NOT NULL DEFAULT 0,
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "parking_locations_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "vehicles" (
    "id" SERIAL NOT NULL,
    "plate_number" TEXT NOT NULL,
    "owner_name" TEXT NOT NULL,
    "owner_phone" TEXT NOT NULL,
    "owner_email" TEXT NOT NULL DEFAULT '',
    "make" TEXT NOT NULL DEFAULT '',
    "model" TEXT NOT NULL DEFAULT '',
    "color" TEXT NOT NULL DEFAULT '',
    "year" INTEGER,
    "category" "VehicleCategory" NOT NULL DEFAULT 'PRIVATE_CAR',
    "registration_date" TIMESTAMP(3),
    "is_valid" BOOLEAN NOT NULL DEFAULT true,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "vehicles_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "control_numbers" (
    "id" SERIAL NOT NULL,
    "control_number" TEXT NOT NULL,
    "plate_number" TEXT NOT NULL,
    "vehicle_id" INTEGER,
    "officer_id" INTEGER,
    "location_id" INTEGER,
    "amount_due" DECIMAL(10,2) NOT NULL,
    "generated_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "expires_at" TIMESTAMP(3) NOT NULL,
    "status" "BillStatus" NOT NULL DEFAULT 'ACTIVE',
    "sms_sent" BOOLEAN NOT NULL DEFAULT false,
    "email_sent" BOOLEAN NOT NULL DEFAULT false,
    "sms_error" TEXT NOT NULL DEFAULT '',
    "notes" TEXT NOT NULL DEFAULT '',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "control_numbers_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "blacklisted_tokens" (
    "id" SERIAL NOT NULL,
    "jti" TEXT NOT NULL,
    "expires_at" TIMESTAMP(3) NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "blacklisted_tokens_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "officers_employee_id_key" ON "officers"("employee_id");

-- CreateIndex
CREATE INDEX "audit_logs_officer_id_timestamp_idx" ON "audit_logs"("officer_id", "timestamp");

-- CreateIndex
CREATE INDEX "audit_logs_action_timestamp_idx" ON "audit_logs"("action", "timestamp");

-- CreateIndex
CREATE UNIQUE INDEX "vehicles_plate_number_key" ON "vehicles"("plate_number");

-- CreateIndex
CREATE UNIQUE INDEX "control_numbers_control_number_key" ON "control_numbers"("control_number");

-- CreateIndex
CREATE INDEX "control_numbers_plate_number_status_expires_at_idx" ON "control_numbers"("plate_number", "status", "expires_at");

-- CreateIndex
CREATE INDEX "control_numbers_officer_id_generated_at_idx" ON "control_numbers"("officer_id", "generated_at");

-- CreateIndex
CREATE INDEX "control_numbers_status_expires_at_idx" ON "control_numbers"("status", "expires_at");

-- CreateIndex
CREATE UNIQUE INDEX "blacklisted_tokens_jti_key" ON "blacklisted_tokens"("jti");

-- AddForeignKey
ALTER TABLE "officers" ADD CONSTRAINT "officers_location_id_fkey" FOREIGN KEY ("location_id") REFERENCES "parking_locations"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "audit_logs" ADD CONSTRAINT "audit_logs_officer_id_fkey" FOREIGN KEY ("officer_id") REFERENCES "officers"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "control_numbers" ADD CONSTRAINT "control_numbers_vehicle_id_fkey" FOREIGN KEY ("vehicle_id") REFERENCES "vehicles"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "control_numbers" ADD CONSTRAINT "control_numbers_officer_id_fkey" FOREIGN KEY ("officer_id") REFERENCES "officers"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "control_numbers" ADD CONSTRAINT "control_numbers_location_id_fkey" FOREIGN KEY ("location_id") REFERENCES "parking_locations"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- ParkiPay v2 — Add supervisor officer for admin screen access
-- Run in Supabase SQL Editor

-- Add a supervisor (can access admin panel)
INSERT INTO officers (employee_id, full_name, phone, email, role, password_hash, location_id, is_active, updated_at)
VALUES (
  'SUP-001', 'Supervisor Admin', '+255700000099', 'supervisor@parkipay.go.tz',
  'SUPERVISOR', '', 1, TRUE, NOW()
)
ON CONFLICT (employee_id) DO NOTHING;

-- Make existing officers have empty password_hash (ID-only auth)
UPDATE officers SET password_hash = '', updated_at = NOW()
WHERE password_hash != '' AND role != 'ADMIN';

-- Verify
SELECT employee_id, full_name, role, is_active FROM officers ORDER BY id;

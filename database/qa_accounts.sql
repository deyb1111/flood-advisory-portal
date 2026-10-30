-- Bantay Daan Pasig: create/update the nine reserved QA accounts.
-- SAFE SCOPE: no DROP/DELETE/TRUNCATE/ALTER statements are used.
-- Run only against your development/QA database. Back up first if possible.
-- Passwords are stored as Werkzeug-compatible PBKDF2 hashes, not plaintext.
USE bantay_daan_pasig;

START TRANSACTION;

-- Ensure the three required barangay records exist without replacing existing IDs.
INSERT INTO barangays (name) VALUES
  ('Kalawaan'), ('San Joaquin'), ('Bambang')
ON DUPLICATE KEY UPDATE name = VALUES(name);

-- Each INSERT selects its barangay_id by name; no fixed IDs are assumed.
INSERT INTO users (full_name, email, password_hash, role, barangay_id, is_active)
SELECT 'QA Resident - Kalawaan', 'qa.resident.kalawaan@example.test', 'pbkdf2:sha256:600000$wrQpGmIUxoEMpdQB-l75pQ$59da2513e1e2eb874e17a96d79cb5699c87708c203e290d566e818ee78bf63e8', 'resident', barangay_id, 1
FROM barangays WHERE name = 'Kalawaan'
ON DUPLICATE KEY UPDATE
  full_name = VALUES(full_name),
  password_hash = VALUES(password_hash),
  role = VALUES(role),
  barangay_id = VALUES(barangay_id),
  is_active = VALUES(is_active);

INSERT INTO users (full_name, email, password_hash, role, barangay_id, is_active)
SELECT 'QA Staff - Kalawaan', 'qa.staff.kalawaan@example.test', 'pbkdf2:sha256:600000$vRuzVJ69nUnTCI_zGn1CLg$3047aca4ef36815697041caf08724fb173f76c024088fb0959a03d003bef2500', 'staff', barangay_id, 1
FROM barangays WHERE name = 'Kalawaan'
ON DUPLICATE KEY UPDATE
  full_name = VALUES(full_name),
  password_hash = VALUES(password_hash),
  role = VALUES(role),
  barangay_id = VALUES(barangay_id),
  is_active = VALUES(is_active);

INSERT INTO users (full_name, email, password_hash, role, barangay_id, is_active)
SELECT 'QA Admin - Kalawaan', 'qa.admin.kalawaan@example.test', 'pbkdf2:sha256:600000$58F8JnGw89T55V8xRy-0uw$c2de8604965f1d7e7bfcde78283b2c776df8aa70279f081163c1ba3fa7cafa23', 'admin', barangay_id, 1
FROM barangays WHERE name = 'Kalawaan'
ON DUPLICATE KEY UPDATE
  full_name = VALUES(full_name),
  password_hash = VALUES(password_hash),
  role = VALUES(role),
  barangay_id = VALUES(barangay_id),
  is_active = VALUES(is_active);

INSERT INTO users (full_name, email, password_hash, role, barangay_id, is_active)
SELECT 'QA Resident - San Joaquin', 'qa.resident.sanjoaquin@example.test', 'pbkdf2:sha256:600000$WQKF_BUeoIQcr7NvW-u16w$e4c0e229377fa33f6b1fad1cae16a41bd75e72b034adf6fe96c311a58c153ea7', 'resident', barangay_id, 1
FROM barangays WHERE name = 'San Joaquin'
ON DUPLICATE KEY UPDATE
  full_name = VALUES(full_name),
  password_hash = VALUES(password_hash),
  role = VALUES(role),
  barangay_id = VALUES(barangay_id),
  is_active = VALUES(is_active);

INSERT INTO users (full_name, email, password_hash, role, barangay_id, is_active)
SELECT 'QA Staff - San Joaquin', 'qa.staff.sanjoaquin@example.test', 'pbkdf2:sha256:600000$7tavvZ44incbFk9mPfc64Q$432d1ae729a3dd273e85219b07d960f561a8ca8a0555c3420e473bbf4ecb3ae6', 'staff', barangay_id, 1
FROM barangays WHERE name = 'San Joaquin'
ON DUPLICATE KEY UPDATE
  full_name = VALUES(full_name),
  password_hash = VALUES(password_hash),
  role = VALUES(role),
  barangay_id = VALUES(barangay_id),
  is_active = VALUES(is_active);

INSERT INTO users (full_name, email, password_hash, role, barangay_id, is_active)
SELECT 'QA Admin - San Joaquin', 'qa.admin.sanjoaquin@example.test', 'pbkdf2:sha256:600000$3k5QCFqoay2kl6pbGOQbVA$d4c9ea872ec287b0fcdfbafd8aac54cad5a8ecf13c26866a0585e755d59fab97', 'admin', barangay_id, 1
FROM barangays WHERE name = 'San Joaquin'
ON DUPLICATE KEY UPDATE
  full_name = VALUES(full_name),
  password_hash = VALUES(password_hash),
  role = VALUES(role),
  barangay_id = VALUES(barangay_id),
  is_active = VALUES(is_active);

INSERT INTO users (full_name, email, password_hash, role, barangay_id, is_active)
SELECT 'QA Resident - Bambang', 'qa.resident.bambang@example.test', 'pbkdf2:sha256:600000$rfSx5Kf404MOdOAbfYbP2g$a685ff9d649d64f73d0433afffdc5510f55a0e3152099d8f032a23d8a4ebbeb0', 'resident', barangay_id, 1
FROM barangays WHERE name = 'Bambang'
ON DUPLICATE KEY UPDATE
  full_name = VALUES(full_name),
  password_hash = VALUES(password_hash),
  role = VALUES(role),
  barangay_id = VALUES(barangay_id),
  is_active = VALUES(is_active);

INSERT INTO users (full_name, email, password_hash, role, barangay_id, is_active)
SELECT 'QA Staff - Bambang', 'qa.staff.bambang@example.test', 'pbkdf2:sha256:600000$Ec-SCbjBn_bzbsJeNP38bg$63ce81017caad2372f7fca9fdcb1d1d6fb02825d37e9ef6f89c2b4bf97065cec', 'staff', barangay_id, 1
FROM barangays WHERE name = 'Bambang'
ON DUPLICATE KEY UPDATE
  full_name = VALUES(full_name),
  password_hash = VALUES(password_hash),
  role = VALUES(role),
  barangay_id = VALUES(barangay_id),
  is_active = VALUES(is_active);

INSERT INTO users (full_name, email, password_hash, role, barangay_id, is_active)
SELECT 'QA Admin - Bambang', 'qa.admin.bambang@example.test', 'pbkdf2:sha256:600000$M0Kj5t8nUXM_mKe33KfWEQ$def712212506ac31531597b1081f42d69d535f997ce0d5fa71141f85fa73ea99', 'admin', barangay_id, 1
FROM barangays WHERE name = 'Bambang'
ON DUPLICATE KEY UPDATE
  full_name = VALUES(full_name),
  password_hash = VALUES(password_hash),
  role = VALUES(role),
  barangay_id = VALUES(barangay_id),
  is_active = VALUES(is_active);

COMMIT;

-- Verify account rows:
SELECT full_name, email, role, b.name AS barangay, is_active
FROM users u JOIN barangays b ON b.barangay_id = u.barangay_id
WHERE email LIKE 'qa.%@example.test'
ORDER BY b.name, FIELD(role, 'resident', 'staff', 'admin');

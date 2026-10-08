-- 1. Insert Barangays
INSERT INTO barangays (name) VALUES 
('Kalawaan'), 
('San Joaquin'), 
('Bambang');

-- 2. Insert Roads (assuming barangay IDs are 1, 2, 3 based on insertion order)
INSERT INTO roads (barangay_id, name) VALUES 
(1, 'Kalawaan Main Road'), 
(1, 'P. Cruz Street'),
(2, 'San Joaquin Road'), 
(2, 'Alley 1'),
(3, 'Bambang Street'), 
(3, 'H. Bautista Street');

-- 3. Insert Users 
-- NOTE: Replace 'YOUR_HASH_HERE' with a real hash (see Step 2 below)
INSERT INTO users (barangay_id, full_name, email, password_hash, role, is_active) VALUES 
(1, 'Test Resident', 'resident@example.com', 'scrypt:32768:8:1$GRdL1k4RKHVYMxA7$b0e7fedbd6dab66e94e0625b252244430cba7343b3776a0aa4dae110ada7bc8bfa943f92d71c1b2c23fb7b1996be08f61649bae3b64452b3df979f9458c60d77', 'resident', 1),
(1, 'Test Staff', 'staff@example.com', 'scrypt:32768:8:1$GRdL1k4RKHVYMxA7$b0e7fedbd6dab66e94e0625b252244430cba7343b3776a0aa4dae110ada7bc8bfa943f92d71c1b2c23fb7b1996be08f61649bae3b64452b3df979f9458c60d77', 'staff', 1),
(1, 'Test Admin', 'admin@example.com', 'scrypt:32768:8:1$GRdL1k4RKHVYMxA7$b0e7fedbd6dab66e94e0625b252244430cba7343b3776a0aa4dae110ada7bc8bfa943f92d71c1b2c23fb7b1996be08f61649bae3b64452b3df979f9458c60d77', 'admin', 1);
-- Additive migration for the administrator UI. Existing records are preserved.
USE bantay_daan_pasig;

CREATE TABLE IF NOT EXISTS system_settings (
  `key` VARCHAR(100) NOT NULL,
  `value` VARCHAR(255) NOT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS data_disposal_requests (
  request_id INT NOT NULL AUTO_INCREMENT,
  email VARCHAR(190) NOT NULL,
  details TEXT NULL,
  status ENUM('pending','approved','rejected','completed') NOT NULL DEFAULT 'pending',
  reviewed_by INT NULL,
  reviewed_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (request_id),
  KEY idx_disposal_status_created (status, created_at),
  CONSTRAINT fk_disposal_reviewed_by FOREIGN KEY (reviewed_by)
    REFERENCES users(user_id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO system_settings (`key`, `value`)
VALUES ('flood_threshold_cm', '30')
ON DUPLICATE KEY UPDATE `key` = VALUES(`key`);

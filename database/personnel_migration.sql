-- sql/personnel_migration.sql
USE bantay_daan_pasig;

ALTER TABLE advisories
  ADD COLUMN title  VARCHAR(200) NOT NULL DEFAULT '' AFTER is_resolved,
  ADD COLUMN status ENUM('draft','published','archived') NOT NULL DEFAULT 'published' AFTER title;

ALTER TABLE advisories
  ADD KEY idx_advisories_status (status);

CREATE TABLE activity_logs (
  log_id      INT           NOT NULL AUTO_INCREMENT,
  user_id     INT           NOT NULL,
  barangay_id INT           NOT NULL,
  action      VARCHAR(64)   NOT NULL,
  record_type VARCHAR(32)   NULL,
  record_id   INT           NULL,
  details     TEXT          NULL,
  created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (log_id),
  KEY idx_activity_logs_barangay_created (barangay_id, created_at),
  KEY idx_activity_logs_user (user_id),
  CONSTRAINT fk_activity_logs_user
    FOREIGN KEY (user_id) REFERENCES users (user_id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_activity_logs_barangay
    FOREIGN KEY (barangay_id) REFERENCES barangays (barangay_id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
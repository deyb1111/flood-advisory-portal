-- database/upvote_migration.sql
-- Community upvotes: nearby residents confirm a pending report.
-- Count is derived (COUNT(*)), so no denormalized column is added to `reports`.
USE bantay_daan_pasig;

CREATE TABLE report_upvotes (
  upvote_id  INT      NOT NULL AUTO_INCREMENT,
  report_id  INT      NOT NULL,
  user_id    INT      NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (upvote_id),
  UNIQUE KEY uq_report_upvotes_report_user (report_id, user_id),  -- one upvote per user
  KEY idx_report_upvotes_user (user_id),
  CONSTRAINT fk_report_upvotes_report
    FOREIGN KEY (report_id) REFERENCES reports (report_id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_report_upvotes_user
    FOREIGN KEY (user_id) REFERENCES users (user_id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- sql/notification_migration.sql
USE bantay_daan_pasig;

CREATE TABLE notifications (
  notification_id INT          NOT NULL AUTO_INCREMENT,
  user_id         INT          NOT NULL,
  report_id       INT          NULL,
  message         VARCHAR(255) NOT NULL,
  is_read         TINYINT(1)   NOT NULL DEFAULT 0,
  created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (notification_id),
  KEY idx_notifications_user_read (user_id, is_read, notification_id),
  KEY idx_notifications_report (report_id),
  CONSTRAINT fk_notifications_user
    FOREIGN KEY (user_id) REFERENCES users (user_id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_notifications_report
    FOREIGN KEY (report_id) REFERENCES reports (report_id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

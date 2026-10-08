-- =====================================================================
-- Bantay Daan Pasig — database schema
-- MySQL 8.0+ / InnoDB / utf8mb4
-- Mirrors §12 of the project handoff. Keep in sync with app/models.py.
--
-- ⚠ DEVELOPMENT RESET: this script DROPs the six tables before recreating
--   them. Comment out the DROP block once you have data you care about.
-- =====================================================================

SET NAMES utf8mb4;

CREATE DATABASE IF NOT EXISTS bantay_daan_pasig
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE bantay_daan_pasig;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS advisories;
DROP TABLE IF EXISTS verifications;
DROP TABLE IF EXISTS reports;
DROP TABLE IF EXISTS roads;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS barangays;
SET FOREIGN_KEY_CHECKS = 1;


-- ---------------------------------------------------------------------
-- 1. BARANGAYS
-- ---------------------------------------------------------------------
CREATE TABLE barangays (
  barangay_id INT          NOT NULL AUTO_INCREMENT,
  name        VARCHAR(64)  NOT NULL,
  PRIMARY KEY (barangay_id),
  UNIQUE KEY uq_barangays_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ---------------------------------------------------------------------
-- 2. USERS
--    role drives access: resident = own reports, staff = own barangay
--    queue, admin = everything.
-- ---------------------------------------------------------------------
CREATE TABLE users (
  user_id       INT           NOT NULL AUTO_INCREMENT,
  barangay_id   INT           NOT NULL,
  full_name     VARCHAR(120)  NOT NULL,
  email         VARCHAR(190)  NOT NULL,
  password_hash VARCHAR(255)  NOT NULL,
  role          ENUM('resident','staff','admin') NOT NULL DEFAULT 'resident',
  is_active     TINYINT(1)    NOT NULL DEFAULT 1,
  created_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id),
  UNIQUE KEY uq_users_email (email),
  KEY idx_users_barangay_role (barangay_id, role),
  CONSTRAINT fk_users_barangay
    FOREIGN KEY (barangay_id) REFERENCES barangays (barangay_id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ---------------------------------------------------------------------
-- 3. ROADS
-- ---------------------------------------------------------------------
CREATE TABLE roads (
  road_id     INT          NOT NULL AUTO_INCREMENT,
  barangay_id INT          NOT NULL,
  name        VARCHAR(150) NOT NULL,
  PRIMARY KEY (road_id),
  UNIQUE KEY uq_roads_barangay_name (barangay_id, name),
  CONSTRAINT fk_roads_barangay
    FOREIGN KEY (barangay_id) REFERENCES barangays (barangay_id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ---------------------------------------------------------------------
-- 4. REPORTS
--    status: pending | verified | unverified | rejected
--    duplicate_of: points at the earlier report this one was grouped under.
-- ---------------------------------------------------------------------
CREATE TABLE reports (
  report_id     INT            NOT NULL AUTO_INCREMENT,
  user_id       INT            NOT NULL,
  barangay_id   INT            NOT NULL,
  road_id       INT            NULL,
  report_type   ENUM('flood','traffic') NOT NULL,
  water_level   ENUM('none','gutter','ankle','knee','waist_or_higher') NULL,
  traffic_level ENUM('light','heavy','standstill') NULL,
  description   TEXT           NULL,
  latitude      DECIMAL(9,6)   NOT NULL,
  longitude     DECIMAL(9,6)   NOT NULL,
  photo_path    VARCHAR(255)   NULL,
  status        ENUM('pending','verified','unverified','rejected')
                               NOT NULL DEFAULT 'pending',
  duplicate_of  INT            NULL,
  created_at    DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (report_id),
  KEY idx_reports_status_created (status, created_at),
  KEY idx_reports_barangay_status (barangay_id, status),
  KEY idx_reports_user_created (user_id, created_at),
  KEY idx_reports_road (road_id),
  KEY idx_reports_duplicate_of (duplicate_of),
  CONSTRAINT fk_reports_user
    FOREIGN KEY (user_id) REFERENCES users (user_id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_reports_barangay
    FOREIGN KEY (barangay_id) REFERENCES barangays (barangay_id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_reports_road
    FOREIGN KEY (road_id) REFERENCES roads (road_id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_reports_duplicate_of
    FOREIGN KEY (duplicate_of) REFERENCES reports (report_id)
    ON DELETE RESTRICT ON UPDATE CASCADE,

  -- Rough bounding box for Pasig City. Stops stray pins from a bad GPS
  -- reading or a tampered POST body. The tight geofence (Kalawaan /
  -- San Joaquin / Bambang) lives in app/services/rules.py.
  CONSTRAINT chk_reports_coords CHECK (
    latitude  BETWEEN 14.500000 AND 14.700000 AND
    longitude BETWEEN 121.000000 AND 121.150000
  ),

  -- A flood report must carry a water level; a traffic report must carry
  -- a traffic level. The other column may still be filled in as extra
  -- context (e.g. a flood report that also notes standstill traffic).
  CONSTRAINT chk_reports_condition CHECK (
    (report_type = 'flood'   AND water_level   IS NOT NULL) OR
    (report_type = 'traffic' AND traffic_level IS NOT NULL)
  )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DELIMITER $$

CREATE TRIGGER trg_reports_prevent_self_duplicate
BEFORE INSERT ON reports
FOR EACH ROW
BEGIN
    IF NEW.duplicate_of IS NOT NULL AND NEW.duplicate_of = NEW.report_id THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'A report cannot be marked as a duplicate of itself.';
    END IF;
END$$

-- You should also add a similar trigger for UPDATE operations
CREATE TRIGGER trg_reports_prevent_self_duplicate_update
BEFORE UPDATE ON reports
FOR EACH ROW
BEGIN
    IF NEW.duplicate_of IS NOT NULL AND NEW.duplicate_of = NEW.report_id THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'A report cannot be marked as a duplicate of itself.';
    END IF;
END$$

DELIMITER ;


-- ---------------------------------------------------------------------
-- 5. VERIFICATIONS
--    Audit trail of staff decisions. A report may collect several rows
--    (re-checks); the current decision is the latest by decided_at.
-- ---------------------------------------------------------------------
CREATE TABLE verifications (
  verification_id INT          NOT NULL AUTO_INCREMENT,
  report_id       INT          NOT NULL,
  staff_id        INT          NOT NULL,
  decision        ENUM('verified','unverified','rejected') NOT NULL,
  remarks         TEXT         NULL,
  decided_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (verification_id),
  KEY idx_verifications_report_decided (report_id, decided_at),
  KEY idx_verifications_staff (staff_id),
  CONSTRAINT fk_verifications_report
    FOREIGN KEY (report_id) REFERENCES reports (report_id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_verifications_staff
    FOREIGN KEY (staff_id) REFERENCES users (user_id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ---------------------------------------------------------------------
-- 6. ADVISORIES
--    report_id is nullable: staff may publish a road-status advisory
--    without a single originating report.
-- ---------------------------------------------------------------------
CREATE TABLE advisories (
  advisory_id  INT          NOT NULL AUTO_INCREMENT,
  report_id    INT          NULL,
  barangay_id  INT          NOT NULL,
  road_id      INT          NOT NULL,
  published_by INT          NOT NULL,
  road_status  ENUM('passable','caution','not_passable') NOT NULL,
  message      TEXT         NOT NULL,
  published_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at   DATETIME     NULL,
  is_resolved  TINYINT(1)   NOT NULL DEFAULT 0,
  PRIMARY KEY (advisory_id),
  KEY idx_advisories_resolved_expires (is_resolved, expires_at),
  KEY idx_advisories_barangay (barangay_id),
  KEY idx_advisories_road (road_id),
  KEY idx_advisories_report (report_id),
  CONSTRAINT fk_advisories_report
    FOREIGN KEY (report_id) REFERENCES reports (report_id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_advisories_barangay
    FOREIGN KEY (barangay_id) REFERENCES barangays (barangay_id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_advisories_road
    FOREIGN KEY (road_id) REFERENCES roads (road_id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_advisories_publisher
    FOREIGN KEY (published_by) REFERENCES users (user_id)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT chk_advisories_expiry CHECK (
    expires_at IS NULL OR expires_at > published_at
  )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
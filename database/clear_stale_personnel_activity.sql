-- Clear stale personnel activity history left behind by the previous database reset.
-- This affects ONLY activity_logs. It does not drop tables or modify users,
-- barangays, reports, roads, advisories, or other application data.
-- Review the selected database before executing.

USE bantay_daan_pasig;

START TRANSACTION;
DELETE FROM activity_logs;
COMMIT;

-- Verify the stale activity history is cleared (expected result: 0).
SELECT COUNT(*) AS remaining_activity_logs FROM activity_logs;

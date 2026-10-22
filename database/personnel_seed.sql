-- sql/personnel_seed.sql
USE bantay_daan_pasig;

INSERT INTO reports
  (user_id, barangay_id, road_id, report_type, water_level, traffic_level,
   description, latitude, longitude, status, created_at) VALUES
  (1, 1, 1, 'flood',   'knee',   NULL,      'Floodwater covers both lanes near the intersection.',         14.576400, 121.085100, 'verified', NOW() - INTERVAL 1 HOUR),
  (1, 1, 2, 'traffic', NULL,     'heavy',   'Slow-moving vehicles near the flooded curb.',                 14.577400, 121.084800, 'pending',  NOW() - INTERVAL 45 MINUTE),
  (1, 1, 1, 'flood',   'gutter', NULL,      'Gutter-deep water. Motorcycles passing with difficulty.',     14.576800, 121.085600, 'verified', NOW() - INTERVAL 30 MINUTE),
  (1, 1, 2, 'flood',   'ankle',  NULL,      'Water has gathered near the corner after the rain.',          14.577800, 121.084200, 'rejected', NOW() - INTERVAL 20 MINUTE);

INSERT INTO verifications (report_id, staff_id, decision, remarks, decided_at) VALUES
  (1, 2, 'verified', 'Photo and location checked; condition corroborated.', NOW() - INTERVAL 50 MINUTE),
  (3, 2, 'verified', 'Gutter-deep confirmed.',                            NOW() - INTERVAL 25 MINUTE);

INSERT INTO advisories
  (report_id, barangay_id, road_id, published_by, road_status,
   message, published_at, status, title) VALUES
  (1, 1, 1, 2, 'not_passable',
   'Floodwater covers both lanes. Avoid this segment if possible; small vehicles should not attempt to pass.',
   NOW() - INTERVAL 40 MINUTE, 'published',
   'Flooding near Kalawaan Main Road intersection');

INSERT INTO activity_logs (user_id, barangay_id, action, record_type, record_id, details, created_at) VALUES
  (2, 1, 'Report verified',   'report',   1, 'Photo and location checked.',                       NOW() - INTERVAL 50 MINUTE),
  (2, 1, 'Advisory published','advisory', 1, 'Published advisory.',                              NOW() - INTERVAL 40 MINUTE),
  (2, 1, 'Report rejected',   'report',   4, 'Reason: Duplicate image; location not confirmed.', NOW() - INTERVAL 20 MINUTE);
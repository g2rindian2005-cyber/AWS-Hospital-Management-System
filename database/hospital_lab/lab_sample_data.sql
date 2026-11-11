-- ============================================================
-- SAMPLE LAB ORDERS for hospital_lab
-- Run AFTER laboratory.sql AND the main sample_data.sql
-- (patients 1-5 and doctors 1-5 must already exist).
-- Test IDs refer to the catalog seeded by laboratory.sql.
-- ============================================================

USE hospital_lab;

INSERT INTO lab_orders (patient_id, test_id, ordered_by, order_date, priority, status, result_value, remarks, report_date) VALUES
(1, 4,  1, '2026-10-01 11:00:00', 'Routine', 'Completed',       '182',      'Total cholesterol mildly raised; diet advice given.', '2026-10-02 09:15:00'),
(2, 11, 2, '2026-09-20 15:00:00', 'Urgent',  'Completed',       '14',       'CRP raised — consistent with migraine inflammation workup.', '2026-09-21 10:00:00'),
(3, 1,  3, '2026-10-15 10:00:00', 'Routine', 'Completed',       '13.2',     'Haemoglobin normal before fracture management.', '2026-10-15 16:30:00'),
(4, 10, 4, '2026-08-05 12:00:00', 'Urgent',  'Sample Collected', NULL,      'Dengue screen ordered with asthma review.', NULL),
(5, 3,  1, '2026-07-10 17:15:00', 'Routine', 'Processing',       NULL,      'Quarterly diabetes monitoring panel.', NULL),
(1, 5,  1, '2026-11-08 09:30:00', 'Routine', 'Ordered',          NULL,      'Annual liver profile with hypertension review.', NULL);

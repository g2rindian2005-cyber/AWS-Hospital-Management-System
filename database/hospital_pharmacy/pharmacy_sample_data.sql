-- ============================================================
-- SAMPLE PRESCRIPTIONS for hospital_pharmacy
-- Run AFTER pharmacy.sql AND the main sample_data.sql
-- (patients 1-5 and doctors 1-5 must already exist).
-- Medicine IDs refer to the catalog seeded by pharmacy.sql.
-- ============================================================

USE hospital_pharmacy;

INSERT INTO prescriptions (patient_id, doctor_id, medicine_id, quantity, dosage, frequency, duration_days, prescribed_date, status, dispensed_date, remarks) VALUES
(1, 1, 3,  30, '5mg',   'Once a day',   30, '2026-10-01 11:30:00', 'Dispensed', '2026-10-01 12:00:00', 'For hypertension — monthly refill.'),
(2, 2, 1,  10, '500mg', 'Thrice a day', 3,  '2026-09-20 15:30:00', 'Dispensed', '2026-09-20 16:05:00', 'For migraine pain relief.'),
(3, 3, 7,  20, '400mg', 'Twice a day',  10, '2026-10-15 10:30:00', 'Dispensed', '2026-10-15 11:00:00', 'Post-fracture pain management.'),
(4, 4, 10, 1,  '2 puffs','As needed',   30, '2026-08-05 12:30:00', 'Pending',   NULL,                  'Asthma reliever inhaler.'),
(5, 1, 4,  60, '500mg', 'Twice a day',  30, '2026-07-10 17:45:00', 'Dispensed', '2026-07-10 18:10:00', 'Diabetes — morning and evening after food.'),
(5, 1, 11, 1,  '100 units/ml', 'Once at night', 30, '2026-11-05 10:00:00', 'Pending', NULL,            'Basal insulin — keep refrigerated.');

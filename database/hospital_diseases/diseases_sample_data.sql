-- Sample data for hospital_diseases ONLY — split from database/sample_data.sql
-- for the 6-RDS topology (run against the hospital_diseases instance's endpoint).
-- The combined database/sample_data.sql remains the source for
-- single-instance/local setups; keep the two in sync.

USE hospital_diseases;
INSERT INTO diseases (patient_id, disease_name, diagnosis_date, severity, symptoms, description, treatment, prescribed_meds, status, diagnosed_by, follow_up_date) VALUES
(1, 'Hypertension',         '2026-10-01', 'Moderate', 'High BP, headaches',         'Stage 1 hypertension',       'Lifestyle changes + medication', 'Amlodipine 5mg',  'Under Treatment', 2, '2026-11-15'),
(2, 'Migraine',              '2026-09-20', 'Mild',     'Recurrent headaches',       'Chronic migraine',           'Pain management',              'Sumatriptan',     'Active',          2, '2026-11-10'),
(3, 'Fracture - Tibia',      '2026-10-15', 'Severe',  'Leg pain, swelling',        'Tibial shaft fracture',      'Plaster + physiotherapy',       'Calcium + D3',    'Under Treatment', 3, '2026-12-01'),
(4, 'Asthma',                '2026-08-05', 'Moderate', 'Wheezing, shortness of breath','Persistent asthma',       'Inhaler + avoid triggers',     'Salbutamol inhaler','Active',         4, '2026-11-20'),
(5, 'Type 2 Diabetes',       '2026-07-10', 'Moderate', 'Increased thirst, fatigue','Type 2 diabetes mellitus',   'Diet control + metformin',     'Metformin 500mg', 'Chronic',         1, '2026-11-30');

-- ---------- 4. Bills ----------

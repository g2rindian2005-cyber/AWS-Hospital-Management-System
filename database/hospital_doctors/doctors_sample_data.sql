-- Sample data for hospital_doctors ONLY — split from database/sample_data.sql
-- for the 6-RDS topology (run against the hospital_doctors instance's endpoint).
-- The combined database/sample_data.sql remains the source for
-- single-instance/local setups; keep the two in sync.

USE hospital_doctors;
INSERT INTO doctors (first_name, last_name, specialization, department, phone, email, license_number, availability, consultation_fee) VALUES
('Dr. Anil',  'Gupta',   'Cardiologist', 'Cardiology', '9000012345', 'anil.gupta@hospital.com', 'MED-101', 'Available', 800.00),
('Dr. Meera', 'Nair',    'Neurologist',  'Neurology',  '9000012346', 'meera.nair@hospital.com', 'MED-102', 'Available', 1000.00),
('Dr. Vivek', 'Joshi',   'Orthopedic',   'Orthopedics','9000012347', 'vivek.joshi@hospital.com','MED-103', 'Busy',      600.00),
('Dr. Sunita','Kapoor',  'Pediatrician', 'Pediatrics', '9000012348', 'sunita.kapoor@hospital.com','MED-104','Available', 500.00),
('Dr. Rajesh','Mehta',   'General Physician','General', '9000012349','rajesh.mehta@hospital.com','MED-105','On Leave', 400.00);

-- ---------- 3. Diseases ----------
USE hospital_doctors;
INSERT INTO doctor_assignments (patient_id, doctor_id, disease_id, assignment_date, appointment_date, status, room_number, notes) VALUES
(1, 1, 1, '2026-10-01 10:00:00', '2026-11-15 10:00:00', 'Active',    'C-101', 'Regular BP monitoring'),
(2, 2, 2, '2026-09-20 13:30:00', '2026-11-10 11:00:00', 'Scheduled','N-203', 'Migraine management'),
(3, 3, 3, '2026-10-15 08:30:00', '2026-12-01 09:00:00', 'Active',    'O-305', 'Post fracture review'),
(4, 4, 4, '2026-08-05 11:00:00', '2026-11-20 14:00:00', 'Scheduled', 'P-102', 'Asthma action plan'),
(5, 1, 5, '2026-07-10 16:30:00', '2026-11-30 15:00:00', 'Active',    'G-201', 'Diabetes management');

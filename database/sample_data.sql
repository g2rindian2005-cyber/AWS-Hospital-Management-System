-- ============================================================
-- SAMPLE DATA for all 4 databases
-- Run AFTER the schema files (patients.sql, bills.sql,
-- payments.sql, diseases.sql, doctors.sql, doctor_assignments.sql)
-- ============================================================

-- ---------- 1. Patients ----------
USE hospital_patients;
INSERT INTO patients (first_name, last_name, date_of_birth, gender, phone, email, address, blood_group, emergency_contact, insurance_number) VALUES
('Rahul',  'Sharma',  '1990-05-14', 'Male',   '9876543210', 'rahul.sharma@email.com',  '12 MG Road, Bangalore', 'O+',  '9123456780', 'INS-001'),
('Priya',  'Patel',   '1988-09-22', 'Female', '9876543211', 'priya.patel@email.com',   '45 Park Street, Mumbai', 'A+',  '9123456781', 'INS-002'),
('Amit',   'Verma',   '1995-01-30', 'Male',   '9876543212', 'amit.verma@email.com',    '78 Lake View, Delhi',    'B+',  '9123456782', 'INS-003'),
('Sneha',  'Reddy',   '2000-07-08', 'Female', '9876543213', 'sneha.reddy@email.com',   '23 Brigade Rd, Hyderabad','AB+', '9123456783', 'INS-004'),
('Karan',  'Singh',   '1982-11-19', 'Male',   '9876543214', 'karan.singh@email.com',   '56 Civil Lines, Jaipur',  'O-',  '9123456784', 'INS-005');

-- ---------- 2. Doctors ----------
USE hospital_doctors;
INSERT INTO doctors (first_name, last_name, specialization, department, phone, email, license_number, availability, consultation_fee) VALUES
('Dr. Anil',  'Gupta',   'Cardiologist', 'Cardiology', '9000012345', 'anil.gupta@hospital.com', 'MED-101', 'Available', 800.00),
('Dr. Meera', 'Nair',    'Neurologist',  'Neurology',  '9000012346', 'meera.nair@hospital.com', 'MED-102', 'Available', 1000.00),
('Dr. Vivek', 'Joshi',   'Orthopedic',   'Orthopedics','9000012347', 'vivek.joshi@hospital.com','MED-103', 'Busy',      600.00),
('Dr. Sunita','Kapoor',  'Pediatrician', 'Pediatrics', '9000012348', 'sunita.kapoor@hospital.com','MED-104','Available', 500.00),
('Dr. Rajesh','Mehta',   'General Physician','General', '9000012349','rajesh.mehta@hospital.com','MED-105','On Leave', 400.00);

-- ---------- 3. Diseases ----------
USE hospital_diseases;
INSERT INTO diseases (patient_id, disease_name, diagnosis_date, severity, symptoms, description, treatment, prescribed_meds, status, diagnosed_by, follow_up_date) VALUES
(1, 'Hypertension',         '2026-10-01', 'Moderate', 'High BP, headaches',         'Stage 1 hypertension',       'Lifestyle changes + medication', 'Amlodipine 5mg',  'Under Treatment', 2, '2026-11-15'),
(2, 'Migraine',              '2026-09-20', 'Mild',     'Recurrent headaches',       'Chronic migraine',           'Pain management',              'Sumatriptan',     'Active',          2, '2026-11-10'),
(3, 'Fracture - Tibia',      '2026-10-15', 'Severe',  'Leg pain, swelling',        'Tibial shaft fracture',      'Plaster + physiotherapy',       'Calcium + D3',    'Under Treatment', 3, '2026-12-01'),
(4, 'Asthma',                '2026-08-05', 'Moderate', 'Wheezing, shortness of breath','Persistent asthma',       'Inhaler + avoid triggers',     'Salbutamol inhaler','Active',         4, '2026-11-20'),
(5, 'Type 2 Diabetes',       '2026-07-10', 'Moderate', 'Increased thirst, fatigue','Type 2 diabetes mellitus',   'Diet control + metformin',     'Metformin 500mg', 'Chronic',         1, '2026-11-30');

-- ---------- 4. Bills ----------
USE hospital_billing;
INSERT INTO bills (patient_id, bill_date, description, category, amount, discount, status) VALUES
(1, '2026-10-01 10:30:00', 'Cardiology consultation + ECG',     'Consultation', 1500.00, 0.00,   'Partial'),
(2, '2026-09-20 14:00:00', 'Neurology consultation + MRI scan', 'Lab Test',    5000.00, 500.00, 'Pending'),
(3, '2026-10-15 09:00:00', 'Orthopedic consultation + X-Ray',   'Consultation', 2500.00, 0.00,   'Paid'),
(4, '2026-08-05 11:15:00', 'Pulmonology consultation + Spirometry','Consultation',1800.00, 0.00,'Pending'),
(5, '2026-07-10 16:45:00', 'General consult + Blood sugar panel','Lab Test',   1200.00, 100.00,'Partial');

-- ---------- 5. Payments ----------
INSERT INTO payments (bill_id, patient_id, amount_paid, payment_method, payment_date, transaction_id, remarks) VALUES
(1, 1, 1000.00, 'UPI',     '2026-10-01 10:45:00', 'TXN-1001', 'Partial payment'),
(3, 3, 2500.00, 'Card',    '2026-10-15 09:30:00', 'TXN-1002', 'Full payment'),
(5, 5, 500.00,  'Cash',    '2026-07-10 17:00:00', 'TXN-1003', 'Advance payment');

-- ---------- 6. Doctor Assignments ----------
USE hospital_doctors;
INSERT INTO doctor_assignments (patient_id, doctor_id, disease_id, assignment_date, appointment_date, status, room_number, notes) VALUES
(1, 1, 1, '2026-10-01 10:00:00', '2026-11-15 10:00:00', 'Active',    'C-101', 'Regular BP monitoring'),
(2, 2, 2, '2026-09-20 13:30:00', '2026-11-10 11:00:00', 'Scheduled','N-203', 'Migraine management'),
(3, 3, 3, '2026-10-15 08:30:00', '2026-12-01 09:00:00', 'Active',    'O-305', 'Post fracture review'),
(4, 4, 4, '2026-08-05 11:00:00', '2026-11-20 14:00:00', 'Scheduled', 'P-102', 'Asthma action plan'),
(5, 1, 5, '2026-07-10 16:30:00', '2026-11-30 15:00:00', 'Active',    'G-201', 'Diabetes management');

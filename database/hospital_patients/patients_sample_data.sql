-- Sample data for hospital_patients ONLY — split from database/sample_data.sql
-- for the 6-RDS topology (run against the hospital_patients instance's endpoint).
-- The combined database/sample_data.sql remains the source for
-- single-instance/local setups; keep the two in sync.

USE hospital_patients;
INSERT INTO patients (first_name, last_name, date_of_birth, gender, phone, email, address, blood_group, emergency_contact, insurance_number) VALUES
('Rahul',  'Sharma',  '1990-05-14', 'Male',   '9876543210', 'rahul.sharma@email.com',  '12 MG Road, Bangalore', 'O+',  '9123456780', 'INS-001'),
('Priya',  'Patel',   '1988-09-22', 'Female', '9876543211', 'priya.patel@email.com',   '45 Park Street, Mumbai', 'A+',  '9123456781', 'INS-002'),
('Amit',   'Verma',   '1995-01-30', 'Male',   '9876543212', 'amit.verma@email.com',    '78 Lake View, Delhi',    'B+',  '9123456782', 'INS-003'),
('Sneha',  'Reddy',   '2000-07-08', 'Female', '9876543213', 'sneha.reddy@email.com',   '23 Brigade Rd, Hyderabad','AB+', '9123456783', 'INS-004'),
('Karan',  'Singh',   '1982-11-19', 'Male',   '9876543214', 'karan.singh@email.com',   '56 Civil Lines, Jaipur',  'O-',  '9123456784', 'INS-005');

-- ---------- 2. Doctors ----------

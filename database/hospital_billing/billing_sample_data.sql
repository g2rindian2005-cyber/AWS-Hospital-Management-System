-- Sample data for hospital_billing ONLY — split from database/sample_data.sql
-- for the 6-RDS topology (run against the hospital_billing instance's endpoint).
-- The combined database/sample_data.sql remains the source for
-- single-instance/local setups; keep the two in sync.

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

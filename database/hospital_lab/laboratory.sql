-- ============================================================
-- DATABASE 5: hospital_lab
-- Laboratory module: test catalog + patient test orders/results
-- Synchronised with hospital_patients via patient_id
-- Synchronised with hospital_doctors via ordered_by (doctor_id)
-- ============================================================

CREATE DATABASE IF NOT EXISTS hospital_lab
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE hospital_lab;

-- ---------- Test catalog (the lab's price / reference list) ----------
CREATE TABLE IF NOT EXISTS lab_tests (
    test_id          INT AUTO_INCREMENT PRIMARY KEY,
    test_name        VARCHAR(200) NOT NULL,
    category         ENUM('Hematology','Biochemistry','Microbiology','Serology','Pathology','Radiology','Hormones') DEFAULT 'Biochemistry',
    sample_type      VARCHAR(100),               -- Blood, Urine, Sputum, ...
    unit             VARCHAR(50),                -- mg/dL, g/dL, IU/L, ...
    normal_range     VARCHAR(100),               -- e.g. '70 - 110'
    price            DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    turnaround_hours INT DEFAULT 24,
    is_active        TINYINT(1) DEFAULT 1,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_test_category (category),
    INDEX idx_test_name (test_name)
) ENGINE=InnoDB;

-- ---------- Patient lab orders + results ----------
CREATE TABLE IF NOT EXISTS lab_orders (
    order_id     INT AUTO_INCREMENT PRIMARY KEY,
    patient_id   INT NOT NULL,                   -- FK (logical) -> hospital_patients.patients.patient_id
    test_id      INT NOT NULL,                   -- FK (logical) -> lab_tests.test_id
    ordered_by   INT,                            -- FK (logical) -> hospital_doctors.doctors.doctor_id
    order_date   DATETIME DEFAULT CURRENT_TIMESTAMP,
    priority     ENUM('Routine','Urgent','STAT') DEFAULT 'Routine',
    status       ENUM('Ordered','Sample Collected','Processing','Completed','Cancelled') DEFAULT 'Ordered',
    result_value VARCHAR(200),                   -- filled when the report is ready
    remarks      TEXT,
    report_date  DATETIME,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_order_patient (patient_id),
    INDEX idx_order_test (test_id),
    INDEX idx_order_status (status)
) ENGINE=InnoDB;

-- View: orders still moving through the lab
CREATE OR REPLACE VIEW v_pending_lab_orders AS
SELECT
    order_id,
    patient_id,
    test_id,
    ordered_by,
    order_date,
    priority,
    status
FROM lab_orders
WHERE status IN ('Ordered','Sample Collected','Processing')
ORDER BY order_date ASC;

-- ---------- Test catalog seed (standard hospital price list) ----------
INSERT INTO lab_tests (test_name, category, sample_type, unit, normal_range, price, turnaround_hours) VALUES
('Complete Blood Count (CBC)', 'Hematology',   'Blood',  'g/dL',   'Hb 12.0 - 15.5',      300.00, 6),
('Fasting Blood Sugar',        'Biochemistry', 'Blood',  'mg/dL',  '70 - 110',            150.00, 4),
('HbA1c (Glycated Hb)',        'Biochemistry', 'Blood',  '%',      'Below 5.7',           450.00, 24),
('Lipid Profile',              'Biochemistry', 'Blood',  'mg/dL',  'Total Chol. below 200', 800.00, 24),
('Liver Function Test (LFT)',  'Biochemistry', 'Blood',  'IU/L',   'SGOT 5 - 40',         700.00, 24),
('Kidney Function Test (KFT)', 'Biochemistry', 'Blood',  'mg/dL',  'Creatinine 0.6 - 1.3', 750.00, 24),
('Thyroid Profile (T3 T4 TSH)','Hormones',     'Blood',  'mIU/L',  'TSH 0.4 - 4.2',       900.00, 48),
('Vitamin D Total',            'Biochemistry', 'Blood',  'ng/mL',  '30 - 100',           1600.00, 48),
('Urine Routine Examination',  'Pathology',    'Urine',  '',       'No abnormality',      250.00, 6),
('Dengue NS1 Antigen',         'Serology',     'Blood',  '',       'Negative',            600.00, 12),
('CRP (C-Reactive Protein)',   'Serology',     'Blood',  'mg/L',   'Below 6',             500.00, 12),
('Chest X-Ray (PA View)',      'Radiology',    'X-Ray',  '',       'Normal study',        550.00, 6)
ON DUPLICATE KEY UPDATE test_name = VALUES(test_name);

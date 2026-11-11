-- ============================================================
-- DATABASE 6: hospital_pharmacy
-- Pharmacy module: medicine catalog + patient prescriptions
-- Synchronised with hospital_patients via patient_id
-- Synchronised with hospital_doctors via doctor_id
-- ============================================================

CREATE DATABASE IF NOT EXISTS hospital_pharmacy
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE hospital_pharmacy;

-- ---------- Medicine catalog (with stock) ----------
CREATE TABLE IF NOT EXISTS medicines (
    medicine_id          INT AUTO_INCREMENT PRIMARY KEY,
    medicine_name        VARCHAR(200) NOT NULL,
    generic_name         VARCHAR(200),
    category             ENUM('Antibiotic','Analgesic','Antacid','Cardiac','Diabetic','Antihistamine','Vitamin','Steroid','First Aid','Other') DEFAULT 'Other',
    manufacturer         VARCHAR(150),
    unit                 VARCHAR(50) DEFAULT 'Tablet',   -- Tablet, Capsule, Syrup, Injection, Ointment
    unit_price           DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    stock_quantity       INT NOT NULL DEFAULT 0,
    reorder_level        INT NOT NULL DEFAULT 20,
    expiry_date          DATE,
    requires_prescription TINYINT(1) DEFAULT 1,
    created_at           DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at           DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_med_category (category),
    INDEX idx_med_name (medicine_name)
) ENGINE=InnoDB;

-- ---------- Patient prescriptions ----------
CREATE TABLE IF NOT EXISTS prescriptions (
    prescription_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id      INT NOT NULL,                   -- FK (logical) -> hospital_patients.patients.patient_id
    doctor_id       INT,                            -- FK (logical) -> hospital_doctors.doctors.doctor_id
    medicine_id     INT NOT NULL,                   -- FK (logical) -> medicines.medicine_id
    quantity        INT NOT NULL DEFAULT 1,
    dosage          VARCHAR(100),                   -- e.g. '500mg'
    frequency       VARCHAR(100),                   -- e.g. 'Twice a day'
    duration_days   INT,
    prescribed_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    status          ENUM('Pending','Dispensed','Cancelled') DEFAULT 'Pending',
    dispensed_date  DATETIME,
    remarks         TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_rx_patient (patient_id),
    INDEX idx_rx_medicine (medicine_id),
    INDEX idx_rx_status (status)
) ENGINE=InnoDB;

-- View: medicines running low on stock
CREATE OR REPLACE VIEW v_low_stock AS
SELECT
    medicine_id,
    medicine_name,
    category,
    unit,
    unit_price,
    stock_quantity,
    reorder_level,
    expiry_date
FROM medicines
WHERE stock_quantity <= reorder_level
ORDER BY stock_quantity ASC;

-- ---------- Medicine catalog seed (common hospital stock) ----------
INSERT INTO medicines (medicine_name, generic_name, category, manufacturer, unit, unit_price, stock_quantity, reorder_level, expiry_date, requires_prescription) VALUES
('Paracetamol 500mg',   'Paracetamol',       'Analgesic',     'Cipla',        'Tablet',    2.50,  1200, 200, '2027-06-30', 0),
('Amoxicillin 250mg',   'Amoxicillin',       'Antibiotic',    'Sun Pharma',   'Capsule',   8.00,  450,  100, '2026-12-31', 1),
('Amlodipine 5mg',      'Amlodipine',        'Cardiac',       'Dr Reddy''s',  'Tablet',    4.20,  600,  100, '2027-03-31', 1),
('Metformin 500mg',     'Metformin',         'Diabetic',      'USV',          'Tablet',    3.10,  800,  150, '2027-01-31', 1),
('Omeprazole 20mg',     'Omeprazole',        'Antacid',       'Zydus',        'Capsule',   5.50,  520,  100, '2026-11-30', 0),
('Cetirizine 10mg',     'Cetirizine',        'Antihistamine', 'GSK',          'Tablet',    3.00,  350,  80,  '2027-08-31', 0),
('Ibuprofen 400mg',     'Ibuprofen',         'Analgesic',     'Abbott',       'Tablet',    4.00,  275,  80,  '2026-10-31', 0),
('Azithromycin 500mg',  'Azithromycin',      'Antibiotic',    'Cipla',        'Tablet',    18.00, 180,  60,  '2026-09-30', 1),
('Vitamin D3 60K',      'Cholecalciferol',   'Vitamin',       'Mankind',      'Capsule',   28.00, 140,  40,  '2027-02-28', 0),
('Salbutamol Inhaler',  'Salbutamol',        'Other',         'Cipla',        'Inhaler',   165.00, 65,  25,  '2026-08-31', 1),
('Insulin Glargine',    'Insulin Glargine',  'Diabetic',      'Sanofi',       'Injection', 540.00, 42,  15,  '2026-07-31', 1),
('Betadine Ointment',   'Povidone Iodine',   'First Aid',     'Win-Medicare', 'Ointment',  65.00, 95,  30,  '2027-05-31', 0)
ON DUPLICATE KEY UPDATE medicine_name = VALUES(medicine_name);

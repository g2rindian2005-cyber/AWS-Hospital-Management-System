-- ============================================================
-- DATABASE 2: hospital_billing
-- Stores patient bills, payment history, and present dues
-- Synchronised with hospital_patients via patient_id
-- ============================================================

CREATE DATABASE IF NOT EXISTS hospital_billing
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE hospital_billing;

CREATE TABLE IF NOT EXISTS bills (
    bill_id     INT AUTO_INCREMENT PRIMARY KEY,
    patient_id  INT           NOT NULL,          -- FK (logical) -> hospital_patients.patients.patient_id
    bill_date   DATETIME      DEFAULT CURRENT_TIMESTAMP,
    description TEXT          NOT NULL,
    category    ENUM('Consultation','Lab Test','Surgery','Pharmacy','Room','Other') DEFAULT 'Consultation',
    amount      DECIMAL(10,2) NOT NULL,
    discount    DECIMAL(10,2) DEFAULT 0.00,
    net_amount  DECIMAL(10,2) GENERATED ALWAYS AS (amount - discount) STORED,
    status      ENUM('Pending','Partial','Paid','Cancelled') DEFAULT 'Pending',
    created_at  DATETIME      DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_bill_patient (patient_id),
    INDEX idx_bill_status (status),
    INDEX idx_bill_date (bill_date)
) ENGINE=InnoDB;

-- View showing present dues (bills not fully paid)
CREATE OR REPLACE VIEW v_pending_dues AS
SELECT
    b.bill_id,
    b.patient_id,
    b.description,
    b.net_amount,
    COALESCE((SELECT SUM(amount_paid) FROM payments p WHERE p.bill_id = b.bill_id), 0) AS amount_paid,
    b.net_amount - COALESCE((SELECT SUM(amount_paid) FROM payments p WHERE p.bill_id = b.bill_id), 0) AS due_amount,
    b.status,
    b.bill_date
FROM bills b
WHERE b.status IN ('Pending','Partial');

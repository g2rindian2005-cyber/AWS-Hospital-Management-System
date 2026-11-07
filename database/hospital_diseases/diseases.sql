-- ============================================================
-- DATABASE 3: hospital_diseases
-- Stores patient diseases / diagnosis records
-- Synchronised with hospital_patients via patient_id
-- Synchronised with hospital_doctors via diagnosed_by (doctor_id)
-- ============================================================

CREATE DATABASE IF NOT EXISTS hospital_diseases
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE hospital_diseases;

CREATE TABLE IF NOT EXISTS diseases (
    disease_id      INT AUTO_INCREMENT PRIMARY KEY,
    patient_id      INT           NOT NULL,      -- FK (logical) -> hospital_patients.patients.patient_id
    disease_name    VARCHAR(200)  NOT NULL,
    diagnosis_date  DATE          NOT NULL,
    severity        ENUM('Mild','Moderate','Severe','Critical') DEFAULT 'Mild',
    symptoms        TEXT,
    description     TEXT,
    treatment       TEXT,
    prescribed_meds TEXT,
    status          ENUM('Active','Under Treatment','Recovered','Chronic') DEFAULT 'Active',
    diagnosed_by    INT,                         -- FK (logical) -> hospital_doctors.doctors.doctor_id
    follow_up_date  DATE,
    created_at      DATETIME      DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_disease_patient (patient_id),
    INDEX idx_disease_status (status),
    INDEX idx_disease_name (disease_name)
) ENGINE=InnoDB;

-- View: active diseases that need attention
CREATE OR REPLACE VIEW v_active_diseases AS
SELECT
    disease_id,
    patient_id,
    disease_name,
    diagnosis_date,
    severity,
    status,
    diagnosed_by,
    follow_up_date
FROM diseases
WHERE status IN ('Active','Under Treatment')
ORDER BY follow_up_date ASC;

-- ============================================================
-- DATABASE 1: hospital_patients
-- Stores patient names and personal information
-- ============================================================

CREATE DATABASE IF NOT EXISTS hospital_patients
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE hospital_patients;

CREATE TABLE IF NOT EXISTS patients (
    patient_id        INT AUTO_INCREMENT PRIMARY KEY,
    first_name        VARCHAR(100)  NOT NULL,
    last_name         VARCHAR(100)  NOT NULL,
    date_of_birth     DATE          NOT NULL,
    gender            ENUM('Male','Female','Other') NOT NULL DEFAULT 'Male',
    phone             VARCHAR(20)   NOT NULL,
    email             VARCHAR(150),
    address           TEXT,
    blood_group       VARCHAR(5),
    emergency_contact VARCHAR(20),
    insurance_number  VARCHAR(50),
    registration_date DATETIME      DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_patient_name (last_name, first_name),
    INDEX idx_patient_phone (phone)
) ENGINE=InnoDB;

-- View that combines patient full name for easy joins
CREATE OR REPLACE VIEW v_patient_full AS
SELECT
    patient_id,
    CONCAT(first_name, ' ', last_name) AS full_name,
    first_name,
    last_name,
    date_of_birth,
    gender,
    phone,
    email,
    blood_group,
    registration_date
FROM patients;

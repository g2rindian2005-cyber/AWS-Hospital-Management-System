-- ============================================================
-- DATABASE 4: hospital_doctors
-- Stores doctors and doctor-patient assignments
-- Synchronised with hospital_patients via patient_id
-- Synchronised with hospital_diseases via disease_id
-- ============================================================

CREATE DATABASE IF NOT EXISTS hospital_doctors
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE hospital_doctors;

CREATE TABLE IF NOT EXISTS doctors (
    doctor_id       INT AUTO_INCREMENT PRIMARY KEY,
    first_name      VARCHAR(100)  NOT NULL,
    last_name       VARCHAR(100)  NOT NULL,
    specialization  VARCHAR(150)  NOT NULL,
    department      VARCHAR(100),
    phone           VARCHAR(20),
    email           VARCHAR(150),
    license_number  VARCHAR(50),
    availability    ENUM('Available','Busy','On Leave','Off Duty') DEFAULT 'Available',
    consultation_fee DECIMAL(10,2) DEFAULT 0.00,
    created_at      DATETIME      DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_doctor_name (last_name, first_name),
    INDEX idx_doctor_specialization (specialization),
    INDEX idx_doctor_availability (availability)
) ENGINE=InnoDB;

-- View: doctor full name
CREATE OR REPLACE VIEW v_doctor_full AS
SELECT
    doctor_id,
    CONCAT(first_name, ' ', last_name) AS full_name,
    first_name,
    last_name,
    specialization,
    department,
    phone,
    email,
    availability,
    consultation_fee
FROM doctors;

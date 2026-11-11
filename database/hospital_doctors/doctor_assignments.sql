-- ============================================================
-- DATABASE 4 (cont): hospital_doctors -> doctor_assignments
-- Links doctors to patients (and optionally a disease record)
-- This is the synchronisation hub between all 4 databases
-- ============================================================

USE hospital_doctors;

CREATE TABLE IF NOT EXISTS doctor_assignments (
    assignment_id    INT AUTO_INCREMENT PRIMARY KEY,
    patient_id       INT           NOT NULL,    -- FK (logical) -> hospital_patients.patients.patient_id
    doctor_id        INT           NOT NULL,    -- FK (logical) -> hospital_doctors.doctors.doctor_id
    disease_id       INT,                        -- FK (logical) -> hospital_diseases.diseases.disease_id
    assignment_date  DATETIME      DEFAULT CURRENT_TIMESTAMP,
    appointment_date DATETIME,
    status           ENUM('Assigned','Scheduled','Active','Completed','Cancelled') DEFAULT 'Assigned',
    room_number      VARCHAR(20),
    notes            TEXT,
    created_at       DATETIME      DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_assign_patient (patient_id),
    INDEX idx_assign_doctor (doctor_id),
    INDEX idx_assign_disease (disease_id),
    INDEX idx_assign_status (status)
) ENGINE=InnoDB;

-- View: all assignments with doctor context (LOCAL tables only).
-- NOTE (6-RDS topology): every database lives on its OWN RDS instance,
-- so cross-database JOINs are impossible. patient_name and disease_name
-- are attached by the doctor Lambda at runtime via live reads against
-- the patients / diseases instances (see backend/doctor-lambda).
CREATE OR REPLACE VIEW v_assignments_full AS
SELECT
    a.assignment_id,
    a.patient_id,
    a.doctor_id,
    CONCAT(d.first_name, ' ', d.last_name) AS doctor_name,
    d.specialization,
    a.disease_id,
    a.appointment_date,
    a.status,
    a.room_number,
    a.notes
FROM doctor_assignments a
LEFT JOIN doctors                       d   ON a.doctor_id  = d.doctor_id
ORDER BY a.appointment_date DESC;

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

-- View: all assignments with patient + doctor + disease context
-- NOTE: cross-database queries work because all 4 DBs live on the
-- same RDS MySQL instance and are queried via fully-qualified names.
CREATE OR REPLACE VIEW v_assignments_full AS
SELECT
    a.assignment_id,
    a.patient_id,
    CONCAT(p.first_name, ' ', p.last_name) AS patient_name,
    a.doctor_id,
    CONCAT(d.first_name, ' ', d.last_name) AS doctor_name,
    d.specialization,
    a.disease_id,
    dis.disease_name,
    a.appointment_date,
    a.status,
    a.room_number,
    a.notes
FROM doctor_assignments a
LEFT JOIN hospital_patients.patients   p   ON a.patient_id = p.patient_id
LEFT JOIN doctors                       d   ON a.doctor_id  = d.doctor_id
LEFT JOIN hospital_diseases.diseases  dis ON a.disease_id = dis.disease_id
ORDER BY a.appointment_date DESC;

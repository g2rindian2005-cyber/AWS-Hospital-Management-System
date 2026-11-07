-- ============================================================
-- DATABASE 2 (cont): hospital_billing -> payments table
-- Stores payment history linked to bills and patients
-- ============================================================

USE hospital_billing;

CREATE TABLE IF NOT EXISTS payments (
    payment_id      INT AUTO_INCREMENT PRIMARY KEY,
    bill_id         INT           NOT NULL,      -- FK (logical) -> bills.bill_id
    patient_id      INT           NOT NULL,      -- FK (logical) -> hospital_patients.patients.patient_id
    amount_paid     DECIMAL(10,2) NOT NULL,
    payment_method  ENUM('Cash','Card','UPI','Insurance','Bank Transfer','Cheque') NOT NULL DEFAULT 'Cash',
    payment_date    DATETIME      DEFAULT CURRENT_TIMESTAMP,
    transaction_id  VARCHAR(100),
    remarks         TEXT,
    INDEX idx_pay_bill (bill_id),
    INDEX idx_pay_patient (patient_id),
    INDEX idx_pay_date (payment_date)
) ENGINE=InnoDB;

-- Trigger: auto-update bill status after each payment
DELIMITER //
CREATE TRIGGER IF NOT EXISTS trg_payment_after_insert
AFTER INSERT ON payments
FOR EACH ROW
BEGIN
    DECLARE total_paid DECIMAL(10,2);
    DECLARE net_amt    DECIMAL(10,2);

    SELECT COALESCE(SUM(amount_paid), 0) INTO total_paid
    FROM payments WHERE bill_id = NEW.bill_id;

    SELECT net_amount INTO net_amt
    FROM bills WHERE bill_id = NEW.bill_id;

    IF total_paid >= net_amt THEN
        UPDATE bills SET status = 'Paid' WHERE bill_id = NEW.bill_id;
    ELSEIF total_paid > 0 THEN
        UPDATE bills SET status = 'Partial' WHERE bill_id = NEW.bill_id;
    END IF;
END//
DELIMITER ;

-- View: full payment history with bill context
CREATE OR REPLACE VIEW v_payment_history AS
SELECT
    p.payment_id,
    p.bill_id,
    p.patient_id,
    b.description AS bill_description,
    b.net_amount,
    p.amount_paid,
    p.payment_method,
    p.transaction_id,
    p.payment_date
FROM payments p
JOIN bills b ON p.bill_id = b.bill_id
ORDER BY p.payment_date DESC;

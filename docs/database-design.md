# Database Design

## 4 Synchronised Databases (one RDS MySQL instance)

### Database 1 — `hospital_patients`
**Table: `patients`**
| Column             | Type          | Notes                      |
|--------------------|---------------|----------------------------|
| patient_id (PK)    | INT AUTO_INC  | Shared key across all DBs  |
| first_name         | VARCHAR(100)  |                            |
| last_name          | VARCHAR(100)  |                            |
| date_of_birth      | DATE          |                            |
| gender             | ENUM          | Male/Female/Other          |
| phone              | VARCHAR(20)   |                            |
| email              | VARCHAR(150)  | Used for SES emails         |
| address            | TEXT          |                            |
| blood_group        | VARCHAR(5)    |                            |
| emergency_contact  | VARCHAR(20)   |                            |
| insurance_number   | VARCHAR(50)   |                            |
| registration_date  | DATETIME      | default NOW                |
| updated_at         | DATETIME      | ON UPDATE NOW              |

**View:** `v_patient_full` (full_name)

---

### Database 2 — `hospital_billing`
**Table: `bills`**
| Column      | Type           | Notes                              |
|-------------|----------------|------------------------------------|
| bill_id (PK)| INT AUTO_INC   |                                    |
| patient_id  | INT            | → hospital_patients.patients       |
| bill_date   | DATETIME       |                                    |
| description | TEXT           |                                    |
| category    | ENUM           | Consultation/Lab/Surgery/…         |
| amount      | DECIMAL(10,2) |                                    |
| discount    | DECIMAL(10,2) |                                    |
| net_amount  | GENERATED      | amount - discount (STORED)         |
| status      | ENUM           | Pending/Partial/Paid/Cancelled      |

**Table: `payments`**
| Column          | Type           | Notes                          |
|-----------------|----------------|--------------------------------|
| payment_id (PK) | INT AUTO_INC   |                                |
| bill_id (FK)    | INT            | → bills.bill_id                |
| patient_id      | INT            | → hospital_patients.patients   |
| amount_paid     | DECIMAL(10,2) |                                |
| payment_method  | ENUM           | Cash/Card/UPI/Insurance/…      |
| payment_date    | DATETIME       |                                |
| transaction_id  | VARCHAR(100)   |                                |

**Trigger:** `trg_payment_after_insert` — recalculates bill status.

**Views:** `v_pending_dues`, `v_payment_history`.

---

### Database 3 — `hospital_diseases`
**Table: `diseases`**
| Column          | Type          | Notes                          |
|-----------------|---------------|--------------------------------|
| disease_id (PK) | INT AUTO_INC  |                                |
| patient_id      | INT           | → hospital_patients.patients    |
| disease_name    | VARCHAR(200) |                                |
| diagnosis_date  | DATE          |                                |
| severity        | ENUM          | Mild/Moderate/Severe/Critical   |
| symptoms        | TEXT          |                                |
| description     | TEXT          |                                |
| treatment       | TEXT          |                                |
| prescribed_meds | TEXT          |                                |
| status          | ENUM          | Active/Under Treatment/Recovered/Chronic |
| diagnosed_by    | INT           | → hospital_doctors.doctors      |
| follow_up_date  | DATE          |                                |

**View:** `v_active_diseases`.

---

### Database 4 — `hospital_doctors`
**Table: `doctors`**
| Column            | Type          | Notes                        |
|-------------------|---------------|------------------------------|
| doctor_id (PK)    | INT AUTO_INC  |                              |
| first_name        | VARCHAR(100)  |                              |
| last_name         | VARCHAR(100)  |                              |
| specialization    | VARCHAR(150)  |                              |
| department        | VARCHAR(100)  |                              |
| phone             | VARCHAR(20)   |                              |
| email             | VARCHAR(150)  |                              |
| license_number    | VARCHAR(50)   |                              |
| availability      | ENUM          | Available/Busy/On Leave/Off  |
| consultation_fee  | DECIMAL(10,2)|                              |

**Table: `doctor_assignments`** ← synchronisation hub
| Column            | Type   | Notes                              |
|-------------------|--------|------------------------------------|
| assignment_id (PK)| INT    |                                    |
| patient_id        | INT    | → hospital_patients.patients       |
| doctor_id         | INT    | → hospital_doctors.doctors          |
| disease_id        | INT    | → hospital_diseases.diseases (opt)  |
| appointment_date  | DATETIME|                                    |
| status            | ENUM   | Assigned/Scheduled/Active/Completed/Cancelled |
| room_number       | VARCHAR(20)|                                  |
| notes             | TEXT   |                                    |

**View:** `v_assignments_full` (joins across all 4 databases).

---

## Synchronisation keys
```
hospital_patients.patients.patient_id  ◄──┐
        │                                 │
  ┌─────┴──────────┐  ┌───────────────────┴────────────┐
  │hospital_billing│  │hospital_diseases.diseases       │
  │.bills.patient_id│  │.patient_id                     │
  │.payments.patient_id│└───────────────┬────────────────┘
  └────────────────┘                   │
        │                              │
  hospital_doctors.doctor_assignments ──┘
  (.patient_id, .doctor_id, .disease_id)
```
One `patient_id` ties all 4 databases together → true synchronisation.

# API Documentation

Base URL: `https://<api-id>.execute-api.<region>.amazonaws.com/prod`

All responses are JSON. All mutations require `Content-Type: application/json`.

---

## Patients (`/patients`)
### `GET /patients`
→ `{ "count": N, "patients": [ {patient_id, first_name, last_name, date_of_birth, gender, phone, email, blood_group, registration_date} ] }`

### `GET /patients/{patient_id}`
→ `{ "patient": {...}, "synchronised": { "total_due": 500.00, "bills":[...], "diseases":[...], "assignments":[...] } }`

### `POST /patients`
Body: `{ "first_name":"Rahul", "last_name":"Sharma", "date_of_birth":"1990-05-14", "gender":"Male", "phone":"9876543210", "email":"...","address":"...","blood_group":"O+","emergency_contact":"...","insurance_number":"..." }`
→ `{ "message":"Patient created", "patient_id": 6 }`

### `PUT /patients/{patient_id}` — any subset of patient fields
### `DELETE /patients/{patient_id}`

---

## Billing (`/bills`, `/payments`, `/dues`)
### `GET /bills` — list all bills with patient name
### `GET /bills/{bill_id}` — bill + its payments
### `POST /bills` — `{ "patient_id":1, "description":"...", "category":"Consultation", "amount":1500, "discount":0 }`
### `PUT /bills/{bill_id}` — update fields
### `DELETE /bills/{bill_id}`
### `GET /bills/patient/{patient_id}` — bills for a patient

### `GET /payments` — all payments with patient name
### `GET /payments/patient/{patient_id}` — payment history
### `POST /payments` — `{ "bill_id":1, "patient_id":1, "amount_paid":1000, "payment_method":"UPI", "transaction_id":"TXN-1", "remarks":"..." }`

### `GET /dues` — all pending dues (synchronised: joins patients + bills + payments)

---

## Diseases (`/diseases`)
### `GET /diseases` — all disease records (with patient name)
### `GET /diseases/active` — active/under-treatment diseases
### `GET /diseases/{disease_id}`
### `GET /diseases/patient/{patient_id}` — disease history for a patient
### `POST /diseases` — `{ "patient_id":1, "disease_name":"Hypertension", "diagnosis_date":"2026-10-01", "severity":"Moderate", "symptoms":"...", "treatment":"...", "prescribed_meds":"...", "status":"Active", "diagnosed_by":2, "follow_up_date":"2026-11-15" }`
### `PUT /diseases/{disease_id}` — update fields
### `DELETE /diseases/{disease_id}`

---

## Doctors & Assignments (`/doctors`, `/assignments`)
### `GET /doctors` — all doctors
### `GET /doctors/{doctor_id}` — doctor + assigned patients (synchronised)
### `POST /doctors` — `{ "first_name":"Dr. Anil", "last_name":"Gupta", "specialization":"Cardiologist", "department":"Cardiology", "phone":"...", "email":"...", "availability":"Available", "consultation_fee":800 }`
### `PUT /doctors/{doctor_id}` — update fields
### `DELETE /doctors/{doctor_id}`

### `GET /assignments` — all assignments (joins patients + doctors + diseases)
### `GET /assignments/{assignment_id}`
### `GET /assignments/doctor/{doctor_id}` — assignments for a doctor
### `GET /assignments/patient/{patient_id}` — assignments for a patient
### `POST /assignments` — `{ "patient_id":1, "doctor_id":1, "disease_id":1, "appointment_date":"2026-11-15 10:00", "status":"Scheduled", "room_number":"C-101", "notes":"..." }`
### `PUT /assignments/{assignment_id}` — update fields
### `DELETE /assignments/{assignment_id}`

---

## Error format
`{ "error": "Human-readable message" }` with appropriate HTTP status (400/404/500).

## CORS
All endpoints return permissive CORS headers; `OPTIONS` is auto-handled.

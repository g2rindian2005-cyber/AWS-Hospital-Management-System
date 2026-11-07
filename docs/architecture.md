# Architecture

## Overview
The AWS Hospital Management System is a **serverless + RDS** cloud
application that manages patient records, billing, diseases, and
doctor assignments through **4 synchronised MySQL databases**.

## Architecture diagram

```
                        ┌─────────────────────────────────┐
                        │           Users (Browser)        │
                        └───────────────┬─────────────────┘
                                        │ HTTPS
                         ┌──────────────▼──────────────┐
                         │   S3 (static website)         │
                         │   or EC2 + Nginx (prod CDN)   │
                         │   frontend/ (3D animated UI)   │
                         └──────────────┬──────────────┘
                                        │ REST + CORS
                         ┌──────────────▼──────────────┐
                         │       API Gateway (REST)      │
                         │   {proxy+} → 4 Lambdas        │
                         └──┬─────┬──────┬───────┬──────┘
            ┌───────────────┘     │      │       └────────────────┐
   ┌────────▼────────┐  ┌─────────▼───┐ ┌─▼──────────┐  ┌──────────▼────────┐
   │ patient-lambda   │  │billing-    │ │disease-    │  │ doctor-lambda      │
   │ (DB: patients)   │  │lambda      │ │lambda      │  │ (DB: doctors +     │
   │                  │  │(DB: billing)│ │(DB: diseases)│  │  assignments)     │
   └────────┬─────────┘  └─────┬──────┘ └──────┬─────┘  └──────────┬─────────┘
            │                  │               │                   │
            └──────────────────┴───────┬───────┴───────────────────┘
                                     │ PyMySQL (3306)
                          ┌──────────▼──────────┐
                          │   RDS MySQL 8.0       │
                          │   (single instance,  │
                          │    4 databases)       │
                          │                       │
                          │  hospital_patients    │
                          │  hospital_billing      │
                          │  hospital_diseases     │
                          │  hospital_doctors      │
                          └───────────────────────┘
                                     │
                          ┌──────────▼──────────┐
                          │   Amazon SES (SMTP)  │
                          │   Email notifications │
                          └─────────────────────┘
```

## Data flow & synchronisation
1. **Patient registered** → `patient-lambda` inserts into
   `hospital_patients.patients`, returns a `patient_id`.
2. That **same `patient_id`** is the foreign key in:
   - `hospital_billing.bills.patient_id`
   - `hospital_diseases.diseases.patient_id`
   - `hospital_doctors.doctor_assignments.patient_id`
3. Because all 4 databases live on **one RDS instance**, the Lambdas
   use fully-qualified cross-database `JOIN`s to fetch synchronised
   views (e.g. a bill with the patient's name, a disease with the
   diagnosing doctor).
4. **Billing**: when a payment is recorded, a MySQL `TRIGGER`
   (`trg_payment_after_insert`) auto-updates the bill status
   (`Pending → Partial → Paid`) — keeping billing & dues in sync
   automatically.
5. **Email**: each write operation (register, bill, payment, assign)
   triggers a best-effort email via SES SMTP through the shared
   `email/send_email.py` module.

## Infrastructure (Terraform)
- **VPC** with 2 public + 2 private subnets, NAT Gateway, IGW.
- **RDS** MySQL subnet group + instance in private subnets.
- **4 Lambda functions** deployed in private subnets (VPC config) to
  reach RDS.
- **API Gateway** REST API with `{proxy+}` routes to each Lambda.
- **S3** bucket with static website hosting for the frontend.
- **EC2** (optional) running Nginx, fronting S3-synced content.
- **IAM** roles with least-privilege policies (RDS, S3, SES, logs).
- **Security groups**: RDS 3306 only from Lambda/EC2 SGs.

## Why 4 databases?
Separation of concerns + independent scaling/backup. Each domain
(patients, billing, diseases, doctors) is its own logical database
while sharing a physical instance for fast cross-DB joins — the best
of both microservice isolation and relational integrity.

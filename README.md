# 🏥 AWS Hospital Management System

A cloud-native hospital management application with **6 synchronised
MySQL databases**, **7 serverless Lambda microservices**, **API Gateway**,
**S3** static hosting, **EC2** (Nginx), **SES SMTP** email, and a
**fully animated 3D frontend** — all deployed with **Terraform**.

## Project Structure
```
AWS-Hospital-Management-System/
│
├── frontend/                    → Website (jo user dekhta hai)
│   ├── patients/                → Add / View / History
│   ├── billing/                 → Create Bill / Payments / Pending Dues
│   ├── diseases/                → Add Disease / History
│   ├── doctors/                 → Add / Assign / Appointments
│   ├── laboratory/              → Lab Orders / Order Test / Test Catalog
│   ├── pharmacy/                → Prescriptions / Add / Medicine Catalog
│   ├── js/                      → api.js (server se baat), ui.js (design + dark mode),
│   │                              patients/billing/diseases/doctors/laboratory/pharmacy.js
│   ├── css/style.css            → pura design
│   ├── dashboard.html           → main dashboard
│   ├── login.html               → OTP + JWT login
│   ├── index.html               → landing page
│   ├── reports.html
│   └── settings.html
│
├── backend/                     → Server-side code (7 Lambda services)
│   ├── auth-lambda/             → Login + OTP + JWT
│   ├── patient-lambda/          → Patients API
│   ├── billing-lambda/          → Bills + Payments API
│   ├── disease-lambda/          → Diseases API
│   ├── doctor-lambda/           → Doctors + Assignments API
│   ├── lab-lambda/              → Laboratory API
│   ├── pharmacy-lambda/         → Pharmacy API
│   └── local_server.py          → computer pe chalane ke liye
│      (har service: lambda_function.py + db_connection.py — db_connection
│       apne RDS instance se judta hai, dusre databases ko live padhta hai)
│
├── database/                    → 6 MySQL databases (har ek apne RDS instance pe)
│   ├── hospital_patients/       → schema + patients_sample_data.sql
│   ├── hospital_billing/        → bills/payments schemas + billing_sample_data.sql
│   ├── hospital_diseases/       → schema + diseases_sample_data.sql
│   ├── hospital_doctors/        → doctors/assignments schemas + doctors_sample_data.sql
│   ├── hospital_lab/            → laboratory.sql + lab_sample_data.sql
│   ├── hospital_pharmacy/       → pharmacy.sql + pharmacy_sample_data.sql
│   └── sample_data.sql          → combined sample data (local/single-instance)
│
├── terraform/                   → AWS pe deploy karne ka code
│   ├── main.tf                  → VPC, 6× RDS, 7× Lambda, API, S3, EC2 — sab
│   ├── variables.tf
│   ├── outputs.tf               → rds_endpoints (saare 6 addresses), api_gateway_url, …
│   └── deploy.sh
│
├── aws/                         → AWS guides (api-gateway, ec2, iam, lambda, rds, s3, ses-smtp)
├── docs/                        → MANUAL_DEPLOY.md, architecture, CICD
├── email/                       → Email templates + SMTP (OTP + receipts)
├── config/                      → config.py + .env.example
├── scripts/                     → validate_frontend.py
├── .github/workflows/           → CI/CD pipeline
└── requirements.txt   .gitignore   README.md
```

## The 6 Databases (all synchronised via shared `patient_id`)
| # | Database             | Own RDS instance | Purpose                                |
|---|----------------------|------------------|----------------------------------------|
| 1 | hospital_patients    | hospital-patients   | Patient names & personal info       |
| 2 | hospital_billing     | hospital-billing    | Bills, payment history & pending dues |
| 3 | hospital_diseases    | hospital-diseases   | Patient disease / diagnosis records |
| 4 | hospital_doctors     | hospital-doctors    | Doctors & doctor↔patient assignments |
| 5 | hospital_lab         | hospital-lab        | Lab tests & lab orders              |
| 6 | hospital_pharmacy    | hospital-pharmacy   | Medicines & prescriptions           |

Each database lives on **its own RDS MySQL instance** (6 in total).
Cross-database JOINs are impossible across instances, so the Lambdas
read each other's data **live** — every service knows every instance's
host (`DB_HOST_PATIENTS`, `DB_HOST_BILLING`, …) and attaches names and
summaries per request. The shared `patient_id` key links them together.

## Tech Stack
- **Frontend**: HTML5, CSS3 (3D transforms, glassmorphism, animations), Vanilla JS
- **Backend**: Python 3.11 AWS Lambda (7 microservices)
- **API**: Amazon API Gateway (REST, per-base-path proxy)
- **Database**: Amazon RDS MySQL 8.0 — **6 instances, one per database**
- **Storage**: Amazon S3 (static website) + EC2/Nginx
- **Email**: Amazon SES SMTP
- **Infra**: Terraform (VPC, RDS, Lambda, API GW, S3, EC2, IAM)

---

# 🚀 Complete Deploy Steps

> 📖 **For the full detailed walkthrough with verification & troubleshooting,
> see [`docs/deployment-guide.md`](docs/deployment-guide.md).**

## Prerequisites
- AWS account with admin access
- Terraform >= 1.3 installed
- AWS CLI configured (`aws configure`)
- MySQL client installed
- Python 3.11+ (for local testing)
- An EC2 key pair named `hospital-key`

## STEP 1 — Create EC2 Key Pair
```bash
aws ec2 create-key-pair --key-name hospital-key \
  --query 'KeyMaterial' --output text > ~/.ssh/hospital-key.pem
chmod 600 ~/.ssh/hospital-key.pem
```

## STEP 2 — Verify an SES Sender Email
```bash
aws ses verify-email-identity --email-address noreply@yourdomain.com --region us-east-1
# Check inbox, click verification link
```
Then generate SMTP credentials:
AWS Console → SES → SMTP Settings → Create My SMTP Credentials
Copy the username + password for `terraform.tfvars`.

## STEP 3 — Deploy Infrastructure with Terraform
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars: db_password, ses creds, ses_from_email
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```
Wait ~15-20 minutes (the RDS instances take the longest; the six are
created in parallel).

**What gets created:**
- **6 RDS MySQL instances — one per database** (`hospital-patients`,
  `hospital-billing`, `hospital-diseases`, `hospital-doctors`,
  `hospital-lab`, `hospital-pharmacy`), all in the private subnets
- **7 Lambda services** (auth, patient, billing, disease, doctor, lab,
  pharmacy). Every Lambda receives all six instance addresses
  (`DB_HOST_PATIENTS`, `DB_HOST_BILLING`, …) and reads the other
  databases **live** — there are no cross-instance SQL JOINs
- API Gateway (REST, per-base-path proxy routes), S3 website bucket,
  EC2/Nginx frontend host, IAM roles, VPC

> **Upgrading from the old single-RDS setup?** `terraform apply` will
> replace the one `hospital-mysql` instance with the six new ones and
> the databases start empty — re-run STEP 4 to initialise them.
> If the lab/pharmacy Lambdas were ever created by hand (AWS CLI)
> outside Terraform, delete those two functions and their `/lab` and
> `/pharmacy` API resources first, or the apply will hit name
> conflicts.

## STEP 4 — Initialise the 6 Databases
Each database has its OWN RDS endpoint — get them all from Terraform:
```bash
terraform output rds_endpoints
# { patients = "...", billing = "...", diseases = "...",
#   doctors = "...", lab = "...", pharmacy = "..." }
```
Run each SQL file against **its own instance's endpoint** (through the
EC2 instance — RDS is private), e.g.:
```bash
mysql -h <patients-endpoint> -u admin -p < database/hospital_patients/patients.sql
mysql -h <billing-endpoint>  -u admin -p < database/hospital_billing/bills.sql
mysql -h <billing-endpoint>  -u admin -p < database/hospital_billing/payments.sql
mysql -h <diseases-endpoint> -u admin -p < database/hospital_diseases/diseases.sql
mysql -h <doctors-endpoint>  -u admin -p < database/hospital_doctors/doctors.sql
mysql -h <doctors-endpoint>  -u admin -p < database/hospital_doctors/doctor_assignments.sql
mysql -h <lab-endpoint>      -u admin -p < database/hospital_lab/laboratory.sql
mysql -h <pharmacy-endpoint> -u admin -p < database/hospital_pharmacy/pharmacy.sql
```
Then load the sample data — one file per instance (these are the
per-database splits of `database/sample_data.sql`):
```bash
mysql -h <patients-endpoint> -u admin -p < database/hospital_patients/patients_sample_data.sql
mysql -h <doctors-endpoint>  -u admin -p < database/hospital_doctors/doctors_sample_data.sql
mysql -h <diseases-endpoint> -u admin -p < database/hospital_diseases/diseases_sample_data.sql
mysql -h <billing-endpoint>  -u admin -p < database/hospital_billing/billing_sample_data.sql
mysql -h <lab-endpoint>      -u admin -p < database/hospital_lab/lab_sample_data.sql
mysql -h <pharmacy-endpoint> -u admin -p < database/hospital_pharmacy/pharmacy_sample_data.sql
```
Expected result: 5 patients, 5 doctors, 5 diseases, 5 bills,
3 payments, 6 lab orders, 6 prescriptions. See `docs/MANUAL_DEPLOY.md`
for the full ordered schema list.

## STEP 5 — Wire the Frontend to API Gateway
```bash
API=$(terraform output -raw api_gateway_url)
echo "API: $API"
# Set it as the default in frontend/js/api.js (the API_BASE_URL fallback),
# or serve a js/config.js that sets window.HMS_CONFIG = { apiBase: "$API" }
# before api.js loads — config.js wins when present.
grep -n "execute-api" frontend/js/api.js   # find the current default
sed -i "s|https://[a-z0-9]*\.execute-api\.[a-z0-9-]*\.amazonaws\.com/prod|$API|g" frontend/js/api.js
```

## STEP 6 — Upload Frontend to S3
```bash
aws s3 sync frontend/ s3://hospital-management-frontend-bucket/ --delete
```
S3 website URL (from outputs):
```bash
terraform output s3_website_url
# → http://hospital-management-frontend-bucket.s3-website-us-east-1.amazonaws.com
```

## STEP 7 — (Optional) Deploy Frontend to EC2/Nginx
The EC2 user-data script already installed Nginx. Sync S3 → EC2:
```bash
EC2IP=$(terraform output -raw ec2_public_ip)
ssh -i ~/.ssh/hospital-key.pem ubuntu@$EC2IP \
  "aws s3 sync s3://hospital-management-frontend-bucket/ /var/www/hospital/ --delete"
echo "Open: http://$EC2IP"
```

## STEP 8 — Test the App (every feature)
1. Open the S3 website URL, the EC2 IP, or the GitHub Pages site.
2. Login with `admin` / `admin123`, then enter the OTP. Until the SES
   sender is verified (STEP 2/9), the code is shown on the login page
   itself; afterwards it arrives by email only.
3. Walk every module once — each one reads/writes its own RDS instance
   and pulls names live from the others:
   - **Dashboard** — stat cards and charts load
   - **Patients** — add a patient; open the patient → history shows
     bills, diseases and assignments from the other instances
   - **Doctors** — add a doctor; create an assignment (appointment)
   - **Diseases** — add a diagnosis for the patient
   - **Billing** — create a bill, record a payment, check Pending Dues
   - **Laboratory** — order a test, update its status/result
   - **Pharmacy** — create a prescription, dispense it (stock drops)
   - **Reports** — totals match the data you just entered
4. Check the patient's email for SES notifications (bill / receipt /
   appointment), once SES is verified.

## STEP 9 — Request SES Production Access
While in sandbox, only verified emails can receive notifications.
AWS Console → SES → Account dashboard → Request Production access.

## STEP 10 — Tear Down (stop costs)
Destroys everything, including **all six RDS instances**:
```bash
cd terraform
terraform destroy -var-file=terraform.tfvars
```

---

## Local Development (without AWS)
The frontend ships with a **mock-data fallback** so the UI works
immediately without any backend. Just open `frontend/index.html` in
a browser, or serve the folder:
```bash
cd frontend
python -m http.server 8080
# open http://localhost:8080
```

## Key Files Quick Reference
| What              | Where                                              |
|-------------------|----------------------------------------------------|
| Frontend entry    | `frontend/index.html`                              |
| API client        | `frontend/js/api.js`                               |
| Lambda handlers    | `backend/*/lambda_function.py`                     |
| DB schemas        | `database/*/*.sql`                                 |
| Email templates   | `email/templates/*.html`                           |
| Infra             | `terraform/main.tf`                                |
| API docs          | `docs/api-documentation.md`                        |
| Architecture      | `docs/architecture.md`                             |

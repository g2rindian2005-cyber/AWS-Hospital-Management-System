# 🏥 AWS Hospital Management System

A cloud-native hospital management application with **6 synchronised
MySQL databases**, **7 serverless Lambda microservices**, **API Gateway**,
**S3** static hosting, **EC2** (Nginx), **SES SMTP** email, and a
**fully animated 3D frontend** — all deployed with **Terraform**.

## Project Structure
```
AWS-Hospital-Management-System/
├── frontend/          3D animated UI (HTML + CSS + JS)
│   ├── index.html, login.html, dashboard.html
│   ├── patients/   billing/   diseases/   doctors/
│   ├── css/style.css
│   └── js/  api.js, patients.js, billing.js, diseases.js, doctors.js
├── backend/           4 AWS Lambda functions
│   ├── patient-lambda/   billing-lambda/
│   ├── disease-lambda/   doctor-lambda/
│   └── (each has lambda_function.py, db_connection.py, requirements.txt)
├── database/          4 MySQL schemas + sample data
│   ├── hospital_patients/   hospital_billing/
│   ├── hospital_diseases/   hospital_doctors/
│   └── sample_data.sql
├── aws/               AWS service config docs
│   ├── api-gateway/  ec2/  s3/  lambda/  rds/  ses-smtp/  iam/
├── email/             SES SMTP module + HTML templates
├── config/            config.py + .env.example
├── docs/              architecture, database-design, api-documentation
├── terraform/         Infrastructure as Code
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
Wait ~10-15 minutes (RDS takes the longest).

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
Sample data: `database/sample_data.sql` spans the patients/billing/
diseases/doctors instances (run each part against its instance), plus
`lab_sample_data.sql` and `pharmacy_sample_data.sql` on theirs. See
`docs/MANUAL_DEPLOY.md` for the full ordered list.

## STEP 5 — Wire the Frontend to API Gateway
```bash
API=$(terraform output -raw api_gateway_url)
# Replace the placeholder URL in api.js
sed -i "s|https://abc123.execute-api.*amazonaws.com.*|$API\"|" frontend/js/api.js
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

## STEP 8 — Test the App
1. Open the S3 website URL or EC2 IP in your browser.
2. Login with `admin` / `admin123`.
3. Try the dashboard, add a patient, create a bill, assign a doctor.
4. Check the patient's email for SES notifications.

## STEP 9 — Request SES Production Access
While in sandbox, only verified emails can receive notifications.
AWS Console → SES → Account dashboard → Request Production access.

## STEP 10 — Tear Down (stop costs)
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

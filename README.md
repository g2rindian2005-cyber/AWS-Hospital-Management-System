# 🏥 AWS Hospital Management System

A cloud-native hospital management application with **4 synchronised
MySQL databases**, **4 serverless Lambda microservices**, **API Gateway**,
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

## The 4 Databases (all synchronised via shared `patient_id`)
| # | Database             | Purpose                                       |
|---|----------------------|-----------------------------------------------|
| 1 | hospital_patients    | Patient names & personal info                 |
| 2 | hospital_billing     | Bills, payment history & pending dues         |
| 3 | hospital_diseases    | Patient disease / diagnosis records            |
| 4 | hospital_doctors     | Doctors & doctor↔patient assignments           |

All 4 live on **one RDS MySQL instance**, so the Lambdas use
cross-database JOINs to keep everything synchronised. The shared
`patient_id` key links them together.

## Tech Stack
- **Frontend**: HTML5, CSS3 (3D transforms, glassmorphism, animations), Vanilla JS
- **Backend**: Python 3.11 AWS Lambda (4 microservices)
- **API**: Amazon API Gateway (REST, per-base-path proxy)
- **Database**: Amazon RDS MySQL 8.0 (4 logical databases)
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

## STEP 4 — Initialise the 4 Databases
Use the RDS endpoint from Terraform outputs:
```bash
RDS=$(terraform output -raw rds_endpoint)
echo "RDS endpoint: $RDS"

mysql -h $RDS -u admin -p < database/hospital_patients/patients.sql
mysql -h $RDS -u admin -p < database/hospital_billing/bills.sql
mysql -h $RDS -u admin -p < database/hospital_billing/payments.sql
mysql -h $RDS -u admin -p < database/hospital_diseases/diseases.sql
mysql -h $RDS -u admin -p < database/hospital_doctors/doctors.sql
mysql -h $RDS -u admin -p < database/hospital_doctors/doctor_assignments.sql
mysql -h $RDS -u admin -p < database/sample_data.sql
```

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

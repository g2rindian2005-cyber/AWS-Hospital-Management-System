# Deployment Guide — AWS Hospital Management System

This is the **complete, step-by-step deployment process** for the entire
infrastructure and application. Follow the phases in order.

---

## Architecture Recap

```
 Browser → S3 website / EC2(Nginx) → API Gateway → 4 Lambdas → RDS MySQL (4 DBs)
                                                     ↘ SES SMTP (email)
```

All infrastructure is defined in `terraform/main.tf` and provisioned with
one `terraform apply`. This guide then initialises the databases, deploys
the frontend, and verifies everything works.

---

## Prerequisites (install once)

| Tool          | Why                              | Check command        |
|---------------|----------------------------------|----------------------|
| Terraform ≥1.3 | Provision AWS infra              | `terraform version`  |
| AWS CLI v2     | Interact with AWS                | `aws --version`     |
| MySQL client   | Load DB schemas                  | `mysql --version`    |
| Python 3.11    | Local testing (optional)         | `python --version`  |
| Git            | Clone/version                    | `git --version`     |

Configure AWS credentials:
```bash
aws configure
# AWS Access Key ID, Secret Access Key, region (e.g. us-east-1), output json
```

---

## PHASE 1 — AWS Account Prep (manual, ~10 min)

### 1.1 Create an EC2 key pair (for SSH to the Nginx server)
```bash
aws ec2 create-key-pair --key-name hospital-key \
  --query 'KeyMaterial' --output text > ~/.ssh/hospital-key.pem
chmod 600 ~/.ssh/hospital-key.pem     # Linux/Mac
# Windows PowerShell: icacls ~/.ssh/hospital-key.pem /inheritance:r /grant:r "$env:USERNAME:F"
```

### 1.2 Verify a SES sender email address
SES starts in **sandbox mode** — only verified addresses can receive mail.
```bash
aws ses verify-email-identity \
  --email-address noreply@yourdomain.com \
  --region us-east-1
# Check that inbox → click the verification link
```

### 1.3 Generate SES SMTP credentials
1. AWS Console → **Amazon SES** → **SMTP Settings** → **Create My SMTP Credentials**
2. Note the **IAM username** (looks like `AKIA…`) and the **generated password**
3. You'll paste these into `terraform.tfvars` in Phase 2

---

## PHASE 2 — Deploy Infrastructure with Terraform (~12 min)

### 2.1 Configure variables
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```
Edit `terraform.tfvars` — set at minimum:
```hcl
db_password       = "ChangeMeStrongPass123!"   # strong password for RDS
ssh_key_name      = "hospital-key"             # created in 1.1
ses_smtp_username = "AKIAXXXXXXXXXXXXXXXX"     # from 1.3
ses_smtp_password  = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
ses_from_email     = "noreply@yourdomain.com"  # verified in 1.2
```

### 2.2 Initialise Terraform (downloads AWS + archive providers)
```bash
terraform init
```

### 2.3 Preview what will be created
```bash
terraform plan -var-file=terraform.tfvars
```
Review the plan. You should see: 1 VPC, 4 subnets, NAT gateway, IGW,
1 RDS instance, 4 Lambda functions, 1 API Gateway (with routes), 1 S3
bucket, 1 EC2 instance, IAM roles, and security groups.

### 2.4 Apply — this creates everything (~12 min, RDS is slowest)
```bash
terraform apply -var-file=terraform.tfvars
# type "yes" when prompted
```

### 2.5 Capture the outputs
```bash
terraform output

# Save key values to variables for the next phases:
RDS_ENDPOINT=$(terraform output -raw rds_endpoint)
API_URL=$(terraform output -raw api_gateway_url)
S3_URL=$(terraform output -raw s3_website_url)
EC2_IP=$(terraform output -raw ec2_public_ip)

echo "RDS:  $RDS_ENDPOINT"
echo "API:  $API_URL"
echo "S3:   $S3_URL"
echo "EC2:  $EC2_IP"
```

✅ **Checkpoint:** All AWS resources exist now. RDS, Lambdas, API Gateway,
S3, and EC2 are all running.

---

## PHASE 3 — Initialise the 4 Databases (~2 min)

RDS created the instance but the 4 databases/tables must be loaded from
the SQL files. Connect from your machine (RDS is reachable via the
EC2 SG if your IP isn't allowed — in that case, tunnel through EC2 or
temporarily allow your IP in the RDS security group).

### 3.1 (If needed) allow your IP to reach RDS
```bash
MY_IP=$(curl -s ifconfig.me)
aws ec2 authorize-security-group-ingress \
  --group-id $(terraform output -raw | grep rds_sg) \
  --protocol tcp --port 3306 --cidr "$MY_IP/32" 2>/dev/null || true
```
*(Simplest: add a rule to the `hospital-rds-sg` security group for your IP on port 3306.)*

### 3.2 Run the schema files in order
```bash
cd ..   # back to project root

mysql -h "$RDS_ENDPOINT" -u admin -p < database/hospital_patients/patients.sql
mysql -h "$RDS_ENDPOINT" -u admin -p < database/hospital_billing/bills.sql
mysql -h "$RDS_ENDPOINT" -u admin -p < database/hospital_billing/payments.sql
mysql -h "$RDS_ENDPOINT" -u admin -p < database/hospital_diseases/diseases.sql
mysql -h "$RDS_ENDPOINT" -u admin -p < database/hospital_doctors/doctors.sql
mysql -h "$RDS_ENDPOINT" -u admin -p < database/hospital_doctors/doctor_assignments.sql
mysql -h "$RDS_ENDPOINT" -u admin -p < database/sample_data.sql
```
Enter the `db_password` you set in `terraform.tfvars` when prompted.

### 3.3 Verify the data loaded
```bash
mysql -h "$RDS_ENDPOINT" -u admin -p -e \
  "SHOW DATABASES; USE hospital_patients; SELECT COUNT(*) FROM patients;"
# Expect: 5 patients
```

✅ **Checkpoint:** All 4 databases created with tables + sample data.

---

## PHASE 4 — Deploy the Frontend (~1 min)

### 4.1 Point the frontend at your API Gateway URL
```bash
# Replace the placeholder URL in api.js with your real API URL
# (works on Linux/Mac with sed; on Windows use a text editor)
sed -i "s|https://abc123.execute-api.*amazonaws.com.*|$API_URL\"|" frontend/js/api.js
```

### 4.2 Upload frontend to S3
```bash
aws s3 sync frontend/ s3://hospital-management-frontend-bucket/ \
  --delete --exclude "*.DS_Store"
```

✅ **Checkpoint:** Open `$S3_URL` in a browser → you should see the 3D
animated landing page. Click **Login** → `admin` / `admin123`.

### 4.3 (Optional) Mirror to EC2 Nginx
The EC2 instance's user-data already installed Nginx. Sync S3 → EC2:
```bash
ssh -i ~/.ssh/hospital-key.pem ubuntu@$EC2_IP \
  "aws s3 sync s3://hospital-management-frontend-bucket/ /var/www/hospital/ --delete"
```
Now the frontend is also at `http://$EC2_IP`.

✅ **Checkpoint:** Open `http://$EC2_IP` → same 3D UI.

---

## PHASE 5 — Verify End-to-End

### 5.1 Test the API directly
```bash
curl -s "$API_URL/patients" | python -m json.tool
# Expect JSON with 5 patients from the sample data
```

### 5.2 Test through the UI
1. Open the S3 website URL (or EC2 IP)
2. Login: `admin` / `admin123`
3. Dashboard should show stats (5 patients, pending dues, diseases, assignments)
4. Go to **Patients → View Patients** → should list 5 patients
5. Go to **Billing → Pending Dues** → should show 3 pending bills
6. Go to **Doctors → Appointments** → should show 5 assignments
7. Go to **Patient History** → select a patient → see synced bills/diseases/assignments

### 5.3 Test a write operation (creates a patient)
1. **Patients → Add Patient** → fill form → Register
2. **View Patients** → new patient appears at top
3. Check the patient's email inbox → registration email (if SES out of sandbox)

✅ **Checkpoint:** Full system works — frontend → API Gateway → Lambda → RDS → email.

---

## PHASE 6 — SES Production Access (so anyone can receive emails)

In sandbox mode, only verified email addresses can receive mail. To send
to any patient email:

1. AWS Console → **SES** → **Account dashboard**
2. Click **Request production access**
3. Fill the form (use case: transactional hospital notifications)
4. AWS approves within ~24 hours

Until then, verify each test recipient:
```bash
aws ses verify-email-identity --email-address testpatient@email.com --region us-east-1
```

---

## PHASE 7 — Tear Down (stop all costs)

When you're done, destroy everything:
```bash
cd terraform
terraform destroy -var-file=terraform.tfvars
# type "yes"
```
This removes RDS, Lambdas, API Gateway, S3, EC2, VPC, NAT gateway, and
all IAM resources. **All charges stop.**

> ⚠️ `terraform destroy` deletes the RDS instance and its data
> (`skip_final_snapshot = true`). Back up data first if you need it.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `terraform apply` hangs on RDS | Normal — RDS takes 5-8 min. Wait. |
| Lambdas can't reach RDS | They're in the VPC. Confirm the RDS SG allows the Lambda SG on 3306 (it does by default in this Terraform). |
| `502 Bad Gateway` from API | Run schema SQL (Phase 3) — Lambdas return errors if tables are missing. Check CloudWatch logs: `aws logs tail /aws/lambda/hospital-patient-service` |
| CORS errors in browser | The Terraform sets CORS on all routes. If using a custom domain, update allowed origins. |
| No email received | SES is in sandbox — verify the recipient address first (Phase 6). Check SES sending statistics in console. |
| `AccessDenied` on Lambda | IAM role needs `ses:SendEmail` — included in `lambda_extras` policy. |
| S3 website 403 | Public-read bucket policy not applied — re-run `terraform apply` or apply the policy in `aws/s3/bucket-configuration.md`. |
| Can't connect to RDS from laptop | RDS is private. Tunnel via EC2 or add your IP to the RDS security group (Phase 3.1). |

---

## Cost Notes (us-east-1, approximate)

| Resource       | Free tier? | Est. cost/month |
|----------------|------------|-----------------|
| RDS t3.micro   | 750 hrs/yr | ~$14 |
| 4 Lambdas      | 1M req free | ~$0-2 |
| API Gateway    | 1M req free | ~$0-1 |
| S3             | 5 GB free   | ~$0.50 |
| EC2 t3.micro   | 750 hrs/yr  | ~$8 |
| NAT Gateway    | NO free tier | ~$32 |
| SES            | 62k emails free/yr (sandbox) | ~$0 |
| **Total**      |            | **~$55/month** |

> The NAT Gateway is the biggest cost. For a pure dev environment, you can
> remove it from Terraform and put Lambdas in public subnets (not
> recommended for production) to drop to ~$23/month. Destroy when idle.

---

## Quick Reference — All Commands

```bash
# 1. Prep
aws ec2 create-key-pair --key-name hospital-key --query 'KeyMaterial' --output text > ~/.ssh/hospital-key.pem
aws ses verify-email-identity --email-address noreply@yourdomain.com --region us-east-1

# 2. Infra
cd terraform && cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars
terraform init && terraform apply -var-file=terraform.tfvars
RDS=$(terraform output -raw rds_endpoint)
API=$(terraform output -raw api_gateway_url)

# 3. DB
cd ..
for f in database/hospital_patients/patients.sql database/hospital_billing/bills.sql \
         database/hospital_billing/payments.sql database/hospital_diseases/diseases.sql \
         database/hospital_doctors/doctors.sql database/hospital_doctors/doctor_assignments.sql \
         database/sample_data.sql; do mysql -h $RDS -u admin -p < $f; done

# 4. Frontend
sed -i "s|https://abc123.execute-api.*|$API\"|" frontend/js/api.js
aws s3 sync frontend/ s3://hospital-management-frontend-bucket/ --delete

# 5. Verify
curl -s $API/patients | python -m json.tool

# 7. Destroy
cd terraform && terraform destroy -var-file=terraform.tfvars
```

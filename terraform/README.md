# Terraform Infrastructure

Provisions the entire AWS stack for the Hospital Management System:
VPC, RDS MySQL (4 databases), 4 Lambda functions, API Gateway, S3
static website, EC2 (Nginx), IAM roles, and security groups.

## Files
| File                        | Purpose                                  |
|-----------------------------|------------------------------------------|
| `main.tf`                   | All AWS resources                        |
| `variables.tf`              | Input variables + defaults               |
| `outputs.tf`                | Useful outputs (endpoints, URLs, IPs)   |
| `terraform.tfvars.example`  | Copy to `terraform.tfvars`, fill values |

## Prerequisites
1. **Terraform** >= 1.3 installed (`terraform version`)
2. **AWS CLI** configured (`aws configure`)
3. An **EC2 key pair** named `hospital-key` (for SSH):
   ```bash
   aws ec2 create-key-pair --key-name hospital-key \
     --query 'KeyMaterial' --output text > ~/.ssh/hospital-key.pem
   chmod 600 ~/.ssh/hospital-key.pem
   ```
4. **SES** out of sandbox (or at least a verified sender email).

## Deploy steps
```bash
cd terraform

# 1. Initialise providers & download plugins
terraform init

# 2. Copy your variables
cp terraform.tfvars.example terraform.tfvars
#   ... edit terraform.tfvars (db_password, ses creds, etc.)

# 3. Preview the plan
terraform plan -var-file=terraform.tfvars

# 4. Apply (~10-15 min for RDS)
terraform apply -var-file=terraform.tfvars
```

## After `apply` completes
Terraform prints the outputs. Then:

```bash
# A. Initialise the 4 databases (use the RDS endpoint from outputs)
RDS=$(terraform output -raw rds_endpoint)
mysql -h $RDS -u admin -p < database/hospital_patients/patients.sql
mysql -h $RDS -u admin -p < database/hospital_billing/bills.sql
mysql -h $RDS -u admin -p < database/hospital_billing/payments.sql
mysql -h $RDS -u admin -p < database/hospital_diseases/diseases.sql
mysql -h $RDS -u admin -p < database/hospital_doctors/doctors.sql
mysql -h $RDS -u admin -p < database/hospital_doctors/doctor_assignments.sql
mysql -h $RDS -u admin -p < database/sample_data.sql          # seed data

# B. Point the frontend at the API Gateway URL
API=$(terraform output -raw api_gateway_url)
sed -i "s|https://abc123.execute-api.*|$API\"|" frontend/js/api.js

# C. Upload the frontend to S3
aws s3 sync frontend/ s3://hospital-management-frontend-bucket/ --delete

# D. (Optional) sync to EC2 Nginx
EC2IP=$(terraform output -raw ec2_public_ip)
ssh -i ~/.ssh/hospital-key.pem ubuntu@$EC2IP \
  "aws s3 sync s3://hospital-management-frontend-bucket/ /var/www/hospital/ --delete"

# E. Open the app
echo "S3:  http://hospital-management-frontend-bucket.s3-website-us-east-1.amazonaws.com"
echo "EC2: http://$EC2IP"
```

## Destroy (tears down everything — costs stop)
```bash
terraform destroy -var-file=terraform.tfvars
```

## Notes
- **RDS password**: pass via tfvars or better, SSM Parameter Store /
  `terraform import` a Secrets Manager secret. Never commit real passwords.
- **SES sandbox**: until you request production access, only verified
  email addresses can receive mail.
- **NAT Gateway** has an hourly cost (~$0.045/hr + data). Destroy when not
  in use for dev.

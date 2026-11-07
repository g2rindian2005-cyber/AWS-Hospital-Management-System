# Lambda Deployment Guide

Each of the 4 microservices is a separate Lambda function with its own
deployment package (zip). The Terraform in `terraform/main.tf` handles
this automatically; this guide covers the manual / CLI alternative.

## 1. Package a Lambda

Each Lambda folder (`backend/<service>-lambda/`) contains:
- `lambda_function.py` — handler entry point
- `db_connection.py` — MySQL helper
- `requirements.txt` — dependencies

```bash
cd backend/patient-lambda

# Create a clean package directory
rm -rf package && mkdir package

# Install dependencies into it
pip install --platform manylinux2014_x86_64 \
    --only-binary=:all: --target ./package -r requirements.txt

# Add the Lambda code + email module (for send_email)
cp lambda_function.py db_connection.py package/
cp -r ../../email package/email
cp ../../config/config.py package/config.py 2>/dev/null || true

# Zip everything
cd package
zip -r ../patient-lambda.zip .
cd ..
```

Repeat for `billing-lambda`, `disease-lambda`, `doctor-lambda`.

## 2. Create / update the function (CLI)
```bash
aws lambda create-function \
  --function-name hospital-patient-service \
  --runtime python3.11 \
  --handler lambda_function.lambda_handler \
  --zip fileb://patient-lambda.zip \
  --role arn:aws:iam::<account>:role/hospital-lambda-role \
  --timeout 30 --memory-size 256 \
  --vpc-config SubnetIds=<subnet-ids>,SecurityGroupIds=<sg-ids> \
  --environment Variables={DB_HOST=<rds-endpoint>,DB_USER=admin,DB_PASSWORD=<pass>,\
DB_PATIENTS=hospital_patients,SMTP_HOST=<ses-host>,SMTP_USERNAME=<u>,SMTP_PASSWORD=<p>,\
SMTP_FROM_EMAIL=<email>} \
  --region us-east-1
```

Update existing function:
```bash
aws lambda update-function-code \
  --function-name hospital-patient-service \
  --zip-file fileb://patient-lambda.zip
```

## 3. Environment variables per Lambda
All 4 share these (set in Terraform `lambda_env` locals):

| Key             | Example                               |
|-----------------|---------------------------------------|
| DB_HOST         | `hospital-mysql.xxxx.us-east-1.rds.amazonaws.com` |
| DB_PORT         | 3306                                  |
| DB_USER         | admin                                 |
| DB_PASSWORD     | (from SSM / Terraform)                 |
| DB_PATIENTS     | hospital_patients                     |
| DB_BILLING      | hospital_billing                      |
| DB_DISEASES     | hospital_diseases                     |
| DB_DOCTORS      | hospital_doctors                      |
| SMTP_HOST       | email-smtp.us-east-1.amazonaws.com     |
| SMTP_PORT       | 587                                    |
| SMTP_USERNAME   | (SES SMTP creds)                       |
| SMTP_PASSWORD   | (SES SMTP creds)                       |
| SMTP_FROM_EMAIL | noreply@yourdomain.com                 |

## 4. Test invocation
```bash
aws lambda invoke --function-name hospital-patient-service \
  --payload '{"httpMethod":"GET","resource":"/patients","pathParameters":null}' \
  --cli-binary-format raw-in-base64-out response.json
cat response.json
```

## Automated
Prefer `terraform apply` — it builds zips via the `archive_file`
data source and deploys all 4 functions, their IAM roles, VPC config,
and environment variables in one step.

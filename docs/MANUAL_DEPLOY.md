# Manual deployment (from your own machine)

Deploy the whole project with Terraform — no prompts, no manual build steps.
Tested from a fresh download of this repo.

## 0. You need

- Terraform ≥ 1.5 and Python 3 (`python3 --version`) — the dependency
  layer zip is built by `terraform/build_layer.py` during apply.
- AWS CLI configured with your credentials:

  ```bash
  aws configure            # region: us-east-1, output: json
  aws sts get-caller-identity   # must print your account id
  ```

## 1. Get the latest code

Download the repo again (or `git pull`) so you have the current
`terraform/` code, then:

```bash
cd AWS-Hospital-Management-System/terraform
```

## 2. Deploy the infrastructure

```bash
terraform init
terraform plan     # no variable prompts; expect ~160 to add on a fresh account
terraform apply    # type yes — or run ./deploy.sh for init + apply in one go
```

Takes ~10–15 minutes (RDS is the slow part). If apply stops with
"already exists" errors (bucket, Lambda names), the account still holds
the previous deployment and this copy has no `terraform.tfstate` —
stop and get the state file before retrying.

Useful values afterwards:

```bash
terraform output   # api_gateway_url, s3_website_url, ec2_public_ip, rds_endpoints
```

## 3. Upload the frontend to S3

Terraform creates the bucket and website config; the files themselves
are uploaded with one sync. The API URL from step 2 is written into
`js/api.js` first (the repo keeps a placeholder):

```bash
cd ..
API=$(cd terraform && terraform output -raw api_gateway_url)
rm -rf /tmp/site && cp -r frontend /tmp/site
sed -i "s|https://abc123.execute-api.us-east-1.amazonaws.com/prod|$API|g" /tmp/site/js/api.js
aws s3 sync /tmp/site s3://hospital-management-frontend-bucket/ --delete
```

(The EC2 server downloads its copy from S3 when it boots.)

## 4. Initialise the databases (first deploy only)

RDS is private, so this runs through the EC2 instance (same VPC).
**6-RDS topology:** every database lives on its OWN RDS instance —
`terraform output rds_endpoints` lists all six addresses. Run each
SQL file against **its own database's endpoint** (patients files →
patients endpoint, billing files → billing endpoint, and so on).
SSH in with the `hospital-key` pair, install a MySQL client, and run
the repo's SQL in this order (order matters):

1. `database/hospital_patients/patients.sql`
2. `database/hospital_diseases/diseases.sql`
3. `database/hospital_doctors/doctors.sql`
4. `database/hospital_doctors/doctor_assignments.sql`
5. `database/hospital_billing/payments.sql` — first run
   `sed -i 's/CREATE TRIGGER IF NOT EXISTS/CREATE TRIGGER/'` on it
6. `database/hospital_billing/bills.sql`
7. `database/hospital_lab/laboratory.sql`
8. `database/hospital_pharmacy/pharmacy.sql`
9. Sample data — per instance: `patients_sample_data.sql` (patients endpoint),
   `doctors_sample_data.sql` (doctors), `diseases_sample_data.sql` (diseases),
   `billing_sample_data.sql` (billing) — split from `database/sample_data.sql`
10. `database/hospital_lab/lab_sample_data.sql`
11. `database/hospital_pharmacy/pharmacy_sample_data.sql`

## 5. Verify

Open the `s3_website_url` output + `/login.html` and sign in:
user `admin`, password `admin123`. Until the SES sender address is
verified in the AWS console, the OTP code is shown on the login page
itself; after verification it arrives by email only.

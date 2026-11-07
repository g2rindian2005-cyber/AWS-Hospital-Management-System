# RDS MySQL Configuration

A single RDS MySQL instance hosts all **4 logical databases** so that
cross-database `JOIN` queries (synchronisation) work natively.

## Instance settings (default — override in Terraform variables)
| Property          | Value                          |
|-------------------|--------------------------------|
| Engine            | MySQL 8.0                      |
| Instance class    | `db.t3.micro` (dev) / `db.t3.small` (prod) |
| Storage           | 20 GB gp2 (autoscaling enabled)|
| Master username   | `admin`                        |
| Multi-AZ          | `false` (dev) / `true` (prod)  |
| Storage encrypted | true                           |
| Backup retention  | 7 days                         |
| Deletion protection | true (prod)                  |

## Security group
- Inbound: port 3306 from the **Lambda VPC subnets** and the EC2
  security group only (never public).
- Outbound: all.

## Databases created on first boot (via init SQL or manual run)
1. `hospital_patients`
2. `hospital_billing`
3. `hospital_diseases`
4. `hospital_doctors`

Run the schema files in `database/` in this order:
```bash
mysql -h <rds-endpoint> -u admin -p < database/hospital_patients/patients.sql
mysql -h <rds-endpoint> -u admin -p < database/hospital_billing/bills.sql
mysql -h <rds-endpoint> -u admin -p < database/hospital_billing/payments.sql
mysql -h <rds-endpoint> -u admin -p < database/hospital_diseases/diseases.sql
mysql -h <rds-endpoint> -u admin -p < database/hospital_doctors/doctors.sql
mysql -h <rds-endpoint> -u admin -p < database/hospital_doctors/doctor_assignments.sql
mysql -h <rds-endpoint> -u admin -p < database/sample_data.sql   # optional seed data
```

## Synchronisation model
All 4 databases share the **same MySQL instance**, so a query like:
```sql
SELECT b.bill_id, CONCAT(p.first_name,' ',p.last_name) AS patient_name,
       dis.disease_name
FROM hospital_billing.bills b
JOIN hospital_patients.patients  p   ON b.patient_id = p.patient_id
JOIN hospital_diseases.diseases  dis ON b.patient_id = dis.patient_id;
```
…executes natively. The shared `patient_id` key keeps every database
in sync: when a patient is created they get one `patient_id` used by
billing, diseases, and doctor assignments alike.

## Lambda connectivity
Because RDS is in a VPC, the Lambdas are also deployed in that VPC
(see Terraform `aws_lambda_function` → `vpc_config`). This requires a
NAT Gateway for the Lambdas to reach API Gateway / SES if they need
outbound internet; the provided Terraform includes one.

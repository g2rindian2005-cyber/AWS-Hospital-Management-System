#!/bin/bash
# One-time database bootstrap for the local docker-compose stack.
# Runs inside the MySQL container on first start: creates the four
# databases and the application user, then loads the repo's own SQL in
# dependency order (diseases before doctor_assignments, payments
# before bills), finishing with the sample data.
set -e
export MYSQL_PWD="$MYSQL_ROOT_PASSWORD"

mysql -uroot <<SQL
CREATE DATABASE IF NOT EXISTS hospital_patients;
CREATE DATABASE IF NOT EXISTS hospital_billing;
CREATE DATABASE IF NOT EXISTS hospital_diseases;
CREATE DATABASE IF NOT EXISTS hospital_doctors;
CREATE DATABASE IF NOT EXISTS hospital_lab;
CREATE USER IF NOT EXISTS 'admin'@'%' IDENTIFIED BY 'hospital_local_pw';
GRANT ALL PRIVILEGES ON \`hospital\_%\`.* TO 'admin'@'%';
FLUSH PRIVILEGES;
SQL

run() { echo "mysql-init: $1"; mysql -uroot < "$1"; }

run /sql/hospital_patients/patients.sql
run /sql/hospital_diseases/diseases.sql
run /sql/hospital_doctors/doctors.sql
run /sql/hospital_doctors/doctor_assignments.sql
# payments.sql uses MySQL-client DELIMITER (fine here) but also the
# non-standard CREATE TRIGGER IF NOT EXISTS, which MySQL rejects.
sed 's/CREATE TRIGGER IF NOT EXISTS/CREATE TRIGGER/' /sql/hospital_billing/payments.sql > /tmp/payments.sql
run /tmp/payments.sql
run /sql/hospital_billing/bills.sql
run /sql/hospital_lab/laboratory.sql
run /sql/sample_data.sql
run /sql/hospital_lab/lab_sample_data.sql
echo "mysql-init: done"

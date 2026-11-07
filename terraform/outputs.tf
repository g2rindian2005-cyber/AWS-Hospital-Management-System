# ============================================================
# Outputs — printed after `terraform apply`
# ============================================================

output "rds_endpoint" {
  description = "RDS MySQL endpoint — set as DB_HOST"
  value       = aws_db_instance.hospital_mysql.address
}

output "api_gateway_url" {
  description = "API Gateway invoke URL — set as API_GATEWAY_URL"
  value       = aws_api_gateway_stage.prod.invoke_url
}

output "s3_website_url" {
  description = "S3 static website endpoint"
  value       = "${aws_s3_bucket.frontend.id}.s3-website.${var.aws_region}.amazonaws.com"
}

output "ec2_public_ip" {
  description = "EC2 instance public IP (Nginx frontend)"
  value       = aws_instance.frontend_ec2.public_ip
}

output "lambda_function_names" {
  description = "Names of the 4 deployed Lambda functions"
  value       = aws_lambda_function.service[*].function_name
}

output "configuration_reminder" {
  description = "Next steps to wire the app to the infra"
  value       = <<EOF
  ─────────────────────────────────────────────
  1. Run the SQL schema:
     mysql -h ${aws_db_instance.hospital_mysql.address} -u admin -p < database/hospital_patients/patients.sql
     mysql -h ${aws_db_instance.hospital_mysql.address} -u admin -p < database/hospital_billing/bills.sql
     ... (see aws/rds/mysql-configuration.md)

  2. Set API URL in frontend/js/api.js:
     API_BASE_URL = "${aws_api_gateway_stage.prod.invoke_url}"

  3. Upload frontend to S3:
     aws s3 sync frontend/ s3://${aws_s3_bucket.frontend.id}/

  4. SES: verify your sender email + request production access.

  5. Open: http://${aws_s3_bucket.frontend.id}.s3-website.${var.aws_region}.amazonaws.com
     or http://${aws_instance.frontend_ec2.public_ip}
  ─────────────────────────────────────────────
EOF
}

"""
Central configuration for the AWS Hospital Management System.
All values are read from environment variables with safe defaults
for local development. In production these are injected via Lambda
environment variables / EC2 user-data / SSM Parameter Store.
"""
import os


def _env(key, default=""):
    return os.environ.get(key, default)


# ------------------------------------------------------------------
# RDS MySQL connection (shared instance, 4 logical databases)
# ------------------------------------------------------------------
DB_HOST     = _env("DB_HOST", "localhost")
DB_PORT     = int(_env("DB_PORT", "3306"))
DB_USER     = _env("DB_USER", "admin")
DB_PASSWORD = _env("DB_PASSWORD", "adminpassword")
DB_SSL_CA   = _env("DB_SSL_CA", "")  # path to RDS CA cert pem (optional)

# The four synchronised databases
DB_PATIENTS = _env("DB_PATIENTS", "hospital_patients")
DB_BILLING  = _env("DB_BILLING",  "hospital_billing")
DB_DISEASES = _env("DB_DISEASES", "hospital_diseases")
DB_DOCTORS  = _env("DB_DOCTORS",  "hospital_doctors")

ALL_DATABASES = [DB_PATIENTS, DB_BILLING, DB_DISEASES, DB_DOCTORS]

# ------------------------------------------------------------------
# AWS / S3
# ------------------------------------------------------------------
AWS_REGION       = _env("AWS_REGION", "us-east-1")
S3_BUCKET_NAME   = _env("S3_BUCKET_NAME", "hospital-management-frontend-bucket")
S3_WEBSITE_URL   = _env("S3_WEBSITE_URL", "")

# ------------------------------------------------------------------
# API Gateway
# ------------------------------------------------------------------
API_GATEWAY_URL  = _env("API_GATEWAY_URL", "https://abc123.execute-api.us-east-1.amazonaws.com/prod")

# ------------------------------------------------------------------
# SES SMTP (for email notifications)
# ------------------------------------------------------------------
SMTP_HOST        = _env("SMTP_HOST", "email-smtp.us-east-1.amazonaws.com")
SMTP_PORT        = int(_env("SMTP_PORT", "587"))
SMTP_USERNAME    = _env("SMTP_USERNAME", "")   # SES SMTP credentials IAM user
SMTP_PASSWORD    = _env("SMTP_PASSWORD", "")   # SES SMTP password
SMTP_FROM_EMAIL  = _env("SMTP_FROM_EMAIL", "noreply@hospital.com")
SMTP_USE_TLS     = _env("SMTP_USE_TLS", "true").lower() == "true"

# ------------------------------------------------------------------
# Application
# ------------------------------------------------------------------
APP_NAME    = "AWS Hospital Management System"
APP_VERSION = "1.0.0"
JWT_SECRET  = _env("JWT_SECRET", "change-me-in-production")

# Default admin credentials (for first-time login demo)
ADMIN_USERNAME = _env("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = _env("ADMIN_PASSWORD", "admin123")


def get_db_config(database_name):
    """Return a connection-ready dict for the given database."""
    return {
        "host":     DB_HOST,
        "port":     DB_PORT,
        "user":     DB_USER,
        "password": DB_PASSWORD,
        "database": database_name,
        "charset":  "utf8mb4",
        "cursorclass": "pymysql.cursors.DictCursor",
    }

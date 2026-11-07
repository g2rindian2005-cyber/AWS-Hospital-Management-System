# ============================================================
# Input variables — override in terraform.tfvars
# ============================================================

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project prefix used in resource names"
  type        = string
  default     = "hospital"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "prod"
}

# ---- Networking ----
variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "AZs to spread resources across"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

# ---- RDS ----
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "RDS storage in GB"
  type        = number
  default     = 20
}

variable "db_name" {
  description = "Initial database name (4 DBs created via SQL init)"
  type        = string
  default     = "hospital_patients"
}

variable "db_username" {
  description = "RDS master username"
  type        = string
  default     = "admin"
}

variable "db_password" {
  description = "RDS master password (use tfvars or SSM — NOT committed)"
  type        = string
  sensitive   = true
  default     = "ChangeMeStrongPass123!"
}

# ---- EC2 ----
variable "ec2_instance_type" {
  description = "EC2 instance type for Nginx frontend"
  type        = string
  default     = "t3.micro"
}

variable "ssh_key_name" {
  description = "Name of the EC2 key pair for SSH access"
  type        = string
  default     = "hospital-key"
}

# ---- SES SMTP ----
variable "ses_smtp_username" {
  description = "SES SMTP username"
  type        = string
  default     = ""
}

variable "ses_smtp_password" {
  description = "SES SMTP password"
  type        = string
  sensitive   = true
  default     = ""
}

variable "ses_from_email" {
  description = "Verified SES sender email"
  type        = string
  default     = "noreply@hospital.com"
}

# ---- Lambda ----
variable "lambda_memory" {
  description = "Memory allocated to each Lambda (MB)"
  type        = number
  default     = 256
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 30
}

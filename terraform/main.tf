# ============================================================
# AWS Hospital Management System — Infrastructure as Code
# Provisions: VPC, RDS MySQL, 4 Lambdas, API Gateway, S3, EC2, IAM
# ============================================================

terraform {
  required_version = ">= 1.3.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Tag everything for easy identification
locals {
  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
  common_env = {
    DB_HOST         = aws_db_instance.hospital_mysql.address
    DB_PORT         = "3306"
    DB_USER         = var.db_username
    DB_PASSWORD     = var.db_password
    DB_PATIENTS     = "hospital_patients"
    DB_BILLING      = "hospital_billing"
    DB_DISEASES     = "hospital_diseases"
    DB_DOCTORS      = "hospital_doctors"
    SMTP_HOST       = "email-smtp.${var.aws_region}.amazonaws.com"
    SMTP_PORT       = "587"
    AUTH_USERNAME   = var.auth_admin_username
    AUTH_EMAIL      = var.ses_from_email
    AUTH_PASSWORD   = var.auth_admin_password
    JWT_SECRET      = var.jwt_secret
    SMTP_USERNAME   = var.ses_smtp_username
    SMTP_PASSWORD   = var.ses_smtp_password
    SMTP_FROM_EMAIL = var.ses_from_email
  }
}

# ============================================================
# VPC
# ============================================================
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = merge(local.tags, { Name = "${var.project_name}-vpc" })
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
  tags   = merge(local.tags, { Name = "${var.project_name}-igw" })
}

# Public subnets (EC2 + NAT)
resource "aws_subnet" "public" {
  count                   = length(var.availability_zones)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true
  tags                    = merge(local.tags, { Name = "${var.project_name}-public-${count.index}" })
}

# Private subnets (RDS + Lambda)
resource "aws_subnet" "private" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 10)
  availability_zone = var.availability_zones[count.index]
  tags              = merge(local.tags, { Name = "${var.project_name}-private-${count.index}" })
}

# NAT Gateway so Lambdas in private subnets can reach SES / API GW
resource "aws_eip" "nat" {
  domain = "vpc"
  tags   = merge(local.tags, { Name = "${var.project_name}-nat-eip" })
}

resource "aws_nat_gateway" "nat" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id
  tags          = merge(local.tags, { Name = "${var.project_name}-nat" })
  depends_on    = [aws_internet_gateway.igw]
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
  tags = merge(local.tags, { Name = "${var.project_name}-rt-public" })
}

resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat.id
  }
  tags = merge(local.tags, { Name = "${var.project_name}-rt-private" })
}

resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# ============================================================
# Security Groups
# ============================================================
resource "aws_security_group" "rds" {
  name        = "${var.project_name}-rds-sg"
  description = "Allow MySQL from Lambda and EC2"
  vpc_id      = aws_vpc.main.id
  ingress {
    description     = "MySQL from Lambda SG"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id]
  }
  ingress {
    description     = "MySQL from EC2 SG"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = local.tags
}

resource "aws_security_group" "lambda" {
  name        = "${var.project_name}-lambda-sg"
  description = "Allow Lambda outbound to RDS and internet (via NAT)"
  vpc_id      = aws_vpc.main.id
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = local.tags
}

resource "aws_security_group" "ec2" {
  name        = "${var.project_name}-ec2-sg"
  description = "Allow HTTP/SSH to EC2"
  vpc_id      = aws_vpc.main.id
  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = local.tags
}

# ============================================================
# RDS MySQL (4 databases on one instance)
# ============================================================
resource "aws_db_subnet_group" "hospital" {
  name       = "${var.project_name}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id
  tags       = local.tags
}

resource "aws_db_instance" "hospital_mysql" {
  identifier              = "${var.project_name}-mysql"
  engine                  = "mysql"
  engine_version          = "8.0"
  instance_class          = var.db_instance_class
  allocated_storage       = var.db_allocated_storage
  storage_type            = "gp2"
  db_name                 = var.db_name
  username                = var.db_username
  password                = var.db_password
  db_subnet_group_name    = aws_db_subnet_group.hospital.name
  vpc_security_group_ids  = [aws_security_group.rds.id]
  publicly_accessible     = false
  skip_final_snapshot     = true
  backup_retention_period = 7
  storage_encrypted       = true
  tags                    = local.tags
}

# ============================================================
# IAM — Lambda execution role
# ============================================================
data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda" {
  name               = "${var.project_name}-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
  tags               = local.tags
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role_policy" "lambda_extras" {
  name = "${var.project_name}-lambda-extras"
  role = aws_iam_role.lambda.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"], Resource = "*" },
      { Effect = "Allow", Action = ["ses:SendEmail", "ses:SendRawEmail"], Resource = "*" },
    ]
  })
}

# ============================================================
# Lambda packages (archive_file builds the zip from source)
# ============================================================
locals {
  lambda_services = [
    { name = "patient", source = "../backend/patient-lambda" },
    { name = "billing", source = "../backend/billing-lambda" },
    { name = "disease", source = "../backend/disease-lambda" },
    { name = "doctor", source = "../backend/doctor-lambda" },
    { name = "auth", source = "../backend/auth-lambda" },
  ]
}

# Install deps + zip each lambda directory
resource "archive_file" "lambda_zip" {
  count       = length(local.lambda_services)
  type        = "zip"
  source_dir  = local.lambda_services[count.index].source
  output_path = "${path.module}/build/${local.lambda_services[count.index].name}.zip"
}

# Shared dependencies layer (PyMySQL + cryptography from requirements.txt).
# Built locally: pip install -t layer/python PyMySQL cryptography, zipped as
# build/deps-layer.zip. archive_file above only zips source code, so without
# this layer every function fails with "No module named 'pymysql'".
resource "aws_lambda_layer_version" "deps" {
  filename            = "${path.module}/build/deps-layer.zip"
  layer_name          = "${var.project_name}-deps"
  compatible_runtimes = ["python3.11"]
  source_code_hash    = filebase64sha256("${path.module}/build/deps-layer.zip")
  description         = "PyMySQL + cryptography for hospital Lambda services"
}

# ============================================================
# Lambda functions (in VPC so they reach RDS)
# ============================================================
resource "aws_lambda_function" "service" {
  count            = length(local.lambda_services)
  function_name    = "${var.project_name}-${local.lambda_services[count.index].name}-service"
  runtime          = "python3.11"
  handler          = "lambda_function.lambda_handler"
  role             = aws_iam_role.lambda.arn
  filename         = archive_file.lambda_zip[count.index].output_path
  source_code_hash = archive_file.lambda_zip[count.index].output_base64sha256
  layers           = [aws_lambda_layer_version.deps.arn]
  memory_size      = var.lambda_memory
  timeout          = var.lambda_timeout

  vpc_config {
    subnet_ids         = aws_subnet.private[*].id
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = local.common_env
  }
  tags = local.tags
}

# ============================================================
# API Gateway — REST API with per-base-path proxy routes
# Each base path (patients, bills, payments, dues, diseases,
# doctors, assignments) gets its own resource + {proxy+} child,
# each routing to the correct Lambda via AWS_PROXY.
# ============================================================
locals {
  route_map = {
    patients    = 0 # -> patient-lambda
    bills       = 1 # -> billing-lambda
    payments    = 1 # -> billing-lambda
    dues        = 1 # -> billing-lambda
    diseases    = 2 # -> disease-lambda
    doctors     = 3 # -> doctor-lambda
    assignments = 3 # -> doctor-lambda
    auth        = 4 # -> auth-lambda
  }
}

resource "aws_api_gateway_rest_api" "hospital" {
  name        = "${var.project_name}-api"
  description = "Hospital Management System API"
  tags        = local.tags
}

# Top-level resource per base path: /patients, /bills, ...
resource "aws_api_gateway_resource" "base" {
  for_each    = local.route_map
  rest_api_id = aws_api_gateway_rest_api.hospital.id
  parent_id   = aws_api_gateway_rest_api.hospital.root_resource_id
  path_part   = each.key
}

# Child proxy resource: /patients/{proxy+}, /bills/{proxy+}, ...
resource "aws_api_gateway_resource" "proxy" {
  for_each    = local.route_map
  rest_api_id = aws_api_gateway_rest_api.hospital.id
  parent_id   = aws_api_gateway_resource.base[each.key].id
  path_part   = "{proxy+}"
}

# ANY method on the base resource (handles GET /patients)
resource "aws_api_gateway_method" "base_any" {
  for_each      = local.route_map
  rest_api_id   = aws_api_gateway_rest_api.hospital.id
  resource_id   = aws_api_gateway_resource.base[each.key].id
  http_method   = "ANY"
  authorization = "NONE"
}

# ANY method on the proxy child (handles /patients/123, /bills/patient/1)
resource "aws_api_gateway_method" "proxy_any" {
  for_each      = local.route_map
  rest_api_id   = aws_api_gateway_rest_api.hospital.id
  resource_id   = aws_api_gateway_resource.proxy[each.key].id
  http_method   = "ANY"
  authorization = "NONE"
}

# Integration: base resource -> correct Lambda
resource "aws_api_gateway_integration" "base" {
  for_each                = local.route_map
  rest_api_id             = aws_api_gateway_rest_api.hospital.id
  resource_id             = aws_api_gateway_resource.base[each.key].id
  http_method             = aws_api_gateway_method.base_any[each.key].http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.service[local.route_map[each.key]].invoke_arn
}

# Integration: proxy child -> correct Lambda
resource "aws_api_gateway_integration" "proxy" {
  for_each                = local.route_map
  rest_api_id             = aws_api_gateway_rest_api.hospital.id
  resource_id             = aws_api_gateway_resource.proxy[each.key].id
  http_method             = aws_api_gateway_method.proxy_any[each.key].http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.service[local.route_map[each.key]].invoke_arn
}

# CORS: OPTIONS on base + proxy for each base path
resource "aws_api_gateway_method" "base_options" {
  for_each      = local.route_map
  rest_api_id   = aws_api_gateway_rest_api.hospital.id
  resource_id   = aws_api_gateway_resource.base[each.key].id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "proxy_options" {
  for_each      = local.route_map
  rest_api_id   = aws_api_gateway_rest_api.hospital.id
  resource_id   = aws_api_gateway_resource.proxy[each.key].id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "cors_base" {
  for_each    = local.route_map
  rest_api_id = aws_api_gateway_rest_api.hospital.id
  resource_id = aws_api_gateway_resource.base[each.key].id
  http_method = aws_api_gateway_method.base_options[each.key].http_method
  type        = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_integration" "cors_proxy" {
  for_each    = local.route_map
  rest_api_id = aws_api_gateway_rest_api.hospital.id
  resource_id = aws_api_gateway_resource.proxy[each.key].id
  http_method = aws_api_gateway_method.proxy_options[each.key].http_method
  type        = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "cors_base" {
  for_each    = local.route_map
  rest_api_id = aws_api_gateway_rest_api.hospital.id
  resource_id = aws_api_gateway_resource.base[each.key].id
  http_method = aws_api_gateway_method.base_options[each.key].http_method
  status_code = "200"
  response_models = {
    "application/json" = "Empty"
  }
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Headers" = true
  }
  depends_on = [aws_api_gateway_integration.cors_base]
}

resource "aws_api_gateway_method_response" "cors_proxy" {
  for_each    = local.route_map
  rest_api_id = aws_api_gateway_rest_api.hospital.id
  resource_id = aws_api_gateway_resource.proxy[each.key].id
  http_method = aws_api_gateway_method.proxy_options[each.key].http_method
  status_code = "200"
  response_models = {
    "application/json" = "Empty"
  }
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Headers" = true
  }
  depends_on = [aws_api_gateway_integration.cors_proxy]
}

# Integration responses that set the actual CORS header values
resource "aws_api_gateway_integration_response" "cors_base" {
  for_each    = local.route_map
  rest_api_id = aws_api_gateway_rest_api.hospital.id
  resource_id = aws_api_gateway_resource.base[each.key].id
  http_method = aws_api_gateway_method.base_options[each.key].http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
  }
  depends_on = [aws_api_gateway_method_response.cors_base]
}

resource "aws_api_gateway_integration_response" "cors_proxy" {
  for_each    = local.route_map
  rest_api_id = aws_api_gateway_rest_api.hospital.id
  resource_id = aws_api_gateway_resource.proxy[each.key].id
  http_method = aws_api_gateway_method.proxy_options[each.key].http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
  }
  depends_on = [aws_api_gateway_method_response.cors_proxy]
}

# Permissions for API Gateway to invoke each Lambda
resource "aws_lambda_permission" "apigw" {
  count         = length(local.lambda_services)
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.service[count.index].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.hospital.execution_arn}/*/*"
}

resource "aws_api_gateway_deployment" "hospital" {
  rest_api_id = aws_api_gateway_rest_api.hospital.id
  depends_on = [
    aws_api_gateway_integration.base,
    aws_api_gateway_integration.proxy,
    aws_api_gateway_integration.cors_base,
    aws_api_gateway_integration.cors_proxy,
  ]
  triggers = {
    redeployment = sha1(jsonencode([
      keys(aws_api_gateway_resource.base),
      keys(aws_api_gateway_resource.proxy),
    ]))
  }
  lifecycle { create_before_destroy = true }
}

resource "aws_api_gateway_stage" "prod" {
  rest_api_id   = aws_api_gateway_rest_api.hospital.id
  stage_name    = var.environment
  deployment_id = aws_api_gateway_deployment.hospital.id
  tags          = local.tags
}

# ============================================================
# S3 — static website hosting for the frontend
# ============================================================
resource "aws_s3_bucket" "frontend" {
  bucket = "${var.project_name}-management-frontend-bucket"
  tags   = local.tags
}

resource "aws_s3_bucket_versioning" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket                  = aws_s3_bucket.frontend.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  index_document { suffix = "index.html" }
  error_document { key = "index.html" }
}

resource "aws_s3_bucket_policy" "frontend_public_read" {
  bucket = aws_s3_bucket.frontend.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "PublicReadGetObject"
      Effect    = "Allow"
      Principal = "*"
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.frontend.arn}/*"
    }]
  })
  depends_on = [aws_s3_bucket_public_access_block.frontend]
}

# ============================================================
# EC2 — Nginx serving the frontend (production front)
# ============================================================
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

resource "aws_instance" "frontend_ec2" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.ec2_instance_type
  subnet_id              = aws_subnet.public[0].id
  vpc_security_group_ids = [aws_security_group.ec2.id]
  key_name               = var.ssh_key_name
  user_data              = file("../aws/ec2/install-nginx.sh")
  tags                   = merge(local.tags, { Name = "${var.project_name}-frontend-ec2" })
}

# Stable public address for the EC2 mirror: without this, every instance
# replacement changes the IP (it changed twice during the first deploy).
resource "aws_eip" "frontend" {
  instance = aws_instance.frontend_ec2.id
  domain   = "vpc"
  tags     = merge(local.tags, { Name = "${var.project_name}-frontend-eip" })
}

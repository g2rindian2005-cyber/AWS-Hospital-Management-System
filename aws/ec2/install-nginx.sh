#!/bin/bash
# ============================================================
# EC2 user-data script: installs Nginx and serves the frontend
# Run this as user-data when launching the EC2 instance, or
# SSH in and run manually.
# ============================================================
set -e

echo "=== Installing Nginx ==="
apt-get update -y
apt-get install -y nginx

echo "=== Configuring Nginx for Hospital frontend ==="
mkdir -p /var/www/hospital

# Nginx server block — reverse-proxies /api/* to API Gateway,
# serves everything else from the S3-synced frontend directory.
cat > /etc/nginx/sites-available/hospital <<'NGINX'
server {
    listen 80;
    server_name _;
    root /var/www/hospital;
    index index.html;

    # Gzip for performance
    gzip on;
    gzip_types text/css application/javascript application/json image/svg+xml;

    # Cache static assets
    location ~* \.(css|js|jpg|png|gif|ico|svg|woff2)$ {
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    # API proxy → API Gateway (update the hostname after deploy)
    location /api/ {
        proxy_pass https://API_ID.execute-api.REGION.amazonaws.com/prod/;
        proxy_set_header Host API_ID.execute-api.REGION.amazonaws.com;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/hospital /etc/nginx/sites-enabled/hospital
rm -f /etc/nginx/sites-enabled/default

# Install AWS CLI for syncing frontend from S3
apt-get install -y awscli

echo "=== Installing MySQL client (for debugging RDS) ==="
apt-get install -y mysql-client

echo "=== Restarting Nginx ==="
systemctl restart nginx
systemctl enable nginx

echo "=== Nginx setup complete ==="
echo "Frontend will be served from /var/www/hospital"
echo "Sync with:  aws s3 sync s3://hospital-management-frontend-bucket /var/www/hospital"

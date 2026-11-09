#!/bin/bash
# ============================================================
# EC2 user-data script: installs Nginx and serves the frontend.
#
# Hardened after the first deploy: the original version used
# `set -e` and died when apt ran before the NAT gateway was
# ready, and it never actually copied the frontend files.
# This version retries package installs, tolerates optional
# failures, syncs the frontend from the (public) S3 bucket,
# and always tries to leave nginx running.
# ============================================================
exec > /var/log/hospital-setup.log 2>&1
set -x

export DEBIAN_FRONTEND=noninteractive
BUCKET="hospital-management-frontend-bucket"
WEBROOT="/var/www/hospital"
API_HOST="s5x2pju9d3.execute-api.us-east-1.amazonaws.com"

# Wait until apt + network work (NAT may still be provisioning)
for i in $(seq 1 30); do
  apt-get update -y && break
  echo "apt update failed, retry $i"; sleep 10
done

echo "=== Installing Nginx ==="
for i in 1 2 3 4 5; do
  apt-get install -y nginx && break
  sleep 10
done

echo "=== Configuring Nginx for Hospital frontend ==="
mkdir -p "$WEBROOT"
cat > /etc/nginx/sites-available/hospital <<NGINX
server {
    listen 80;
    server_name _;
    root $WEBROOT;
    index index.html;

    gzip on;
    gzip_types text/css application/javascript application/json image/svg+xml;

    location ~* \.(css|js|jpg|png|gif|ico|svg|woff2)$ {
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    # Optional API proxy -> API Gateway (the frontend's api.js already
    # points at the API directly; this is a same-origin alternative)
    location /api/ {
        proxy_pass https://$API_HOST/prod/;
        proxy_set_header Host $API_HOST;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location / {
        try_files \$uri \$uri/ /index.html;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/hospital /etc/nginx/sites-enabled/hospital
rm -f /etc/nginx/sites-enabled/default
nginx -t && (systemctl restart nginx || service nginx restart || nginx)
systemctl enable nginx || true

echo "=== Installing AWS CLI (for the S3 sync) ==="
if ! command -v aws >/dev/null 2>&1; then
  apt-get install -y awscli || apt-get install -y python3-pip && pip3 install --quiet awscli || true
fi

echo "=== Syncing frontend from S3 ==="
if command -v aws >/dev/null 2>&1; then
  for i in 1 2 3 4 5 6; do
    aws s3 sync "s3://$BUCKET" "$WEBROOT" --no-sign-request && break
    echo "s3 sync failed, retry $i"; sleep 15
  done
fi
chown -R www-data:www-data "$WEBROOT" || true
(systemctl restart nginx || service nginx restart || nginx -s reload) || true

echo "=== Installing MySQL client (optional, for debugging RDS) ==="
apt-get install -y mysql-client || true

echo "=== Setup complete ==="

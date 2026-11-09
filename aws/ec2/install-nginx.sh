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

echo "=== Downloading frontend files from the public S3 website ==="
# NOTE: `aws s3 sync` cannot work here — the bucket policy grants public
# GetObject but NOT ListBucket, and sync needs to list. Plain HTTPS GETs
# of the known files work fine, so fetch them one by one.
SITE="http://$BUCKET.s3-website.us-east-1.amazonaws.com"
FILES="index.html login.html dashboard.html reports.html settings.html sidebar.html
css/style.css
js/api.js js/ui.js js/patients.js js/billing.js js/diseases.js js/doctors.js
patients/add-patient.html patients/view-patient.html patients/patient-history.html
billing/create-bill.html billing/payment.html billing/pending-dues.html
diseases/add-disease.html diseases/disease-history.html
doctors/add-doctor.html doctors/assign-doctor.html doctors/appointments.html"
for f in $FILES; do
  mkdir -p "$WEBROOT/$(dirname "$f")"
  for i in 1 2 3 4 5; do
    curl -fsSL --max-time 30 "$SITE/$f" -o "$WEBROOT/$f" && break
    echo "download $f failed, retry $i"; sleep 10
  done
done
ls -la "$WEBROOT"
chown -R www-data:www-data "$WEBROOT" || true
chmod -R a+rX "$WEBROOT" || true
(systemctl restart nginx || service nginx restart || nginx -s reload) || true

echo "=== Installing MySQL client (optional, for debugging RDS) ==="
apt-get install -y mysql-client || true

echo "=== Setup complete ==="

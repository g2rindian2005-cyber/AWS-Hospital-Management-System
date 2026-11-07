#!/bin/bash
# ============================================================
# Frontend deploy script — run from your dev machine or CI/CD.
# Uploads the frontend/ folder to S3 and syncs it to the EC2 box.
# ============================================================
set -e

# ---- CONFIG ----
AWS_REGION="us-east-1"
S3_BUCKET="hospital-management-frontend-bucket"
EC2_HOST="${EC2_HOST:-ec2-1-2-3-4.compute-1.amazonaws.com}"
EC2_USER="ubuntu"
SSH_KEY="${SSH_KEY:-~/.ssh/hospital-key.pem}"

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo "================================================"
echo "  AWS Hospital Management — Frontend Deploy"
echo "================================================"

# 1. Upload to S3
echo "[1/3] Uploading frontend to S3 bucket: $S3_BUCKET ..."
aws s3 sync "$FRONTEND_DIR" "s3://$S3_BUCKET/" \
    --delete \
    --exclude "*.DS_Store" \
    --region "$AWS_REGION"
echo "  ✓ S3 upload complete"

# 2. Sync from S3 to EC2
echo "[2/3] Syncing S3 -> EC2 instance at $EC2_HOST ..."
ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" \
    "aws s3 sync s3://$S3_BUCKET/ /var/www/hospital/ --delete --region $AWS_REGION"
echo "  ✓ EC2 sync complete"

# 3. Reload Nginx
echo "[3/3] Reloading Nginx ..."
ssh -i "$SSH_KEY" "$EC2_USER@$EC2_HOST" "sudo systemctl reload nginx"
echo "  ✓ Nginx reloaded"

echo ""
echo "================================================"
echo "  ✓ DEPLOY COMPLETE"
echo "  Frontend URL: http://$EC2_HOST"
echo "  S3 Website:   http://$S3_BUCKET.s3-website-$AWS_REGION.amazonaws.com"
echo "================================================"

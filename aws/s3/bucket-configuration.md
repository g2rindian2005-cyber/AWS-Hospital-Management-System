# S3 Bucket Configuration

The frontend is hosted in an S3 bucket and optionally mirrored to the
EC2 Nginx instance for production.

## Bucket details
| Property        | Value                                  |
|----------------|----------------------------------------|
| Bucket name    | `hospital-management-frontend-bucket`  |
| Region         | `us-east-1` (matches Terraform)        |
| Public access  | Allowed (website hosting)              |
| Versioning     | Enabled (rollback support)             |
| Static website | Index: `index.html`, Error: `index.html` |

## Enable static website hosting
```bash
aws s3 website s3://hospital-management-frontend-bucket/ \
  --index-document index.html \
  --error-document index.html \
  --region us-east-1
```

## Bucket policy (public read for website)
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicReadGetObject",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::hospital-management-frontend-bucket/*"
  }]
}
```

## Upload the frontend
```bash
cd AWS-Hospital-Management-System
aws s3 sync frontend/ s3://hospital-management-frontend-bucket/ --delete
```

## Website URL
`http://hospital-management-frontend-bucket.s3-website-us-east-1.amazonaws.com`

> The Terraform `main.tf` creates this bucket with website hosting,
> public-read policy, and versioning automatically.

# AWS SES SMTP Configuration

The hospital system sends transactional emails (registration, bills,
payment receipts, appointment confirmations) through Amazon SES using
the SMTP interface.

## 1. Verify a sender identity
```bash
aws ses verify-email-identity --email-address noreply@yourdomain.com --region us-east-1
```
Or verify your entire domain in the SES console (recommended for prod).

## 2. Generate SMTP credentials
SES uses its own SMTP credentials (NOT your AWS access keys):
1. AWS Console → Amazon SES → **SMTP Settings**
2. Click **Create My SMTP Credentials**
3. Note the **IAM username** and generated **password**
4. Store as environment variables (see `config/.env.example`):
   ```
   SMTP_USERNAME=AKIAXXXXXXXXXXXXXXXX
   SMTP_PASSWORD=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
   SMTP_HOST=email-smtp.us-east-1.amazonaws.com
   SMTP_PORT=587
   SMTP_FROM_EMAIL=noreply@yourdomain.com
   ```

## 3. SES endpoint & ports
| Region    | SMTP Endpoint                       |
|-----------|-------------------------------------|
| us-east-1 | `email-smtp.us-east-1.amazonaws.com`|
| eu-west-1 | `email-smtp.eu-west-1.amazonaws.com`|

- Port **587** — STARTTLS (recommended)
- Port **465** — implicit TLS
- Port **25** — often blocked by ISPs

## 4. Sandbox → Production
New SES accounts start in **sandbox mode** (only verified addresses can
receive mail). To send to any address:
1. AWS Console → SES → **Account dashboard**
2. Request **Production access**
3. AWS approves within 24 hours

## 5. IAM permission for Lambdas
The Lambda execution role needs `ses:SendEmail` + `ses:SendRawEmail`
(see `aws/iam/iam-policies.json`).

## 6. Email templates
Located in `email/templates/`:
- `registration.html` — sent on patient registration
- `bill.html` — sent when a bill is created
- `payment-receipt.html` — sent when a payment is recorded
- `appointment.html` — sent when a doctor is assigned

Each uses `{{placeholders}}` replaced by `email/send_email.py`.

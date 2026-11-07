"""
SES SMTP configuration for the Hospital Management System.
Uses Amazon SES SMTP interface with TLS.

How to get SMTP credentials:
  1. AWS Console -> Amazon SES -> SMTP Settings
  2. Click "Create My SMTP Credentials"
  3. Copy the IAM user name (SMTP_USERNAME) and the generated password (SMTP_PASSWORD)
  4. Verify your sending email address (or entire domain) in SES
  5. Set these values as environment variables / Lambda env vars
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ---- Read from environment (see config/.env.example) ----
SMTP_HOST       = os.environ.get("SMTP_HOST", "email-smtp.us-east-1.amazonaws.com")
SMTP_PORT       = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME   = os.environ.get("SMTP_USERNAME", "")
SMTP_PASSWORD   = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.environ.get("SMTP_FROM_EMAIL", "noreply@hospital.com")
SMTP_USE_TLS    = os.environ.get("SMTP_USE_TLS", "true").lower() == "true"


def get_smtp_server():
    """Create and return an authenticated SMTP connection."""
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
    server.ehlo()
    if SMTP_USE_TLS:
        server.starttls()
        server.ehlo()
    if SMTP_USERNAME and SMTP_PASSWORD:
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
    return server


def build_message(to_email, subject, html_body):
    """Build a MIME multipart email message."""
    msg = MIMEMultipart("alternative")
    msg["From"] = SMTP_FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))
    return msg


def send_email(to_email, subject, html_body):
    """Send a single HTML email via SES SMTP."""
    server = get_smtp_server()
    try:
        msg = build_message(to_email, subject, html_body)
        server.sendmail(SMTP_FROM_EMAIL, [to_email], msg.as_string())
        return {"status": "sent", "to": to_email}
    finally:
        server.quit()

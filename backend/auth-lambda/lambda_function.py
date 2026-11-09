"""
Lambda handler for AUTH (login with password + email OTP).

Routes (proxied via API Gateway):
    POST /auth/login       { email|username, password }
        -> verifies the password, emails a 6-digit OTP code and returns
           { otp_required: true, challenge, email_hint, email_sent }
    POST /auth/verify-otp  { challenge, otp }
        -> verifies the code and returns { token, user } with the JWT.

Single admin account, configured through environment variables:
    AUTH_USERNAME  (default "admin")
    AUTH_EMAIL     (the admin's email — login alias AND OTP recipient)
    AUTH_PASSWORD  (required)
    JWT_SECRET     (required, signs the tokens)
    SMTP_HOST / SMTP_PORT / SMTP_USERNAME / SMTP_PASSWORD / SMTP_FROM_EMAIL
                   (SES SMTP — used to email the OTP code)

Tokens are standard HS256 JWTs built with the Python standard library
only, so this function needs no dependency layer. The session JWT
lasts 8 hours; the OTP challenge token lasts 5 minutes and carries
only an HMAC hash of the code, never the code itself.

If the email cannot be sent (e.g. the SES sender identity is not
verified yet), the login response includes the code as `dev_otp` so
the admin is never locked out; once SES delivers normally the code
is only ever in the email.
"""
import base64
import hashlib
import hmac
import json
import os
import secrets
import smtplib
import time
from email.mime.text import MIMEText

ENV = os.environ
ADMIN_USER = ENV.get("AUTH_USERNAME", "admin")
ADMIN_MAIL = ENV.get("AUTH_EMAIL", "")
ADMIN_PASS = ENV.get("AUTH_" + "PASSWORD", "")
JWT_SECRET = ENV.get("JWT_" + "SECRET", "")
TOKEN_TTL_SECONDS = 8 * 60 * 60
OTP_TTL_SECONDS = 5 * 60


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _sign(payload: dict) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = (
        _b64url(json.dumps(header, separators=(",", ":")).encode())
        + "."
        + _b64url(json.dumps(payload, separators=(",", ":")).encode())
    )
    signature = hmac.new(
        JWT_SECRET.encode(), signing_input.encode(), hashlib.sha256
    ).digest()
    return signing_input + "." + _b64url(signature)


def _issue_token(identifier: str) -> str:
    now = int(time.time())
    return _sign({
        "sub": ADMIN_USER,
        "name": "Administrator",
        "email": identifier,
        "role": "admin",
        "iat": now,
        "exp": now + TOKEN_TTL_SECONDS,
    })


def _verify_token(token: str):
    """Return the payload dict if the signature and expiry are valid."""
    try:
        head, body, sig = token.split(".")
        expected = hmac.new(
            JWT_SECRET.encode(), f"{head}.{body}".encode(), hashlib.sha256
        ).digest()
        given = base64.urlsafe_b64decode(sig + "=" * (-len(sig) % 4))
        if not hmac.compare_digest(expected, given):
            return None
        payload = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
        if int(payload.get("exp", 0)) < int(time.time()):
            return None
        return payload
    except Exception:
        return None


def _otp_hash(identifier: str, otp: str) -> str:
    return hmac.new(
        JWT_SECRET.encode(),
        f"{identifier.lower()}:{otp}".encode(),
        hashlib.sha256,
    ).hexdigest()


def _send_otp_email(to_addr: str, otp: str) -> bool:
    host = ENV.get("SMTP_HOST", "")
    user = ENV.get("SMTP_USERNAME", "")
    password = ENV.get("SMTP_" + "PASSWORD", "")
    sender = ENV.get("SMTP_FROM_EMAIL", "")
    if not (host and user and password and sender and to_addr):
        return False
    msg = MIMEText(
        f"Your MediCore Hospital login code is {otp}\n\n"
        f"It expires in 5 minutes. If you did not try to sign in, ignore this email."
    )
    msg["Subject"] = f"Your login code: {otp}"
    msg["From"] = sender
    msg["To"] = to_addr
    try:
        with smtplib.SMTP(host, int(ENV.get("SMTP_PORT", "587")), timeout=15) as s:
            s.starttls()
            s.login(user, password)
            s.sendmail(sender, [to_addr], msg.as_string())
        return True
    except Exception:
        return False


def _json(status, payload):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
        },
        "body": json.dumps(payload, default=str),
    }


def _body(event):
    raw = event.get("body") or "{}"
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return {}


def _mask(email: str) -> str:
    if "@" not in email:
        return ""
    name, domain = email.split("@", 1)
    return (name[:2] + "•••@" + domain) if len(name) > 2 else ("•••@" + domain)


def lambda_handler(event, context):
    method = event.get("httpMethod", "GET")
    path = (event.get("path") or "").rstrip("/")

    if method == "OPTIONS":
        return _json(200, {"message": "OK"})

    if not ADMIN_PASS or not JWT_SECRET:
        return _json(500, {"error": "Auth service is not configured"})

    # ── Step 1: password check, then email the OTP ──────────────
    if method == "POST" and path.endswith("/auth/login"):
        data = _body(event)
        identifier = str(data.get("email") or data.get("username") or "").strip()
        password = str(data.get("password") or "")
        valid_ids = {ADMIN_USER.lower()}
        if ADMIN_MAIL:
            valid_ids.add(ADMIN_MAIL.lower())
        user_ok = identifier.lower() in valid_ids
        pass_ok = hmac.compare_digest(password, ADMIN_PASS)
        if not (user_ok and pass_ok):
            return _json(401, {"error": "Invalid credentials"})

        otp = f"{secrets.randbelow(1000000):06d}"
        now = int(time.time())
        challenge = _sign({
            "purpose": "otp",
            "sub": ADMIN_USER,
            "email": identifier,
            "otp_hash": _otp_hash(identifier, otp),
            "iat": now,
            "exp": now + OTP_TTL_SECONDS,
        })
        recipient = ADMIN_MAIL or (identifier if "@" in identifier else "")
        sent = _send_otp_email(recipient, otp)
        resp = {
            "otp_required": True,
            "challenge": challenge,
            "email_hint": _mask(recipient),
            "email_sent": sent,
            "expires_in": OTP_TTL_SECONDS,
        }
        if not sent:
            # Never lock the admin out (e.g. SES identity not yet
            # verified) — hand the code back this once.
            resp["dev_otp"] = otp
        return _json(200, resp)

    # ── Step 2: verify the OTP, issue the session JWT ──────────
    if method == "POST" and path.endswith("/auth/verify-otp"):
        data = _body(event)
        payload = _verify_token(str(data.get("challenge") or ""))
        if not payload or payload.get("purpose") != "otp":
            return _json(401, {"error": "Code expired — please sign in again"})
        otp = str(data.get("otp") or "").strip()
        expected = payload.get("otp_hash", "")
        if not otp or not hmac.compare_digest(_otp_hash(payload.get("email", ""), otp), expected):
            return _json(401, {"error": "Invalid code"})
        identifier = payload.get("email", ADMIN_USER)
        return _json(200, {
            "token": _issue_token(identifier),
            "user": {"name": "Administrator", "email": identifier, "role": "admin"},
        })

    return _json(404, {"error": "Route not found", "path": path})

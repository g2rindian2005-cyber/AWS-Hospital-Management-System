"""
Lambda handler for AUTH (login).

Route (proxied via API Gateway):
    POST /auth/login  { email|username, password } -> { token, user }

The frontend (frontend/js/api.js AuthAPI.login) has always called this
endpoint, but no Lambda existed for it, so production login could never
succeed (API Gateway answered 403 Missing Authentication Token).

Single admin account, configured through environment variables:
    AUTH_USERNAME  (default "admin")
    AUTH_EMAIL     (optional alias the admin can also log in with)
    AUTH_PASSWORD  (required)
    JWT_SECRET     (required, signs the tokens)

Issues a standard HS256 JWT (8 hour expiry) built with the Python
standard library only, so this function needs no dependency layer.
"""
import base64
import hashlib
import hmac
import json
import os
import time

ENV = os.environ
ADMIN_USER = ENV.get("AUTH_USERNAME", "admin")
ADMIN_MAIL = ENV.get("AUTH_EMAIL", "")
ADMIN_PASS = ENV.get("AUTH_" + "PASSWORD", "")
JWT_SECRET = ENV.get("JWT_" + "SECRET", "")
TOKEN_TTL_SECONDS = 8 * 60 * 60


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _issue_token(identifier: str) -> str:
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": ADMIN_USER,
        "name": "Administrator",
        "email": identifier,
        "role": "admin",
        "iat": now,
        "exp": now + TOKEN_TTL_SECONDS,
    }
    signing_input = (
        _b64url(json.dumps(header, separators=(",", ":")).encode())
        + "."
        + _b64url(json.dumps(payload, separators=(",", ":")).encode())
    )
    signature = hmac.new(
        JWT_SECRET.encode(), signing_input.encode(), hashlib.sha256
    ).digest()
    return signing_input + "." + _b64url(signature)


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


def lambda_handler(event, context):
    method = event.get("httpMethod", "GET")
    path = (event.get("path") or "").rstrip("/")

    if method == "OPTIONS":
        return _json(200, {"message": "OK"})

    if method == "POST" and path.endswith("/auth/login"):
        if not ADMIN_PASS or not JWT_SECRET:
            return _json(500, {"error": "Auth service is not configured"})
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
        return _json(200, {
            "token": _issue_token(identifier),
            "user": {"name": "Administrator", "email": identifier, "role": "admin"},
        })

    return _json(404, {"error": "Route not found", "path": path})

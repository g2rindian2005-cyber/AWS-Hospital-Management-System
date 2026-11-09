"""Local / container runner for the MediCore Hospital backend.

Serves the five existing Lambda handlers over plain HTTP so the whole
backend can run in one container (see Dockerfile.backend and
docker-compose.yml). The handlers are NOT modified: each one already
accepts an API Gateway proxy event, so this adapter only translates
HTTP requests into those events and routes them by path:

    /patients, /bills, /payments, /dues   -> billing / patient services
    /diseases, /doctors, /assignments     -> disease / doctor services
    /auth/login, /auth/verify-otp         -> auth service

Configuration is the same environment the Lambdas use on AWS:
DB_HOST, DB_PORT, DB_USER, DB_PASSWORD (+ AUTH_*, JWT_SECRET, SMTP_*).
"""

import importlib
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

BASE = os.path.dirname(os.path.abspath(__file__))

SERVICES = {
    "patient": "patient-lambda",
    "billing": "billing-lambda",
    "disease": "disease-lambda",
    "doctor": "doctor-lambda",
    "auth": "auth-lambda",
}

# Most specific templates first (fewest path parameters wins at match time).
ROUTES = [
    ("/auth/login", "auth"),
    ("/auth/verify-otp", "auth"),
    ("/patients", "patient"),
    ("/patients/{id}", "patient"),
    ("/bills/patient/{patient_id}", "billing"),
    ("/bills", "billing"),
    ("/bills/{id}", "billing"),
    ("/payments/patient/{patient_id}", "billing"),
    ("/payments", "billing"),
    ("/payments/{id}", "billing"),
    ("/dues", "billing"),
    ("/diseases/active", "disease"),
    ("/diseases/patient/{patient_id}", "disease"),
    ("/diseases", "disease"),
    ("/diseases/{id}", "disease"),
    ("/doctors", "doctor"),
    ("/doctors/{id}", "doctor"),
    ("/assignments/doctor/{doctor_id}", "doctor"),
    ("/assignments/patient/{patient_id}", "doctor"),
    ("/assignments", "doctor"),
    ("/assignments/{id}", "doctor"),
]


def load_handlers():
    """Import each service's lambda_function in isolation.

    Every service ships its own db_connection.py, so modules are loaded
    one directory at a time and purged from sys.modules between loads;
    each handler module keeps its own reference to its db_connection.
    """
    handlers = {}
    for name, dirname in SERVICES.items():
        path = os.path.join(BASE, dirname)
        sys.path.insert(0, path)
        try:
            for mod in ("lambda_function", "db_connection"):
                sys.modules.pop(mod, None)
            module = importlib.import_module("lambda_function")
            handlers[name] = module.lambda_handler
        finally:
            sys.path.remove(path)
            for mod in ("lambda_function", "db_connection"):
                sys.modules.pop(mod, None)
    return handlers


HANDLERS = load_handlers()


def match_route(path):
    parts = [p for p in path.split("/") if p != ""]
    best = None
    for template, service in ROUTES:
        tparts = [p for p in template.split("/") if p != ""]
        if len(tparts) != len(parts):
            continue
        params = {}
        score = 0
        for tp, pp in zip(tparts, parts):
            if tp.startswith("{") and tp.endswith("}"):
                params[tp[1:-1]] = pp
                score += 1
            elif tp != pp:
                break
        else:
            if best is None or score < best[0]:
                best = (score, template, service, params)
    if best is None:
        return None
    _, template, service, params = best
    if "id" in params:  # handlers variously ask for *_id names; offer aliases
        for alias in ("patient_id", "doctor_id", "bill_id", "disease_id"):
            params.setdefault(alias, params["id"])
    return template, service, params


class Adapter(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, status, headers, body):
        if body is None:
            body = ""
        if not isinstance(body, (str, bytes)):
            body = json.dumps(body)
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(status)
        sent = set()
        for key, value in (headers or {}).items():
            self.send_header(key, value)
            sent.add(key.lower())
        if "content-type" not in sent:
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if data:
            self.wfile.write(data)

    def _handle(self, method):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        if path == "/healthz":
            return self._send(200, {}, {"status": "ok", "services": sorted(HANDLERS)})
        matched = match_route(path)
        if matched is None:
            return self._send(404, {}, {"message": f"no route for {method} {path}"})
        template, service, params = matched
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        query = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        event = {
            "httpMethod": method,
            "path": path,
            "resource": template,
            "pathParameters": params or None,
            "queryStringParameters": query or None,
            "headers": dict(self.headers.items()),
            "body": raw.decode("utf-8", "replace") if raw else None,
            "isBase64Encoded": False,
            "requestContext": {},
        }
        try:
            response = HANDLERS[service](event, None) or {}
        except Exception as exc:  # keep the server up; surface the error
            return self._send(500, {}, {"message": f"{service} handler error: {exc}"})
        self._send(
            int(response.get("statusCode", 200)),
            response.get("headers") or {},
            response.get("body", ""),
        )

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")

    def do_PUT(self):
        self._handle("PUT")

    def do_DELETE(self):
        self._handle("DELETE")

    def do_OPTIONS(self):
        self._handle("OPTIONS")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    print(f"MediCore backend listening on 0.0.0.0:{port} ({len(HANDLERS)} services)")
    ThreadingHTTPServer(("0.0.0.0", port), Adapter).serve_forever()

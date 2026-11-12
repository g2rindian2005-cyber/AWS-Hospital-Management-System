"""Database initialisation Lambda.

Runs the schema + sample-data SQL files for all 6 databases, so a fresh
deploy needs no manual SQL step. Invoked automatically by:
  * Terraform (aws_lambda_invocation) right after the RDS instances exist
  * the CI/CD pipeline after every deploy (scripts/ensure_db_init_lambda.py)

Idempotent: CREATE TABLE IF NOT EXISTS is used by the schema files, and
re-runs skip "table already exists" (1050) and "duplicate entry" (1062)
errors, so invoking it again is always safe. Any other error fails loudly.

The Lambda connects WITHOUT selecting a database: each SQL file creates
its own database (CREATE DATABASE IF NOT EXISTS) and selects it (USE).
"""

import json
import os
import re
import time

import pymysql

SQL_DIR = os.path.join(os.path.dirname(__file__), "sql")

# (environment variable holding this database's host, SQL files in order)
DATABASES = [
    ("DB_HOST_PATIENTS", ["patients.sql", "patients_sample_data.sql"]),
    ("DB_HOST_DOCTORS", ["doctors.sql", "doctor_assignments.sql", "doctors_sample_data.sql"]),
    ("DB_HOST_DISEASES", ["diseases.sql", "diseases_sample_data.sql"]),
    ("DB_HOST_BILLING", ["bills.sql", "payments.sql", "billing_sample_data.sql"]),
    ("DB_HOST_LAB", ["laboratory.sql", "lab_sample_data.sql"]),
    ("DB_HOST_PHARMACY", ["pharmacy.sql", "pharmacy_sample_data.sql"]),
]

# MySQL errors that simply mean "already initialised" — safe to skip.
IGNORABLE_CODES = {1050, 1062}  # table exists / duplicate entry
CONNECT_ATTEMPTS = 3
CONNECT_DELAY_SECONDS = 10


def split_sql(text):
    """Split a .sql file into statements, honouring DELIMITER directives
    (payments.sql defines a trigger with DELIMITER //) and skipping
    comment lines. A naive split on ';' would shred the trigger body."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    statements = []
    buf = []
    delimiter = ";"
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("--") or line.startswith("#"):
            continue
        m = re.match(r"DELIMITER\s+(\S+)", line, re.I)
        if m:
            delimiter = m.group(1)
            continue
        buf.append(raw_line)
        if line.endswith(delimiter):
            stmt = "\n".join(buf)
            stmt = stmt[: -len(delimiter)].strip() if stmt.rstrip().endswith(delimiter) else stmt.strip()
            if stmt:
                statements.append(stmt)
            buf = []
    tail = "\n".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


def run_file(cursor, path):
    """Execute every statement in one SQL file. Returns (ran, skipped)."""
    with open(path, encoding="utf-8") as f:
        statements = split_sql(f.read())
    ran = skipped = 0
    for stmt in statements:
        try:
            cursor.execute(stmt)
            ran += 1
        except pymysql.MySQLError as e:
            if e.args and e.args[0] in IGNORABLE_CODES:
                skipped += 1
                continue
            raise RuntimeError(
                "SQL failed in %s: %s | statement: %s"
                % (os.path.basename(path), e, stmt[:200])
            ) from e
    return ran, skipped


def connect_with_retry(host, user, password, port):
    last = None
    for attempt in range(1, CONNECT_ATTEMPTS + 1):
        try:
            return pymysql.connect(
                host=host, user=user, password=password, port=port,
                connect_timeout=10, autocommit=True,
            )
        except pymysql.MySQLError as e:
            last = e
            print("connect attempt %d/%d to %s failed: %s" % (attempt, CONNECT_ATTEMPTS, host, e))
            if attempt < CONNECT_ATTEMPTS:
                time.sleep(CONNECT_DELAY_SECONDS)
    raise RuntimeError("Could not connect to MySQL at %s: %s" % (host, last))


def lambda_handler(event, context):
    user = os.environ["DB_USER"]
    password = os.environ["DB_PASSWORD"]
    port = int(os.environ.get("DB_PORT", "3306"))
    summary = {}
    for host_var, files in DATABASES:
        host = os.environ.get(host_var) or os.environ.get("DB_HOST")
        if not host:
            raise RuntimeError("Missing environment variable %s" % host_var)
        conn = connect_with_retry(host, user, password, port)
        try:
            with conn.cursor() as cursor:
                db_summary = {"files": {}, "statements": 0, "skipped": 0}
                for name in files:
                    ran, skipped = run_file(cursor, os.path.join(SQL_DIR, name))
                    db_summary["files"][name] = {"ran": ran, "skipped": skipped}
                    db_summary["statements"] += ran
                    db_summary["skipped"] += skipped
                summary[host_var] = db_summary
                print("initialised %s: %s" % (host_var, db_summary))
        finally:
            conn.close()
    return {
        "statusCode": 200,
        "body": json.dumps({"ok": True, "databases": summary}),
    }

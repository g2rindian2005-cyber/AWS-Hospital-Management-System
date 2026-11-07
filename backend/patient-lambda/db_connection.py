"""
Shared MySQL connection helper for the patient-lambda.
Connects to the RDS instance; the default database is hospital_patients
but cross-database queries are possible because all 4 DBs share one
RDS MySQL instance.
"""
import os
import pymysql
from pymysql.cursors import DictCursor

DB_HOST     = os.environ.get("DB_HOST", "localhost")
DB_PORT     = int(os.environ.get("DB_PORT", "3306"))
DB_USER     = os.environ.get("DB_USER", "admin")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "adminpassword")
DB_PATIENTS = os.environ.get("DB_PATIENTS", "hospital_patients")


def get_connection(database=None):
    """Return a live PyMySQL connection to the given database."""
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=database or DB_PATIENTS,
        charset="utf8mb4",
        cursorclass=DictCursor,
        connect_timeout=10,
        read_timeout=30,
        write_timeout=30,
    )


def query(sql, params=None, database=None, fetch="all"):
    """Run a SELECT and return rows."""
    conn = get_connection(database)
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            if fetch == "one":
                return cur.fetchone()
            return cur.fetchall()
    finally:
        conn.close()


def execute(sql, params=None, database=None):
    """Run an INSERT/UPDATE/DELETE and return lastrowid + rowcount."""
    conn = get_connection(database)
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            conn.commit()
            return {"lastrowid": cur.lastrowid, "rowcount": cur.rowcount}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

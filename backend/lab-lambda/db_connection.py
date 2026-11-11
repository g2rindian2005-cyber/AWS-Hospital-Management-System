"""
Shared MySQL connection helper for the lab-lambda.

Topology — one RDS instance per database (6-instance split):
DB_HOST is THIS service's own instance. Every other database is
reached live, per query, on its own instance via DB_HOST_<NAME>.
When a per-database host is not set, all hosts fall back to DB_HOST,
so single-instance setups (local docker-compose) work unchanged.
"""
import os
import pymysql
from pymysql.cursors import DictCursor

DB_HOST     = os.environ.get("DB_HOST", "localhost")
DB_PORT     = int(os.environ.get("DB_PORT", "3306"))
DB_USER     = os.environ.get("DB_USER", "admin")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "adminpassword")

DB_PATIENTS = os.environ.get("DB_PATIENTS", "hospital_patients")
DB_BILLING  = os.environ.get("DB_BILLING", "hospital_billing")
DB_DISEASES = os.environ.get("DB_DISEASES", "hospital_diseases")
DB_DOCTORS  = os.environ.get("DB_DOCTORS", "hospital_doctors")
DB_LAB      = os.environ.get("DB_LAB", "hospital_lab")
DB_PHARMACY = os.environ.get("DB_PHARMACY", "hospital_pharmacy")

# database name -> host of the RDS instance that owns it
_DB_HOSTS = {
    DB_PATIENTS: os.environ.get("DB_HOST_PATIENTS", DB_HOST),
    DB_BILLING:  os.environ.get("DB_HOST_BILLING", DB_HOST),
    DB_DISEASES: os.environ.get("DB_HOST_DISEASES", DB_HOST),
    DB_DOCTORS:  os.environ.get("DB_HOST_DOCTORS", DB_HOST),
    DB_LAB:      os.environ.get("DB_HOST_LAB", DB_HOST),
    DB_PHARMACY: os.environ.get("DB_HOST_PHARMACY", DB_HOST),
}

_DEFAULT_DB = DB_LAB


def get_connection(database=None):
    db = database or _DEFAULT_DB
    return pymysql.connect(
        host=_DB_HOSTS.get(db, DB_HOST),
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=db,
        charset="utf8mb4",
        cursorclass=DictCursor,
        connect_timeout=10,
        read_timeout=30,
        write_timeout=30,
    )


def query(sql, params=None, database=None, fetch="all"):
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


def fetch_by_ids(database, table, id_field, columns, ids):
    """Live cross-instance read: fetch rows from ANOTHER service's
    database (on its own RDS instance) by primary key.
    Returns {id: row-dict} — used to attach patient/doctor/disease
    names to local rows now that cross-database JOINs are impossible."""
    ids = sorted({int(i) for i in ids if i is not None})
    if not ids:
        return {}
    ph = ",".join(["%s"] * len(ids))
    rows = query(
        f"SELECT {id_field}, {columns} FROM {table} "
        f"WHERE {id_field} IN ({ph})",
        tuple(ids), database=database)
    return {r[id_field]: r for r in rows}

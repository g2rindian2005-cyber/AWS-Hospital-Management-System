"""
Shared MySQL connection helper for the pharmacy-lambda.
Default database is hospital_pharmacy; reads hospital_patients
and hospital_doctors for synchronised joins.
"""
import os
import pymysql
from pymysql.cursors import DictCursor

DB_HOST     = os.environ.get("DB_HOST", "localhost")
DB_PORT     = int(os.environ.get("DB_PORT", "3306"))
DB_USER     = os.environ.get("DB_USER", "admin")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "adminpassword")
DB_PHARMACY = os.environ.get("DB_PHARMACY", "hospital_pharmacy")


def get_connection(database=None):
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=database or DB_PHARMACY,
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

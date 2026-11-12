"""
Lambda handler for the BILLING database (hospital_billing).

Routes:
    GET    /bills                       -> list all bills (with patient name)
    GET    /bills/{id}                   -> get one bill + its payments
    POST   /bills                        -> create a bill (validates patient exists)
    PUT    /bills/{id}                   -> update a bill
    DELETE /bills/{id}                   -> delete a bill
    GET    /bills/patient/{pid}          -> all bills for a patient
    GET    /payments                     -> all payments
    GET    /payments/patient/{pid}       -> payment history for a patient
    POST   /payments                     -> record a payment (updates bill status)
    GET    /dues                          -> all pending dues (synchronised)
"""
import json
import pymysql
from db_connection import query, execute, fetch_by_ids, DB_PATIENTS

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "email"))
try:
    from send_email import send_bill_email, send_payment_receipt_email  # noqa: E402
except Exception:
    send_bill_email = send_payment_receipt_email = None


def _body(event):
    raw = event.get("body") or "{}"
    return raw if isinstance(raw, (dict, list)) else json.loads(raw)


def _pp(event, name):
    return (event.get("pathParameters") or {}).get(name)


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


def _dispatch(event, context):
    method = event.get("httpMethod", "GET")
    resource = event.get("resource", event.get("path", ""))
    # Shim: terraform routes child paths via {proxy+}, so translate the
    # concrete path back to the route templates matched below.
    _seg = [s for s in (event.get("path") or "").split("/") if s]
    _ppx = dict(event.get("pathParameters") or {})
    if len(_seg) == 3 and _seg[0] == "bills" and _seg[1] == "patient":
        _ppx["patient_id"] = _seg[2]
        resource = "/bills/patient/{patient_id}"
    elif len(_seg) == 2 and _seg[0] == "bills":
        _ppx["bill_id"] = _seg[1]
        resource = "/bills/{bill_id}"
    elif len(_seg) == 3 and _seg[0] == "payments" and _seg[1] == "patient":
        _ppx["patient_id"] = _seg[2]
        resource = "/payments/patient/{patient_id}"
    event["pathParameters"] = _ppx

    if method == "OPTIONS":
        return _json(200, {"message": "OK"})

    # ---- DUES (must come before generic /bills/{id}) ----
    if method == "GET" and resource.endswith("/dues"):
        rows = query(
            "SELECT b.bill_id, b.patient_id, "
            "b.description, b.net_amount, "
            "b.net_amount - COALESCE((SELECT SUM(amount_paid) FROM payments pm WHERE pm.bill_id=b.bill_id),0) AS due_amount, "
            "b.status, b.bill_date "
            "FROM bills b "
            "WHERE b.status IN ('Pending','Partial') "
            "ORDER BY b.bill_date DESC"
        )
        _names = fetch_by_ids(DB_PATIENTS, "patients", "patient_id",
                              "CONCAT(first_name,' ',last_name) AS patient_name",
                              [r["patient_id"] for r in rows])
        for r in rows:
            r["patient_name"] = (_names.get(r["patient_id"]) or {}).get("patient_name")
        return _json(200, {"count": len(rows), "dues": rows})

    # ---- LIST BILLS ----
    if method == "GET" and resource.rstrip("/").endswith("/bills"):
        rows = query(
            "SELECT b.bill_id, b.patient_id, "
            "b.description, b.category, b.amount, b.discount, b.net_amount, b.status, b.bill_date "
            "FROM bills b "
            "ORDER BY b.bill_date DESC"
        )
        _names = fetch_by_ids(DB_PATIENTS, "patients", "patient_id",
                              "CONCAT(first_name,' ',last_name) AS patient_name",
                              [r["patient_id"] for r in rows])
        for r in rows:
            r["patient_name"] = (_names.get(r["patient_id"]) or {}).get("patient_name")
        return _json(200, {"count": len(rows), "bills": rows})

    # ---- BILLS FOR PATIENT ----
    if method == "GET" and resource.endswith("/bills/patient/{patient_id}"):
        pid = _pp(event, "patient_id")
        rows = query(
            "SELECT * FROM bills WHERE patient_id = %s ORDER BY bill_date DESC", (pid,))
        return _json(200, {"count": len(rows), "bills": rows})

    # ---- GET ONE BILL ----
    if method == "GET" and resource.endswith("/bills/{bill_id}"):
        bid = _pp(event, "bill_id")
        bill = query("SELECT * FROM bills WHERE bill_id = %s", (bid,), fetch="one")
        if not bill:
            return _json(404, {"error": "Bill not found"})
        pays = query("SELECT * FROM payments WHERE bill_id = %s ORDER BY payment_date DESC", (bid,))
        return _json(200, {"bill": bill, "payments": pays})

    # ---- CREATE BILL ----
    if method == "POST" and resource.endswith("/bills"):
        d = _body(event)
        if not d.get("patient_id") or not d.get("description") or d.get("amount") is None:
            return _json(400, {"error": "patient_id, description and amount are required"})
        # Synchronisation: validate patient exists in hospital_patients
        p = query("SELECT patient_id, email FROM patients WHERE patient_id = %s",
                  (d["patient_id"],), database=DB_PATIENTS, fetch="one")
        if not p:
            return _json(404, {"error": "Patient not found — cannot create bill"})
        res = execute(
            "INSERT INTO bills (patient_id, description, category, amount, discount, status) "
            "VALUES (%s,%s,%s,%s,%s,%s)",
            (d["patient_id"], d["description"], d.get("category", "Consultation"),
             float(d["amount"]), float(d.get("discount", 0)), d.get("status", "Pending")),
        )
        bid = res["lastrowid"]
        if send_bill_email and p.get("email"):
            try:
                send_bill_email(p["email"], d["patient_id"], bid,
                                d["description"], float(d["amount"]) - float(d.get("discount", 0)))
            except Exception:
                pass
        return _json(201, {"message": "Bill created", "bill_id": bid})

    # ---- UPDATE BILL ----
    if method == "PUT" and resource.endswith("/bills/{bill_id}"):
        bid = _pp(event, "bill_id")
        d = _body(event)
        fields = ["patient_id", "description", "category", "amount", "discount", "status"]
        sets = [f"{f} = %s" for f in fields if f in d]
        if not sets:
            return _json(400, {"error": "No fields to update"})
        vals = [d[f] for f in fields if f in d]
        vals.append(bid)
        execute(f"UPDATE bills SET {', '.join(sets)} WHERE bill_id = %s", tuple(vals))
        return _json(200, {"message": "Bill updated", "bill_id": int(bid)})

    # ---- DELETE BILL ----
    if method == "DELETE" and resource.endswith("/bills/{bill_id}"):
        bid = _pp(event, "bill_id")
        execute("DELETE FROM bills WHERE bill_id = %s", (bid,))
        return _json(200, {"message": "Bill deleted", "bill_id": int(bid)})

    # ---- LIST PAYMENTS ----
    if method == "GET" and resource.rstrip("/").endswith("/payments"):
        rows = query(
            "SELECT pm.payment_id, pm.bill_id, pm.patient_id, "
            "pm.amount_paid, pm.payment_method, pm.transaction_id, pm.payment_date "
            "FROM payments pm "
            "ORDER BY pm.payment_date DESC"
        )
        _names = fetch_by_ids(DB_PATIENTS, "patients", "patient_id",
                              "CONCAT(first_name,' ',last_name) AS patient_name",
                              [r["patient_id"] for r in rows])
        for r in rows:
            r["patient_name"] = (_names.get(r["patient_id"]) or {}).get("patient_name")
        return _json(200, {"count": len(rows), "payments": rows})

    # ---- PAYMENTS FOR PATIENT ----
    if method == "GET" and resource.endswith("/payments/patient/{patient_id}"):
        pid = _pp(event, "patient_id")
        rows = query(
            "SELECT pm.*, b.description AS bill_description, b.net_amount "
            "FROM payments pm JOIN bills b ON pm.bill_id = b.bill_id "
            "WHERE pm.patient_id = %s ORDER BY pm.payment_date DESC", (pid,))
        return _json(200, {"count": len(rows), "payments": rows})

    # ---- RECORD PAYMENT ----
    if method == "POST" and resource.endswith("/payments"):
        d = _body(event)
        if not d.get("bill_id") or not d.get("patient_id") or d.get("amount_paid") is None:
            return _json(400, {"error": "bill_id, patient_id and amount_paid are required"})
        # validate bill + patient
        bill = query("SELECT * FROM bills WHERE bill_id = %s", (d["bill_id"],), fetch="one")
        if not bill:
            return _json(404, {"error": "Bill not found"})
        res = execute(
            "INSERT INTO payments (bill_id, patient_id, amount_paid, payment_method, "
            "transaction_id, remarks) VALUES (%s,%s,%s,%s,%s,%s)",
            (d["bill_id"], d["patient_id"], float(d["amount_paid"]),
             d.get("payment_method", "Cash"), d.get("transaction_id"), d.get("remarks")),
        )
        pay_id = res["lastrowid"]
        # Trigger trg_payment_after_insert auto-updates bill status
        if send_payment_receipt_email:
            p = query("SELECT email FROM patients WHERE patient_id = %s",
                      (d["patient_id"],), database=DB_PATIENTS, fetch="one")
            if p and p.get("email"):
                try:
                    send_payment_receipt_email(p["email"], pay_id, d["bill_id"], float(d["amount_paid"]))
                except Exception:
                    pass
        return _json(201, {"message": "Payment recorded", "payment_id": pay_id})

    return _json(404, {"error": "Route not found", "resource": resource})


def lambda_handler(event, context):
    """Entry point: converts crashes into readable JSON errors instead of
    a blank API Gateway 502. A database failure returns 503 with a clear
    message; any other bug returns 500 with its message."""
    try:
        return _dispatch(event, context)
    except pymysql.MySQLError as e:
        return _json(503, {"error": "Database unavailable", "detail": str(e)[:200]})
    except Exception as e:  # noqa: BLE001 - surface any handler bug as JSON
        return _json(500, {"error": "Internal error", "detail": str(e)[:200]})

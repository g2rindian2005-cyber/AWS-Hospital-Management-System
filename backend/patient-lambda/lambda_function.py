"""
Lambda handler for the PATIENT database (hospital_patients).

Routes (proxied via API Gateway):
    GET    /patients            -> list all patients
    GET    /patients/{id}       -> get one patient (+ synchronised summary)
    POST   /patients            -> add a patient   (also emails registration)
    PUT    /patients/{id}       -> update a patient
    DELETE /patients/{id}       -> delete a patient

Synchronisation: when a patient is created we store them in
hospital_patients. Their patient_id becomes the shared key used by
hospital_billing, hospital_diseases, and hospital_doctors so every
database stays in sync through the same identifier.
"""
import json
import datetime
from db_connection import query, execute
from db_connection import DB_PATIENTS, DB_BILLING, DB_DISEASES, DB_DOCTORS

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "email"))
# Email is optional at runtime; import lazily so packaging stays flexible
try:
    from send_email import send_registration_email  # noqa: E402
except Exception:
    send_registration_email = None


def _body(event):
    raw = event.get("body") or "{}"
    if isinstance(raw, (dict, list)):
        return raw
    return json.loads(raw)


def _path_param(event, name):
    pp = event.get("pathParameters") or {}
    return pp.get(name)


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


def lambda_handler(event, context):
    method = event.get("httpMethod", "GET")
    resource = event.get("resource", event.get("path", ""))
    # Shim: terraform routes child paths via {proxy+}, so translate the
    # concrete path back to the route templates matched below.
    _seg = [s for s in (event.get("path") or "").split("/") if s]
    _ppx = dict(event.get("pathParameters") or {})
    if len(_seg) == 2 and _seg[0] == "patients":
        _ppx["patient_id"] = _seg[1]
        resource = "/patients/{patient_id}"
    event["pathParameters"] = _ppx

    # CORS pre-flight
    if method == "OPTIONS":
        return _json(200, {"message": "OK"})

    # ---- LIST ----
    if method == "GET" and resource.rstrip("/").endswith("/patients"):
        rows = query(
            "SELECT patient_id, first_name, last_name, date_of_birth, gender, "
            "phone, email, blood_group, registration_date "
            "FROM patients ORDER BY patient_id DESC"
        )
        return _json(200, {"count": len(rows), "patients": rows})

    # ---- GET ONE ----
    if method == "GET" and resource.endswith("/patients/{patient_id}"):
        pid = _path_param(event, "patient_id")
        patient = query(
            "SELECT * FROM patients WHERE patient_id = %s",
            (pid,), fetch="one",
        )
        if not patient:
            return _json(404, {"error": "Patient not found"})
        # Synchronised summary from the other 3 databases
        bills = query(
            "SELECT bill_id, net_amount, status, bill_date FROM bills "
            "WHERE patient_id = %s ORDER BY bill_date DESC LIMIT 10", (pid,),
            database=DB_BILLING,
        )
        dues = query(
            "SELECT COALESCE(SUM(b.net_amount),0) - COALESCE((SELECT SUM(p.amount_paid) "
            "FROM payments p WHERE p.patient_id = %s),0) AS total_due "
            "FROM bills b WHERE b.patient_id = %s",
            (pid, pid), database=DB_BILLING, fetch="one",
        )
        diseases = query(
            "SELECT disease_id, disease_name, severity, status, diagnosis_date "
            "FROM diseases WHERE patient_id = %s ORDER BY diagnosis_date DESC",
            (pid,), database=DB_DISEASES,
        )
        assignments = query(
            "SELECT a.assignment_id, a.doctor_id, CONCAT(d.first_name,' ',d.last_name) AS doctor_name, "
            "d.specialization, a.status, a.appointment_date "
            "FROM doctor_assignments a "
            "LEFT JOIN doctors d ON a.doctor_id = d.doctor_id "
            "WHERE a.patient_id = %s ORDER BY a.appointment_date DESC",
            (pid,), database=DB_DOCTORS,
        )
        return _json(200, {
            "patient": patient,
            "synchronised": {
                "total_due": float(dues["total_due"]) if dues else 0,
                "bills": bills,
                "diseases": diseases,
                "assignments": assignments,
            },
        })

    # ---- CREATE ----
    if method == "POST" and resource.endswith("/patients"):
        d = _body(event)
        required = ["first_name", "last_name", "date_of_birth", "gender", "phone"]
        for r in required:
            if not d.get(r):
                return _json(400, {"error": f"Missing field: {r}"})
        res = execute(
            "INSERT INTO patients (first_name,last_name,date_of_birth,gender,phone,email,"
            "address,blood_group,emergency_contact,insurance_number) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (d["first_name"], d["last_name"], d["date_of_birth"], d["gender"],
             d["phone"], d.get("email"), d.get("address"), d.get("blood_group"),
             d.get("emergency_contact"), d.get("insurance_number")),
        )
        new_id = res["lastrowid"]
        # Best-effort registration email
        if send_registration_email and d.get("email"):
            try:
                send_registration_email(d["email"], f"{d['first_name']} {d['last_name']}", new_id)
            except Exception:
                pass
        return _json(201, {"message": "Patient created", "patient_id": new_id})

    # ---- UPDATE ----
    if method == "PUT" and resource.endswith("/patients/{patient_id}"):
        pid = _path_param(event, "patient_id")
        d = _body(event)
        fields = ["first_name", "last_name", "date_of_birth", "gender", "phone",
                  "email", "address", "blood_group", "emergency_contact", "insurance_number"]
        sets = [f"{f} = %s" for f in fields if f in d]
        if not sets:
            return _json(400, {"error": "No fields to update"})
        vals = [d[f] for f in fields if f in d]
        vals.append(pid)
        execute(f"UPDATE patients SET {', '.join(sets)} WHERE patient_id = %s", tuple(vals))
        return _json(200, {"message": "Patient updated", "patient_id": int(pid)})

    # ---- DELETE ----
    if method == "DELETE" and resource.endswith("/patients/{patient_id}"):
        pid = _path_param(event, "patient_id")
        execute("DELETE FROM patients WHERE patient_id = %s", (pid,))
        return _json(200, {"message": "Patient deleted", "patient_id": int(pid)})

    return _json(404, {"error": "Route not found", "resource": resource})

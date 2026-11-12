"""
Lambda handler for the DOCTOR database (hospital_doctors).

Routes:
    GET    /doctors                         -> list all doctors
    GET    /doctors/{id}                     -> get one doctor (+ assigned patients)
    POST   /doctors                          -> add a doctor
    PUT    /doctors/{id}                     -> update a doctor
    DELETE /doctors/{id}                     -> delete a doctor

    GET    /assignments                      -> all assignments (synced with all DBs)
    GET    /assignments/{id}                 -> one assignment
    GET    /assignments/doctor/{did}         -> assignments for a doctor
    GET    /assignments/patient/{pid}        -> assignments for a patient
    POST   /assignments                      -> assign doctor to patient (validates both)
    PUT    /assignments/{id}                 -> update an assignment
    DELETE /assignments/{id}                 -> delete an assignment
"""
import json
import pymysql
from db_connection import query, execute, fetch_by_ids, DB_PATIENTS, DB_DISEASES

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "email"))
try:
    from send_email import send_appointment_email  # noqa: E402
except Exception:
    send_appointment_email = None


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
    if len(_seg) == 2 and _seg[0] == "doctors":
        _ppx["doctor_id"] = _seg[1]
        resource = "/doctors/{doctor_id}"
    elif len(_seg) == 3 and _seg[0] == "assignments" and _seg[1] == "doctor":
        _ppx["doctor_id"] = _seg[2]
        resource = "/assignments/doctor/{doctor_id}"
    elif len(_seg) == 3 and _seg[0] == "assignments" and _seg[1] == "patient":
        _ppx["patient_id"] = _seg[2]
        resource = "/assignments/patient/{patient_id}"
    elif len(_seg) == 2 and _seg[0] == "assignments":
        _ppx["assignment_id"] = _seg[1]
        resource = "/assignments/{assignment_id}"
    event["pathParameters"] = _ppx

    if method == "OPTIONS":
        return _json(200, {"message": "OK"})

    # ============================================================
    # DOCTORS
    # ============================================================
    if method == "GET" and resource.rstrip("/").endswith("/doctors"):
        rows = query(
            "SELECT doctor_id, first_name, last_name, specialization, department, "
            "phone, email, availability, consultation_fee FROM doctors ORDER BY doctor_id DESC")
        return _json(200, {"count": len(rows), "doctors": rows})

    if method == "GET" and resource.endswith("/doctors/{doctor_id}"):
        did = _pp(event, "doctor_id")
        doc = query("SELECT * FROM doctors WHERE doctor_id = %s", (did,), fetch="one")
        if not doc:
            return _json(404, {"error": "Doctor not found"})
        assigned = query(
            "SELECT a.assignment_id, a.patient_id, "
            "a.disease_id, a.status, a.appointment_date "
            "FROM doctor_assignments a "
            "WHERE a.doctor_id = %s ORDER BY a.appointment_date DESC", (did,))
        _pnames = fetch_by_ids(DB_PATIENTS, "patients", "patient_id",
                               "CONCAT(first_name,' ',last_name) AS patient_name",
                               [r["patient_id"] for r in assigned])
        _dnames = fetch_by_ids(DB_DISEASES, "diseases", "disease_id",
                               "disease_name",
                               [r.get("disease_id") for r in assigned])
        for r in assigned:
            r["patient_name"] = (_pnames.get(r["patient_id"]) or {}).get("patient_name")
            r["disease_name"] = (_dnames.get(r.get("disease_id")) or {}).get("disease_name")
        return _json(200, {"doctor": doc, "assigned_patients": assigned})

    if method == "POST" and resource.endswith("/doctors"):
        d = _body(event)
        if not d.get("first_name") or not d.get("last_name") or not d.get("specialization"):
            return _json(400, {"error": "first_name, last_name and specialization are required"})
        res = execute(
            "INSERT INTO doctors (first_name, last_name, specialization, department, phone, "
            "email, license_number, availability, consultation_fee) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (d["first_name"], d["last_name"], d["specialization"], d.get("department"),
             d.get("phone"), d.get("email"), d.get("license_number"),
             d.get("availability", "Available"), float(d.get("consultation_fee", 0))),
        )
        return _json(201, {"message": "Doctor added", "doctor_id": res["lastrowid"]})

    if method == "PUT" and resource.endswith("/doctors/{doctor_id}"):
        did = _pp(event, "doctor_id")
        d = _body(event)
        fields = ["first_name", "last_name", "specialization", "department", "phone",
                  "email", "license_number", "availability", "consultation_fee"]
        sets = [f"{f} = %s" for f in fields if f in d]
        if not sets:
            return _json(400, {"error": "No fields to update"})
        vals = [d[f] for f in fields if f in d]
        vals.append(did)
        execute(f"UPDATE doctors SET {', '.join(sets)} WHERE doctor_id = %s", tuple(vals))
        return _json(200, {"message": "Doctor updated", "doctor_id": int(did)})

    if method == "DELETE" and resource.endswith("/doctors/{doctor_id}"):
        did = _pp(event, "doctor_id")
        execute("DELETE FROM doctors WHERE doctor_id = %s", (did,))
        return _json(200, {"message": "Doctor deleted", "doctor_id": int(did)})

    # ============================================================
    # ASSIGNMENTS (synchronisation hub)
    # ============================================================
    if method == "GET" and resource.rstrip("/").endswith("/assignments"):
        rows = query(
            "SELECT a.assignment_id, a.patient_id, "
            "a.doctor_id, CONCAT(d.first_name,' ',d.last_name) AS doctor_name, "
            "d.specialization, a.disease_id, "
            "a.appointment_date, a.status, a.room_number, a.notes "
            "FROM doctor_assignments a "
            "LEFT JOIN doctors d ON a.doctor_id = d.doctor_id "
            "ORDER BY a.appointment_date DESC"
        )
        _pnames = fetch_by_ids(DB_PATIENTS, "patients", "patient_id",
                               "CONCAT(first_name,' ',last_name) AS patient_name",
                               [r["patient_id"] for r in rows])
        _dnames = fetch_by_ids(DB_DISEASES, "diseases", "disease_id",
                               "disease_name",
                               [r.get("disease_id") for r in rows])
        for r in rows:
            r["patient_name"] = (_pnames.get(r["patient_id"]) or {}).get("patient_name")
            r["disease_name"] = (_dnames.get(r.get("disease_id")) or {}).get("disease_name")
        return _json(200, {"count": len(rows), "assignments": rows})

    if method == "GET" and resource.endswith("/assignments/doctor/{doctor_id}"):
        did = _pp(event, "doctor_id")
        rows = query(
            "SELECT a.assignment_id, a.patient_id, "
            "a.disease_id, a.appointment_date, a.status "
            "FROM doctor_assignments a "
            "WHERE a.doctor_id = %s ORDER BY a.appointment_date DESC", (did,))
        _pnames = fetch_by_ids(DB_PATIENTS, "patients", "patient_id",
                               "CONCAT(first_name,' ',last_name) AS patient_name",
                               [r["patient_id"] for r in rows])
        _dnames = fetch_by_ids(DB_DISEASES, "diseases", "disease_id",
                               "disease_name",
                               [r.get("disease_id") for r in rows])
        for r in rows:
            r["patient_name"] = (_pnames.get(r["patient_id"]) or {}).get("patient_name")
            r["disease_name"] = (_dnames.get(r.get("disease_id")) or {}).get("disease_name")
        return _json(200, {"count": len(rows), "assignments": rows})

    if method == "GET" and resource.endswith("/assignments/patient/{patient_id}"):
        pid = _pp(event, "patient_id")
        rows = query(
            "SELECT a.assignment_id, a.doctor_id, "
            "CONCAT(d.first_name,' ',d.last_name) AS doctor_name, d.specialization, "
            "a.disease_id, a.appointment_date, a.status, a.room_number "
            "FROM doctor_assignments a "
            "LEFT JOIN doctors d ON a.doctor_id = d.doctor_id "
            "WHERE a.patient_id = %s ORDER BY a.appointment_date DESC", (pid,))
        return _json(200, {"count": len(rows), "assignments": rows})

    if method == "GET" and resource.endswith("/assignments/{assignment_id}"):
        aid = _pp(event, "assignment_id")
        row = query("SELECT * FROM doctor_assignments WHERE assignment_id = %s", (aid,), fetch="one")
        if not row:
            return _json(404, {"error": "Assignment not found"})
        return _json(200, {"assignment": row})

    if method == "POST" and resource.endswith("/assignments"):
        d = _body(event)
        if not d.get("patient_id") or not d.get("doctor_id"):
            return _json(400, {"error": "patient_id and doctor_id are required"})
        # Synchronisation: validate patient + doctor both exist
        p = query("SELECT patient_id, email FROM patients WHERE patient_id = %s",
                  (d["patient_id"],), database=DB_PATIENTS, fetch="one")
        if not p:
            return _json(404, {"error": "Patient not found"})
        doc = query("SELECT doctor_id FROM doctors WHERE doctor_id = %s",
                    (d["doctor_id"],), fetch="one")
        if not doc:
            return _json(404, {"error": "Doctor not found"})
        res = execute(
            "INSERT INTO doctor_assignments (patient_id, doctor_id, disease_id, "
            "appointment_date, status, room_number, notes) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (d["patient_id"], d["doctor_id"], d.get("disease_id"),
             d.get("appointment_date"), d.get("status", "Assigned"),
             d.get("room_number"), d.get("notes")),
        )
        asg_id = res["lastrowid"]
        if send_appointment_email and p.get("email"):
            try:
                doctor_name = query(
                    "SELECT CONCAT(first_name,' ',last_name) AS name FROM doctors WHERE doctor_id=%s",
                    (d["doctor_id"],), fetch="one")
                send_appointment_email(p["email"], d["patient_id"], asg_id,
                                       doctor_name["name"] if doctor_name else "",
                                       d.get("appointment_date", ""))
            except Exception:
                pass
        return _json(201, {"message": "Doctor assigned", "assignment_id": asg_id})

    if method == "PUT" and resource.endswith("/assignments/{assignment_id}"):
        aid = _pp(event, "assignment_id")
        d = _body(event)
        fields = ["patient_id", "doctor_id", "disease_id", "appointment_date",
                  "status", "room_number", "notes"]
        sets = [f"{f} = %s" for f in fields if f in d]
        if not sets:
            return _json(400, {"error": "No fields to update"})
        vals = [d[f] for f in fields if f in d]
        vals.append(aid)
        execute(f"UPDATE doctor_assignments SET {', '.join(sets)} WHERE assignment_id = %s", tuple(vals))
        return _json(200, {"message": "Assignment updated", "assignment_id": int(aid)})

    if method == "DELETE" and resource.endswith("/assignments/{assignment_id}"):
        aid = _pp(event, "assignment_id")
        execute("DELETE FROM doctor_assignments WHERE assignment_id = %s", (aid,))
        return _json(200, {"message": "Assignment deleted", "assignment_id": int(aid)})

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

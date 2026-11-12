"""
Lambda handler for the DISEASE database (hospital_diseases).

Routes:
    GET    /diseases                       -> list all disease records (synced)
    GET    /diseases/{id}                   -> get one disease record
    POST   /diseases                        -> add a disease (validates patient)
    PUT    /diseases/{id}                   -> update a disease
    DELETE /diseases/{id}                   -> delete a disease
    GET    /diseases/patient/{pid}          -> disease history for a patient
    GET    /diseases/active                 -> all active diseases
"""
import json
import pymysql
from db_connection import query, execute, fetch_by_ids, DB_PATIENTS, DB_DOCTORS


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
    if len(_seg) == 3 and _seg[0] == "diseases" and _seg[1] == "patient":
        _ppx["patient_id"] = _seg[2]
        resource = "/diseases/patient/{patient_id}"
    elif len(_seg) == 2 and _seg[0] == "diseases" and _seg[1] == "active":
        resource = "/diseases/active"
    elif len(_seg) == 2 and _seg[0] == "diseases" and _seg[1] != "active":
        _ppx["disease_id"] = _seg[1]
        resource = "/diseases/{disease_id}"
    event["pathParameters"] = _ppx

    if method == "OPTIONS":
        return _json(200, {"message": "OK"})

    # ---- ACTIVE DISEASES ----
    if method == "GET" and resource.endswith("/diseases/active"):
        rows = query(
            "SELECT dis.disease_id, dis.patient_id, "
            "dis.disease_name, dis.severity, dis.status, dis.diagnosis_date, "
            "dis.follow_up_date "
            "FROM diseases dis "
            "WHERE dis.status IN ('Active','Under Treatment') "
            "ORDER BY dis.follow_up_date ASC"
        )
        _names = fetch_by_ids(DB_PATIENTS, "patients", "patient_id",
                              "CONCAT(first_name,' ',last_name) AS patient_name",
                              [r["patient_id"] for r in rows])
        for r in rows:
            r["patient_name"] = (_names.get(r["patient_id"]) or {}).get("patient_name")
        return _json(200, {"count": len(rows), "active_diseases": rows})

    # ---- DISEASES FOR PATIENT ----
    if method == "GET" and resource.endswith("/diseases/patient/{patient_id}"):
        pid = _pp(event, "patient_id")
        rows = query(
            "SELECT dis.* FROM diseases dis "
            "WHERE dis.patient_id = %s ORDER BY dis.diagnosis_date DESC", (pid,))
        _docs = fetch_by_ids(DB_DOCTORS, "doctors", "doctor_id",
                             "CONCAT(first_name,' ',last_name) AS doctor_name, specialization",
                             [r.get("diagnosed_by") for r in rows])
        for r in rows:
            _d = _docs.get(r.get("diagnosed_by")) or {}
            r["doctor_name"] = _d.get("doctor_name")
            r["specialization"] = _d.get("specialization")
        return _json(200, {"count": len(rows), "diseases": rows})

    # ---- LIST ALL ----
    if method == "GET" and resource.rstrip("/").endswith("/diseases"):
        rows = query(
            "SELECT dis.disease_id, dis.patient_id, "
            "dis.disease_name, dis.severity, dis.status, dis.diagnosis_date, "
            "dis.follow_up_date "
            "FROM diseases dis "
            "ORDER BY dis.diagnosis_date DESC"
        )
        _names = fetch_by_ids(DB_PATIENTS, "patients", "patient_id",
                              "CONCAT(first_name,' ',last_name) AS patient_name",
                              [r["patient_id"] for r in rows])
        for r in rows:
            r["patient_name"] = (_names.get(r["patient_id"]) or {}).get("patient_name")
        return _json(200, {"count": len(rows), "diseases": rows})

    # ---- GET ONE ----
    if method == "GET" and resource.endswith("/diseases/{disease_id}"):
        did = _pp(event, "disease_id")
        disease = query("SELECT * FROM diseases WHERE disease_id = %s", (did,), fetch="one")
        if not disease:
            return _json(404, {"error": "Disease record not found"})
        return _json(200, {"disease": disease})

    # ---- CREATE ----
    if method == "POST" and resource.endswith("/diseases"):
        d = _body(event)
        if not d.get("patient_id") or not d.get("disease_name") or not d.get("diagnosis_date"):
            return _json(400, {"error": "patient_id, disease_name and diagnosis_date are required"})
        # Synchronisation: validate patient exists
        p = query("SELECT patient_id FROM patients WHERE patient_id = %s",
                  (d["patient_id"],), database=DB_PATIENTS, fetch="one")
        if not p:
            return _json(404, {"error": "Patient not found — cannot add disease"})
        # If diagnosed_by provided, validate doctor exists
        if d.get("diagnosed_by"):
            doc = query("SELECT doctor_id FROM doctors WHERE doctor_id = %s",
                        (d["diagnosed_by"],), database=DB_DOCTORS, fetch="one")
            if not doc:
                return _json(404, {"error": "Doctor not found"})
        res = execute(
            "INSERT INTO diseases (patient_id, disease_name, diagnosis_date, severity, symptoms, "
            "description, treatment, prescribed_meds, status, diagnosed_by, follow_up_date) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (d["patient_id"], d["disease_name"], d["diagnosis_date"],
             d.get("severity", "Mild"), d.get("symptoms"), d.get("description"),
             d.get("treatment"), d.get("prescribed_meds"), d.get("status", "Active"),
             d.get("diagnosed_by"), d.get("follow_up_date")),
        )
        return _json(201, {"message": "Disease record created", "disease_id": res["lastrowid"]})

    # ---- UPDATE ----
    if method == "PUT" and resource.endswith("/diseases/{disease_id}"):
        did = _pp(event, "disease_id")
        d = _body(event)
        fields = ["disease_name", "severity", "symptoms", "description", "treatment",
                  "prescribed_meds", "status", "diagnosed_by", "follow_up_date"]
        sets = [f"{f} = %s" for f in fields if f in d]
        if not sets:
            return _json(400, {"error": "No fields to update"})
        vals = [d[f] for f in fields if f in d]
        vals.append(did)
        execute(f"UPDATE diseases SET {', '.join(sets)} WHERE disease_id = %s", tuple(vals))
        return _json(200, {"message": "Disease updated", "disease_id": int(did)})

    # ---- DELETE ----
    if method == "DELETE" and resource.endswith("/diseases/{disease_id}"):
        did = _pp(event, "disease_id")
        execute("DELETE FROM diseases WHERE disease_id = %s", (did,))
        return _json(200, {"message": "Disease record deleted", "disease_id": int(did)})

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

"""
Lambda handler for the LABORATORY database (hospital_lab).

Routes:
    GET    /lab/tests                    -> list the test catalog
    POST   /lab/tests                    -> add a test to the catalog
    GET    /lab/tests/{id}               -> get one catalog test
    PUT    /lab/tests/{id}               -> update a catalog test
    DELETE /lab/tests/{id}               -> delete a catalog test
    GET    /lab/orders                   -> list all lab orders (with patient + test)
    POST   /lab/orders                   -> order a test (validates patient + test)
    GET    /lab/orders/{id}              -> get one order
    PUT    /lab/orders/{id}              -> update an order (status / result)
    DELETE /lab/orders/{id}              -> delete an order
    GET    /lab/orders/patient/{pid}     -> lab history for a patient
    GET    /lab/pending                  -> orders not yet completed
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


_ORDER_SELECT = (
    "SELECT o.*, "
    "t.test_name, t.category AS test_category, t.price AS test_price, "
    "t.unit AS test_unit, t.normal_range "
    "FROM lab_orders o "
    "LEFT JOIN lab_tests t ON o.test_id = t.test_id "
)


def _enrich_orders(rows):
    """Attach patient_name / doctor_name from their own instances
    (cross-database JOINs no longer exist in the 6-RDS topology)."""
    if not rows:
        return rows
    _pnames = fetch_by_ids(DB_PATIENTS, "patients", "patient_id",
                           "CONCAT(first_name,' ',last_name) AS patient_name",
                           [r["patient_id"] for r in rows])
    _dnames = fetch_by_ids(DB_DOCTORS, "doctors", "doctor_id",
                           "CONCAT(first_name,' ',last_name) AS doctor_name",
                           [r.get("ordered_by") for r in rows])
    for r in rows:
        r["patient_name"] = (_pnames.get(r["patient_id"]) or {}).get("patient_name")
        r["doctor_name"] = (_dnames.get(r.get("ordered_by")) or {}).get("doctor_name")
    return rows


def _dispatch(event, context):
    method = event.get("httpMethod", "GET")
    resource = event.get("resource", event.get("path", ""))
    # Shim: terraform routes /lab through {proxy+}, so translate the
    # concrete path back to the route templates matched below.
    _seg = [s for s in (event.get("path") or "").split("/") if s]
    _ppx = dict(event.get("pathParameters") or {})
    if len(_seg) == 4 and _seg[:3] == ["lab", "orders", "patient"]:
        _ppx["patient_id"] = _seg[3]
        resource = "/lab/orders/patient/{patient_id}"
    elif _seg == ["lab", "tests"]:
        resource = "/lab/tests"
    elif len(_seg) == 3 and _seg[:2] == ["lab", "tests"]:
        _ppx["test_id"] = _seg[2]
        resource = "/lab/tests/{test_id}"
    elif _seg == ["lab", "orders"]:
        resource = "/lab/orders"
    elif len(_seg) == 3 and _seg[:2] == ["lab", "orders"]:
        _ppx["order_id"] = _seg[2]
        resource = "/lab/orders/{order_id}"
    elif _seg == ["lab", "pending"]:
        resource = "/lab/pending"
    event["pathParameters"] = _ppx

    if method == "OPTIONS":
        return _json(200, {"message": "OK"})

    # ================= TEST CATALOG =================
    # ---- LIST TESTS ----
    if method == "GET" and resource.endswith("/lab/tests"):
        rows = query("SELECT * FROM lab_tests ORDER BY category, test_name")
        return _json(200, {"count": len(rows), "tests": rows})

    # ---- GET ONE TEST ----
    if method == "GET" and resource.endswith("/lab/tests/{test_id}"):
        tid = _pp(event, "test_id")
        test = query("SELECT * FROM lab_tests WHERE test_id = %s", (tid,), fetch="one")
        if not test:
            return _json(404, {"error": "Lab test not found"})
        return _json(200, {"test": test})

    # ---- CREATE TEST ----
    if method == "POST" and resource.endswith("/lab/tests"):
        d = _body(event)
        if not d.get("test_name"):
            return _json(400, {"error": "test_name is required"})
        res = execute(
            "INSERT INTO lab_tests (test_name, category, sample_type, unit, "
            "normal_range, price, turnaround_hours, is_active) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (d["test_name"], d.get("category", "Biochemistry"), d.get("sample_type"),
             d.get("unit"), d.get("normal_range"), d.get("price", 0),
             d.get("turnaround_hours", 24), d.get("is_active", 1)),
        )
        return _json(201, {"message": "Lab test created", "test_id": res["lastrowid"]})

    # ---- UPDATE TEST ----
    if method == "PUT" and resource.endswith("/lab/tests/{test_id}"):
        tid = _pp(event, "test_id")
        d = _body(event)
        fields = ["test_name", "category", "sample_type", "unit", "normal_range",
                  "price", "turnaround_hours", "is_active"]
        sets = [f"{f} = %s" for f in fields if f in d]
        if not sets:
            return _json(400, {"error": "No fields to update"})
        vals = [d[f] for f in fields if f in d]
        vals.append(tid)
        execute(f"UPDATE lab_tests SET {', '.join(sets)} WHERE test_id = %s", tuple(vals))
        return _json(200, {"message": "Lab test updated", "test_id": int(tid)})

    # ---- DELETE TEST ----
    if method == "DELETE" and resource.endswith("/lab/tests/{test_id}"):
        tid = _pp(event, "test_id")
        execute("DELETE FROM lab_tests WHERE test_id = %s", (tid,))
        return _json(200, {"message": "Lab test deleted", "test_id": int(tid)})

    # ================= LAB ORDERS =================
    # ---- PENDING ORDERS ----
    if method == "GET" and resource.endswith("/lab/pending"):
        rows = _enrich_orders(query(_ORDER_SELECT +
                     "WHERE o.status IN ('Ordered','Sample Collected','Processing') "
                     "ORDER BY o.order_date ASC"))
        return _json(200, {"count": len(rows), "orders": rows})

    # ---- ORDERS FOR PATIENT ----
    if method == "GET" and resource.endswith("/lab/orders/patient/{patient_id}"):
        pid = _pp(event, "patient_id")
        rows = _enrich_orders(query(_ORDER_SELECT + "WHERE o.patient_id = %s ORDER BY o.order_date DESC", (pid,)))
        return _json(200, {"count": len(rows), "orders": rows})

    # ---- LIST ORDERS ----
    if method == "GET" and resource.rstrip("/").endswith("/lab/orders"):
        rows = _enrich_orders(query(_ORDER_SELECT + "ORDER BY o.order_date DESC"))
        return _json(200, {"count": len(rows), "orders": rows})

    # ---- GET ONE ORDER ----
    if method == "GET" and resource.endswith("/lab/orders/{order_id}"):
        oid = _pp(event, "order_id")
        order = query(_ORDER_SELECT + "WHERE o.order_id = %s", (oid,), fetch="one")
        if not order:
            return _json(404, {"error": "Lab order not found"})
        return _json(200, {"order": _enrich_orders([order])[0]})

    # ---- CREATE ORDER ----
    if method == "POST" and resource.endswith("/lab/orders"):
        d = _body(event)
        if not d.get("patient_id") or not d.get("test_id"):
            return _json(400, {"error": "patient_id and test_id are required"})
        # Synchronisation: validate patient + test exist
        p = query("SELECT patient_id FROM patients WHERE patient_id = %s",
                  (d["patient_id"],), database=DB_PATIENTS, fetch="one")
        if not p:
            return _json(404, {"error": "Patient not found — cannot order a lab test"})
        t = query("SELECT test_id FROM lab_tests WHERE test_id = %s",
                  (d["test_id"],), fetch="one")
        if not t:
            return _json(404, {"error": "Lab test not found"})
        if d.get("ordered_by"):
            doc = query("SELECT doctor_id FROM doctors WHERE doctor_id = %s",
                        (d["ordered_by"],), database=DB_DOCTORS, fetch="one")
            if not doc:
                return _json(404, {"error": "Doctor not found"})
        res = execute(
            "INSERT INTO lab_orders (patient_id, test_id, ordered_by, priority, "
            "status, remarks) VALUES (%s,%s,%s,%s,%s,%s)",
            (d["patient_id"], d["test_id"], d.get("ordered_by"),
             d.get("priority", "Routine"), d.get("status", "Ordered"),
             d.get("remarks")),
        )
        return _json(201, {"message": "Lab test ordered", "order_id": res["lastrowid"]})

    # ---- UPDATE ORDER (status / result) ----
    if method == "PUT" and resource.endswith("/lab/orders/{order_id}"):
        oid = _pp(event, "order_id")
        d = _body(event)
        fields = ["status", "result_value", "remarks", "report_date", "priority"]
        sets = [f"{f} = %s" for f in fields if f in d]
        if not sets:
            return _json(400, {"error": "No fields to update"})
        vals = [d[f] for f in fields if f in d]
        vals.append(oid)
        execute(f"UPDATE lab_orders SET {', '.join(sets)} WHERE order_id = %s", tuple(vals))
        return _json(200, {"message": "Lab order updated", "order_id": int(oid)})

    # ---- DELETE ORDER ----
    if method == "DELETE" and resource.endswith("/lab/orders/{order_id}"):
        oid = _pp(event, "order_id")
        execute("DELETE FROM lab_orders WHERE order_id = %s", (oid,))
        return _json(200, {"message": "Lab order deleted", "order_id": int(oid)})

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

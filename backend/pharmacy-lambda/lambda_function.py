"""
Lambda handler for the PHARMACY database (hospital_pharmacy).

Routes:
    GET    /pharmacy/medicines                    -> list the medicine catalog
    POST   /pharmacy/medicines                    -> add a medicine
    GET    /pharmacy/medicines/{id}               -> get one medicine
    PUT    /pharmacy/medicines/{id}               -> update a medicine (incl. stock)
    DELETE /pharmacy/medicines/{id}               -> delete a medicine
    GET    /pharmacy/prescriptions                -> list all prescriptions
    POST   /pharmacy/prescriptions                -> new prescription (stock-checked)
    GET    /pharmacy/prescriptions/{id}           -> get one prescription
    PUT    /pharmacy/prescriptions/{id}           -> update (dispensing cuts stock)
    DELETE /pharmacy/prescriptions/{id}           -> delete a prescription
    GET    /pharmacy/prescriptions/patient/{pid}  -> prescriptions for a patient
    GET    /pharmacy/low-stock                    -> medicines at/below reorder level
"""
import json
from datetime import datetime
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


_RX_SELECT = (
    "SELECT pr.*, "
    "m.medicine_name, m.unit AS medicine_unit, m.unit_price, "
    "(m.unit_price * pr.quantity) AS total_amount, "
    "m.stock_quantity "
    "FROM prescriptions pr "
    "LEFT JOIN medicines m ON pr.medicine_id = m.medicine_id "
)


def _enrich_rx(rows):
    """Attach patient_name / doctor_name from their own instances
    (cross-database JOINs no longer exist in the 6-RDS topology)."""
    if not rows:
        return rows
    _pnames = fetch_by_ids(DB_PATIENTS, "patients", "patient_id",
                           "CONCAT(first_name,' ',last_name) AS patient_name",
                           [r["patient_id"] for r in rows])
    _dnames = fetch_by_ids(DB_DOCTORS, "doctors", "doctor_id",
                           "CONCAT(first_name,' ',last_name) AS doctor_name",
                           [r.get("doctor_id") for r in rows])
    for r in rows:
        r["patient_name"] = (_pnames.get(r["patient_id"]) or {}).get("patient_name")
        r["doctor_name"] = (_dnames.get(r.get("doctor_id")) or {}).get("doctor_name")
    return rows


def lambda_handler(event, context):
    method = event.get("httpMethod", "GET")
    resource = event.get("resource", event.get("path", ""))
    # Shim: terraform routes /pharmacy through {proxy+}, so translate the
    # concrete path back to the route templates matched below.
    _seg = [s for s in (event.get("path") or "").split("/") if s]
    _ppx = dict(event.get("pathParameters") or {})
    if len(_seg) == 4 and _seg[:3] == ["pharmacy", "prescriptions", "patient"]:
        _ppx["patient_id"] = _seg[3]
        resource = "/pharmacy/prescriptions/patient/{patient_id}"
    elif _seg == ["pharmacy", "medicines"]:
        resource = "/pharmacy/medicines"
    elif len(_seg) == 3 and _seg[:2] == ["pharmacy", "medicines"]:
        _ppx["medicine_id"] = _seg[2]
        resource = "/pharmacy/medicines/{medicine_id}"
    elif _seg == ["pharmacy", "prescriptions"]:
        resource = "/pharmacy/prescriptions"
    elif len(_seg) == 3 and _seg[:2] == ["pharmacy", "prescriptions"]:
        _ppx["prescription_id"] = _seg[2]
        resource = "/pharmacy/prescriptions/{prescription_id}"
    elif _seg == ["pharmacy", "low-stock"]:
        resource = "/pharmacy/low-stock"
    event["pathParameters"] = _ppx

    if method == "OPTIONS":
        return _json(200, {"message": "OK"})

    # ================= MEDICINE CATALOG =================
    # ---- LOW STOCK ----
    if method == "GET" and resource.endswith("/pharmacy/low-stock"):
        rows = query("SELECT * FROM medicines WHERE stock_quantity <= reorder_level "
                     "ORDER BY stock_quantity ASC")
        return _json(200, {"count": len(rows), "medicines": rows})

    # ---- LIST MEDICINES ----
    if method == "GET" and resource.endswith("/pharmacy/medicines"):
        rows = query("SELECT * FROM medicines ORDER BY category, medicine_name")
        return _json(200, {"count": len(rows), "medicines": rows})

    # ---- GET ONE MEDICINE ----
    if method == "GET" and resource.endswith("/pharmacy/medicines/{medicine_id}"):
        mid = _pp(event, "medicine_id")
        med = query("SELECT * FROM medicines WHERE medicine_id = %s", (mid,), fetch="one")
        if not med:
            return _json(404, {"error": "Medicine not found"})
        return _json(200, {"medicine": med})

    # ---- CREATE MEDICINE ----
    if method == "POST" and resource.endswith("/pharmacy/medicines"):
        d = _body(event)
        if not d.get("medicine_name"):
            return _json(400, {"error": "medicine_name is required"})
        res = execute(
            "INSERT INTO medicines (medicine_name, generic_name, category, manufacturer, "
            "unit, unit_price, stock_quantity, reorder_level, expiry_date, "
            "requires_prescription) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (d["medicine_name"], d.get("generic_name"), d.get("category", "Other"),
             d.get("manufacturer"), d.get("unit", "Tablet"), d.get("unit_price", 0),
             d.get("stock_quantity", 0), d.get("reorder_level", 20),
             d.get("expiry_date") or None, d.get("requires_prescription", 1)),
        )
        return _json(201, {"message": "Medicine created", "medicine_id": res["lastrowid"]})

    # ---- UPDATE MEDICINE ----
    if method == "PUT" and resource.endswith("/pharmacy/medicines/{medicine_id}"):
        mid = _pp(event, "medicine_id")
        d = _body(event)
        fields = ["medicine_name", "generic_name", "category", "manufacturer", "unit",
                  "unit_price", "stock_quantity", "reorder_level", "expiry_date",
                  "requires_prescription"]
        sets = [f"{f} = %s" for f in fields if f in d]
        if not sets:
            return _json(400, {"error": "No fields to update"})
        vals = [d[f] if d[f] != "" else None for f in fields if f in d]
        vals.append(mid)
        execute(f"UPDATE medicines SET {', '.join(sets)} WHERE medicine_id = %s", tuple(vals))
        return _json(200, {"message": "Medicine updated", "medicine_id": int(mid)})

    # ---- DELETE MEDICINE ----
    if method == "DELETE" and resource.endswith("/pharmacy/medicines/{medicine_id}"):
        mid = _pp(event, "medicine_id")
        execute("DELETE FROM medicines WHERE medicine_id = %s", (mid,))
        return _json(200, {"message": "Medicine deleted", "medicine_id": int(mid)})

    # ================= PRESCRIPTIONS =================
    # ---- PRESCRIPTIONS FOR PATIENT ----
    if method == "GET" and resource.endswith("/pharmacy/prescriptions/patient/{patient_id}"):
        pid = _pp(event, "patient_id")
        rows = _enrich_rx(query(_RX_SELECT + "WHERE pr.patient_id = %s ORDER BY pr.prescribed_date DESC", (pid,)))
        return _json(200, {"count": len(rows), "prescriptions": rows})

    # ---- LIST PRESCRIPTIONS ----
    if method == "GET" and resource.rstrip("/").endswith("/pharmacy/prescriptions"):
        rows = _enrich_rx(query(_RX_SELECT + "ORDER BY pr.prescribed_date DESC"))
        return _json(200, {"count": len(rows), "prescriptions": rows})

    # ---- GET ONE PRESCRIPTION ----
    if method == "GET" and resource.endswith("/pharmacy/prescriptions/{prescription_id}"):
        rid = _pp(event, "prescription_id")
        rx = query(_RX_SELECT + "WHERE pr.prescription_id = %s", (rid,), fetch="one")
        if not rx:
            return _json(404, {"error": "Prescription not found"})
        return _json(200, {"prescription": _enrich_rx([rx])[0]})

    # ---- CREATE PRESCRIPTION (stock-checked) ----
    if method == "POST" and resource.endswith("/pharmacy/prescriptions"):
        d = _body(event)
        if not d.get("patient_id") or not d.get("medicine_id"):
            return _json(400, {"error": "patient_id and medicine_id are required"})
        qty = int(d.get("quantity") or 1)
        if qty < 1:
            return _json(400, {"error": "quantity must be at least 1"})
        p = query("SELECT patient_id FROM patients WHERE patient_id = %s",
                  (d["patient_id"],), database=DB_PATIENTS, fetch="one")
        if not p:
            return _json(404, {"error": "Patient not found — cannot prescribe"})
        med = query("SELECT medicine_id, stock_quantity FROM medicines WHERE medicine_id = %s",
                    (d["medicine_id"],), fetch="one")
        if not med:
            return _json(404, {"error": "Medicine not found"})
        if int(med["stock_quantity"]) < qty:
            return _json(400, {"error": f"Insufficient stock — only {med['stock_quantity']} left"})
        if d.get("doctor_id"):
            doc = query("SELECT doctor_id FROM doctors WHERE doctor_id = %s",
                        (d["doctor_id"],), database=DB_DOCTORS, fetch="one")
            if not doc:
                return _json(404, {"error": "Doctor not found"})
        res = execute(
            "INSERT INTO prescriptions (patient_id, doctor_id, medicine_id, quantity, "
            "dosage, frequency, duration_days, status, remarks) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (d["patient_id"], d.get("doctor_id"), d["medicine_id"], qty,
             d.get("dosage"), d.get("frequency"), d.get("duration_days"),
             d.get("status", "Pending"), d.get("remarks")),
        )
        return _json(201, {"message": "Prescription created", "prescription_id": res["lastrowid"]})

    # ---- UPDATE PRESCRIPTION (dispensing cuts stock once) ----
    if method == "PUT" and resource.endswith("/pharmacy/prescriptions/{prescription_id}"):
        rid = _pp(event, "prescription_id")
        d = _body(event)
        current = query("SELECT * FROM prescriptions WHERE prescription_id = %s", (rid,), fetch="one")
        if not current:
            return _json(404, {"error": "Prescription not found"})
        # Transition into Dispensed: decrement stock atomically, once.
        if d.get("status") == "Dispensed" and current["status"] != "Dispensed":
            cut = execute(
                "UPDATE medicines SET stock_quantity = stock_quantity - %s "
                "WHERE medicine_id = %s AND stock_quantity >= %s",
                (current["quantity"], current["medicine_id"], current["quantity"]))
            if cut["rowcount"] == 0:
                return _json(400, {"error": "Insufficient stock to dispense"})
            if not d.get("dispensed_date"):
                d["dispensed_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fields = ["quantity", "dosage", "frequency", "duration_days", "status",
                  "dispensed_date", "remarks"]
        sets = [f"{f} = %s" for f in fields if f in d]
        if not sets:
            return _json(400, {"error": "No fields to update"})
        vals = [d[f] if d[f] != "" else None for f in fields if f in d]
        vals.append(rid)
        execute(f"UPDATE prescriptions SET {', '.join(sets)} WHERE prescription_id = %s", tuple(vals))
        return _json(200, {"message": "Prescription updated", "prescription_id": int(rid)})

    # ---- DELETE PRESCRIPTION ----
    if method == "DELETE" and resource.endswith("/pharmacy/prescriptions/{prescription_id}"):
        rid = _pp(event, "prescription_id")
        execute("DELETE FROM prescriptions WHERE prescription_id = %s", (rid,))
        return _json(200, {"message": "Prescription deleted", "prescription_id": int(rid)})

    return _json(404, {"error": "Route not found", "resource": resource})

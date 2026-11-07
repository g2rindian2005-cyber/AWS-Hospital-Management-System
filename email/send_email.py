"""
High-level email helpers that load HTML templates and send them via SES SMTP.
Each function corresponds to a hospital event and is called by the Lambdas.
"""
import os
from smtp_config import send_email

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")


def _load_template(name):
    path = os.path.join(TEMPLATE_DIR, name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def send_registration_email(to_email, patient_name, patient_id):
    """Sent when a new patient is registered."""
    html = _load_template("registration.html")
    html = html.replace("{{patient_name}}", str(patient_name)) \
               .replace("{{patient_id}}", str(patient_id))
    return send_email(to_email, "Welcome to AWS Hospital Management System", html)


def send_bill_email(to_email, patient_id, bill_id, description, amount):
    """Sent when a new bill is created for a patient."""
    html = _load_template("bill.html")
    html = (html.replace("{{patient_id}}", str(patient_id))
               .replace("{{bill_id}}", str(bill_id))
               .replace("{{description}}", str(description))
               .replace("{{amount}}", f"{amount:.2f}"))
    return send_email(to_email, f"New Bill #{bill_id} — AWS Hospital", html)


def send_payment_receipt_email(to_email, payment_id, bill_id, amount):
    """Sent when a payment is recorded."""
    html = _load_template("payment-receipt.html")
    html = (html.replace("{{payment_id}}", str(payment_id))
               .replace("{{bill_id}}", str(bill_id))
               .replace("{{amount}}", f"{amount:.2f}"))
    return send_email(to_email, f"Payment Receipt — AWS Hospital", html)


def send_appointment_email(to_email, patient_id, assignment_id, doctor_name, appointment_date):
    """Sent when a doctor is assigned to a patient."""
    html = _load_template("appointment.html")
    html = (html.replace("{{patient_id}}", str(patient_id))
               .replace("{{assignment_id}}", str(assignment_id))
               .replace("{{doctor_name}}", str(doctor_name))
               .replace("{{appointment_date}}", str(appointment_date)))
    return send_email(to_email, "Appointment Confirmation — AWS Hospital", html)

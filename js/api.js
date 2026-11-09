/* ============================================================
   API layer — talks to AWS API Gateway which proxies to Lambdas
   Update API_BASE_URL with your deployed API Gateway URL.
   ============================================================ */

const API_BASE_URL = window.HMS_CONFIG?.apiBase ||
  (() => { try { return localStorage.getItem("hms_api_base"); } catch (e) { return null; } })() ||
  "https://s5x2pju9d3.execute-api.us-east-1.amazonaws.com/prod";

/** Simple JWT-like token stored in localStorage after login */
function getToken() {
  return localStorage.getItem("hms_token") || sessionStorage.getItem("hms_token") || "";
}
function setToken(t, remember = true) {
  const store = remember ? localStorage : sessionStorage;
  const other = remember ? sessionStorage : localStorage;
  other.removeItem("hms_token");
  store.setItem("hms_token", t);
}
function clearToken() {
  localStorage.removeItem("hms_token");
  sessionStorage.removeItem("hms_token");
}

/** Central request wrapper with auth + error handling */
async function request(path, options = {}) {
  const url = `${API_BASE_URL}${path}`;
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  try {
    const res = await fetch(url, { ...options, headers });
    const data = await res.json();
    if (!res.ok) {
      const msg = data?.error || `HTTP ${res.status}`;
      showToast(msg, "error");
      return null;
    }
    return data;
  } catch (err) {
    // Mock data is strictly opt-in for local development (HMS_CONFIG.devMock).
    // In production a network failure is a real error: tell the user, return null.
    if (window.HMS_CONFIG?.devMock === true) {
      console.warn(`[API] ${path} failed, using mock data (devMock):`, err.message);
      return mockFallback(path, options);
    }
    console.warn(`[API] ${path} failed:`, err.message);
    if (typeof showToast === "function") {
      try { showToast("Unable to reach the server. Please check your connection and try again.", "error"); } catch (e) {}
    }
    return null;
  }
}

/* ---------------- PATIENTS ---------------- */
const PatientsAPI = {
  list:   ()        => request("/patients"),
  get:    (id)      => request(`/patients/${id}`),
  create: (body)    => request("/patients",        { method: "POST",   body: JSON.stringify(body) }),
  update: (id, b)   => request(`/patients/${id}`, { method: "PUT",    body: JSON.stringify(b) }),
  remove: (id)      => request(`/patients/${id}`, { method: "DELETE" }),
};

/* ---------------- BILLING ---------------- */
const BillingAPI = {
  listBills:    ()        => request("/bills"),
  getBill:      (id)      => request(`/bills/${id}`),
  billsFor:     (pid)     => request(`/bills/patient/${pid}`),
  createBill:   (body)    => request("/bills",        { method: "POST", body: JSON.stringify(body) }),
  updateBill:   (id, b)   => request(`/bills/${id}`, { method: "PUT",  body: JSON.stringify(b) }),
  removeBill:   (id)      => request(`/bills/${id}`, { method: "DELETE" }),

  listPayments: ()        => request("/payments"),
  paymentsFor:  (pid)     => request(`/payments/patient/${pid}`),
  recordPayment:(body)    => request("/payments",     { method: "POST", body: JSON.stringify(body) }),

  dues:         ()        => request("/dues"),
};

/* ---------------- DISEASES ---------------- */
const DiseasesAPI = {
  list:    ()        => request("/diseases"),
  get:     (id)      => request(`/diseases/${id}`),
  create:  (body)    => request("/diseases",         { method: "POST",   body: JSON.stringify(body) }),
  update:  (id, b)   => request(`/diseases/${id}`,   { method: "PUT",    body: JSON.stringify(b) }),
  remove:  (id)      => request(`/diseases/${id}`,   { method: "DELETE" }),
  forPatient: (pid)  => request(`/diseases/patient/${pid}`),
  active:  ()        => request("/diseases/active"),
};

/* ---------------- DOCTORS ---------------- */
const DoctorsAPI = {
  list:           ()        => request("/doctors"),
  get:            (id)      => request(`/doctors/${id}`),
  create:         (body)    => request("/doctors",            { method: "POST",   body: JSON.stringify(body) }),
  update:         (id, b)   => request(`/doctors/${id}`,       { method: "PUT",    body: JSON.stringify(b) }),
  remove:         (id)      => request(`/doctors/${id}`,       { method: "DELETE" }),

  listAssignments:()        => request("/assignments"),
  assignment:     (id)      => request(`/assignments/${id}`),
  forDoctor:      (did)     => request(`/assignments/doctor/${did}`),
  forPatient:      (pid)     => request(`/assignments/patient/${pid}`),
  assign:         (body)    => request("/assignments",         { method: "POST",   body: JSON.stringify(body) }),
  updateAssign:   (id, b)   => request(`/assignments/${id}`,   { method: "PUT",    body: JSON.stringify(b) }),
  removeAssign:   (id)      => request(`/assignments/${id}`,   { method: "DELETE" }),
};

/* ---------------- AUTH ---------------- */
const AuthAPI = {
  // POST /auth/login — returns whatever the auth Lambda returns (e.g. { token, user }).
  // This method stores nothing itself; the caller decides where to keep the token
  // (localStorage for "remember me", sessionStorage otherwise).
  login: (email, password) => request("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
};

/* ---------------- Toast helper ---------------- */
function showToast(msg, type = "info") {
  let toast = document.getElementById("toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "toast";
    toast.className = "toast";
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.className = `toast toast-${type} show`;
  clearTimeout(toast._t);
  toast._t = setTimeout(() => toast.classList.remove("show"), 3500);
}

/* ---------------- Mock fallback (for local preview) ---------------- */
function mockFallback(path) {
  // Returns a sample payload so the UI works offline during development
  const m = {
    "/patients":              { count: 5, patients: MOCK_DATA.patients },
    "/bills":                 { count: 5, bills: MOCK_DATA.bills },
    "/dues":                  { count: 3, dues: MOCK_DATA.dues },
    "/payments":              { count: 3, payments: MOCK_DATA.payments },
    "/diseases":              { count: 5, diseases: MOCK_DATA.diseases },
    "/diseases/active":       { count: 4, active_diseases: MOCK_DATA.diseases.filter(d => d.status !== "Recovered") },
    "/doctors":               { count: 5, doctors: MOCK_DATA.doctors },
    "/assignments":          { count: 5, assignments: MOCK_DATA.assignments },
  };
  return Promise.resolve(m[path] || { message: "ok" });
}

const MOCK_DATA = {
  patients: [
    { patient_id:1, first_name:"Rahul",  last_name:"Sharma", date_of_birth:"1990-05-14", gender:"Male",   phone:"9876543210", email:"rahul.sharma@email.com",  blood_group:"O+",  registration_date:"2026-10-01" },
    { patient_id:2, first_name:"Priya",  last_name:"Patel",  date_of_birth:"1988-09-22", gender:"Female", phone:"9876543211", email:"priya.patel@email.com",   blood_group:"A+",  registration_date:"2026-09-20" },
    { patient_id:3, first_name:"Amit",   last_name:"Verma",  date_of_birth:"1995-01-30", gender:"Male",   phone:"9876543212", email:"amit.verma@email.com",     blood_group:"B+",  registration_date:"2026-10-15" },
    { patient_id:4, first_name:"Sneha",  last_name:"Reddy",  date_of_birth:"2000-07-08", gender:"Female", phone:"9876543213", email:"sneha.reddy@email.com",    blood_group:"AB+", registration_date:"2026-08-05" },
    { patient_id:5, first_name:"Karan",  last_name:"Singh",  date_of_birth:"1982-11-19", gender:"Male",   phone:"9876543214", email:"karan.singh@email.com",    blood_group:"O-",  registration_date:"2026-07-10" },
  ],
  bills: [
    { bill_id:1, patient_id:1, patient_name:"Rahul Sharma",  description:"Cardiology consultation + ECG",      category:"Consultation", amount:1500, net_amount:1500, status:"Partial", bill_date:"2026-10-01" },
    { bill_id:2, patient_id:2, patient_name:"Priya Patel",   description:"Neurology consultation + MRI scan",  category:"Lab Test",     amount:5000, net_amount:4500, status:"Pending", bill_date:"2026-09-20" },
    { bill_id:3, patient_id:3, patient_name:"Amit Verma",    description:"Orthopedic consultation + X-Ray",    category:"Consultation", amount:2500, net_amount:2500, status:"Paid",    bill_date:"2026-10-15" },
    { bill_id:4, patient_id:4, patient_name:"Sneha Reddy",   description:"Pulmonology consultation + Spirometry",category:"Consultation",amount:1800, net_amount:1800, status:"Pending", bill_date:"2026-08-05" },
    { bill_id:5, patient_id:5, patient_name:"Karan Singh",   description:"General consult + Blood sugar panel", category:"Lab Test",    amount:1200, net_amount:1100, status:"Partial", bill_date:"2026-07-10" },
  ],
  dues: [
    { bill_id:1, patient_id:1, patient_name:"Rahul Sharma", description:"Cardiology consultation + ECG",     net_amount:1500, due_amount:500,  status:"Partial", bill_date:"2026-10-01" },
    { bill_id:2, patient_id:2, patient_name:"Priya Patel",  description:"Neurology consultation + MRI scan", net_amount:4500, due_amount:4500, status:"Pending", bill_date:"2026-09-20" },
    { bill_id:4, patient_id:4, patient_name:"Sneha Reddy",   description:"Pulmonology consultation + Spirometry",net_amount:1800,due_amount:1800,status:"Pending", bill_date:"2026-08-05" },
  ],
  payments: [
    { payment_id:1, bill_id:1, patient_id:1, patient_name:"Rahul Sharma", amount_paid:1000, payment_method:"UPI",  transaction_id:"TXN-1001", payment_date:"2026-10-01" },
    { payment_id:2, bill_id:3, patient_id:3, patient_name:"Amit Verma",   amount_paid:2500, payment_method:"Card", transaction_id:"TXN-1002", payment_date:"2026-10-15" },
    { payment_id:3, bill_id:5, patient_id:5, patient_name:"Karan Singh",  amount_paid:500,  payment_method:"Cash", transaction_id:"TXN-1003", payment_date:"2026-07-10" },
  ],
  diseases: [
    { disease_id:1, patient_id:1, patient_name:"Rahul Sharma", disease_name:"Hypertension",    severity:"Moderate", status:"Under Treatment", diagnosis_date:"2026-10-01", follow_up_date:"2026-11-15" },
    { disease_id:2, patient_id:2, patient_name:"Priya Patel",  disease_name:"Migraine",        severity:"Mild",     status:"Active",          diagnosis_date:"2026-09-20", follow_up_date:"2026-11-10" },
    { disease_id:3, patient_id:3, patient_name:"Amit Verma",   disease_name:"Fracture - Tibia",severity:"Severe",  status:"Under Treatment", diagnosis_date:"2026-10-15", follow_up_date:"2026-12-01" },
    { disease_id:4, patient_id:4, patient_name:"Sneha Reddy",  disease_name:"Asthma",          severity:"Moderate", status:"Active",          diagnosis_date:"2026-08-05", follow_up_date:"2026-11-20" },
    { disease_id:5, patient_id:5, patient_name:"Karan Singh",  disease_name:"Type 2 Diabetes", severity:"Moderate",status:"Chronic",         diagnosis_date:"2026-07-10", follow_up_date:"2026-11-30" },
  ],
  doctors: [
    { doctor_id:1, first_name:"Dr. Anil",  last_name:"Gupta", specialization:"Cardiologist",     department:"Cardiology", phone:"9000012345", availability:"Available", consultation_fee:800 },
    { doctor_id:2, first_name:"Dr. Meera", last_name:"Nair",  specialization:"Neurologist",      department:"Neurology",  phone:"9000012346", availability:"Available", consultation_fee:1000 },
    { doctor_id:3, first_name:"Dr. Vivek", last_name:"Joshi", specialization:"Orthopedic",        department:"Orthopedics",phone:"9000012347", availability:"Busy",      consultation_fee:600 },
    { doctor_id:4, first_name:"Dr. Sunita",last_name:"Kapoor",specialization:"Pediatrician",     department:"Pediatrics", phone:"9000012348", availability:"Available", consultation_fee:500 },
    { doctor_id:5, first_name:"Dr. Rajesh",last_name:"Mehta", specialization:"General Physician", department:"General",    phone:"9000012349", availability:"On Leave",  consultation_fee:400 },
  ],
  assignments: [
    { assignment_id:1, patient_id:1, patient_name:"Rahul Sharma", doctor_id:1, doctor_name:"Dr. Anil Gupta", specialization:"Cardiologist", disease_name:"Hypertension", appointment_date:"2026-11-15 10:00", status:"Active",    room_number:"C-101" },
    { assignment_id:2, patient_id:2, patient_name:"Priya Patel",  doctor_id:2, doctor_name:"Dr. Meera Nair", specialization:"Neurologist", disease_name:"Migraine",     appointment_date:"2026-11-10 11:00", status:"Scheduled", room_number:"N-203" },
    { assignment_id:3, patient_id:3, patient_name:"Amit Verma",   doctor_id:3, doctor_name:"Dr. Vivek Joshi",specialization:"Orthopedic", disease_name:"Fracture - Tibia",appointment_date:"2026-12-01 09:00", status:"Active",    room_number:"O-305" },
    { assignment_id:4, patient_id:4, patient_name:"Sneha Reddy",  doctor_id:4, doctor_name:"Dr. Sunita Kapoor",specialization:"Pediatrician",disease_name:"Asthma",     appointment_date:"2026-11-20 14:00", status:"Scheduled", room_number:"P-102" },
    { assignment_id:5, patient_id:5, patient_name:"Karan Singh",  doctor_id:1, doctor_name:"Dr. Anil Gupta",  specialization:"Cardiologist", disease_name:"Type 2 Diabetes",appointment_date:"2026-11-30 15:00", status:"Active",   room_number:"G-201" },
  ],
};

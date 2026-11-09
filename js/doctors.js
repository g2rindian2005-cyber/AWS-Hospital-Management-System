/* doctors.js — shared library version for the doctor pages.
 *
 * NOTE: Pages currently use inline scripts (see doctors/add-doctor.html,
 * doctors/assign-doctor.html, doctors/appointments.html) and do NOT load
 * this file. These functions are the shared-library equivalents, aligned to
 * the REAL page element IDs and the existing API contract in js/api.js.
 * Nothing here auto-runs: there is deliberately no DOMContentLoaded handler,
 * so loading this file can never double-run a page's inline logic.
 * Every function is null-safe and no-ops when its elements/APIs are absent.
 */

function _docEsc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }
function _docBadge(s) { return typeof statusBadge === "function" ? statusBadge(s) : '<span class="badge badge-gray">' + _docEsc(s || "—") + "</span>"; }
function _docInitials(n) { return typeof initials === "function" ? initials(n) : "?"; }
function _docToast(m, t) { if (typeof showToast === "function") showToast(m, t); }
function _docVal(id) { const e = document.getElementById(id); return e ? e.value : ""; }
function _docTrim(id) { return String(_docVal(id) || "").trim(); }

/** Load doctors list. On appointments.html the real container is #doctorCards;
 *  a table body #doctorsTableBody is also supported if a page provides one. */
async function loadDoctorsTable() {
  const cards = document.getElementById("doctorCards");
  const tbody = document.getElementById("doctorsTableBody");
  if (!cards && !tbody) return;
  if (typeof DoctorsAPI === "undefined") return;
  const data = await DoctorsAPI.list();
  if (!data) return;
  const list = data.doctors || [];
  if (tbody) {
    tbody.innerHTML = list.length ? list.map(d => `
      <tr>
        <td class="fw-600">#${d.doctor_id}</td>
        <td>${_docEsc(d.first_name)} ${_docEsc(d.last_name)}</td>
        <td>${_docEsc(d.specialization || "—")}</td>
        <td>${_docEsc(d.department || "—")}</td>
        <td>${_docEsc(d.phone || "—")}</td>
        <td>${_docBadge(d.availability)}</td>
      </tr>`).join("")
      : '<tr><td colspan="6"><div class="empty-state"><h4>No doctors found</h4></div></td></tr>';
  }
  if (cards) {
    cards.innerHTML = list.length ? list.map(d => `
      <div class="doctor-card">
        <div class="doctor-card-avatar">${_docEsc(_docInitials((d.first_name || "") + " " + (d.last_name || "")))}</div>
        <div class="doctor-card-info">
          <div class="doctor-card-name">${_docEsc(d.first_name)} ${_docEsc(d.last_name)}</div>
          <div class="doctor-card-spec">${_docEsc(d.specialization || "")}</div>
        </div>
        ${_docBadge(d.availability)}
      </div>`).join("")
      : '<div class="empty-state"><p>No doctors</p></div>';
  }
}

/** Wire the add-doctor form (add-doctor.html: form#addDoctorForm, id-based
 *  fields). The page itself submits via its inline submitDoctor()/submitBtn
 *  flow; call this only from a page that wants form-submit handling instead.
 *  The payload matches the inline page exactly. */
function initAddDoctorForm() {
  const form = document.getElementById("addDoctorForm");
  if (!form || typeof DoctorsAPI === "undefined") return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const body = {
      first_name: _docTrim("firstName"),
      last_name: _docTrim("lastName"),
      gender: _docVal("gender"),
      date_of_birth: _docVal("dob"),
      specialization: _docVal("specialization"),
      department: _docTrim("department"),
      qualification: _docTrim("qualification"),
      experience_years: parseInt(_docVal("experience")) || 0,
      consultation_fee: parseFloat(_docVal("consultFee")) || 0,
      availability: _docVal("availability"),
      license_number: _docTrim("license"),
      joining_date: _docVal("joiningDate"),
      phone: _docTrim("phone"),
      email: _docTrim("email"),
    };
    if (!body.first_name || !body.last_name || !body.phone) { _docToast("Please fill in all required fields.", "warning"); return; }
    const res = await DoctorsAPI.create(body);
    if (res) { _docToast("Doctor registered successfully.", "success"); form.reset(); }
  });
}

/** Load assignments table. Real containers: appointments.html tbody#assignTable,
 *  dashboard.html tbody#assignmentsTable. */
async function loadAssignmentsTable() {
  const tbody = document.getElementById("assignTable") || document.getElementById("assignmentsTable") || document.getElementById("assignmentsTableBody");
  if (!tbody || typeof DoctorsAPI === "undefined") return;
  const data = await DoctorsAPI.listAssignments();
  if (!data) return;
  const list = data.assignments || [];
  tbody.innerHTML = list.length ? list.map(a => `
    <tr>
      <td class="fw-600">#${a.assignment_id}</td>
      <td>${_docEsc(a.patient_name || "Patient #" + a.patient_id)}</td>
      <td>${_docEsc(a.doctor_name || "Doctor #" + a.doctor_id)}</td>
      <td>${_docEsc(a.specialization || "—")}</td>
      <td>${_docEsc(a.disease_name || "—")}</td>
      <td>${_docBadge(a.status)}</td>
      <td>${_docEsc(String(a.appointment_date || "").slice(0, 16))}</td>
    </tr>`).join("")
    : '<tr><td colspan="7"><div class="empty-state"><h4>No assignments</h4></div></td></tr>';
}

/** Populate patient + doctor dropdowns on the assign-doctor page
 *  (assign-doctor.html: form#assignForm, select#patientId, select#doctorId,
 *  select#diseaseId). Submission itself is the page's inline
 *  submitAssignment() via button#submitBtn; this helper only fills selects. */
async function initAssignDoctorForm() {
  const patSel = document.getElementById("patientId");
  const docSel = document.getElementById("doctorId");
  if (!patSel && !docSel) return;
  const [pData, dData] = await Promise.all([
    typeof PatientsAPI !== "undefined" ? PatientsAPI.list() : Promise.resolve(null),
    typeof DoctorsAPI !== "undefined" ? DoctorsAPI.list() : Promise.resolve(null),
  ]);
  if (patSel && pData && pData.patients) {
    patSel.innerHTML = '<option value="">-- Select Patient --</option>' +
      pData.patients.map(p => `<option value="${p.patient_id}">${_docEsc(p.first_name)} ${_docEsc(p.last_name)} (#${p.patient_id})</option>`).join("");
  }
  if (docSel && dData && dData.doctors) {
    docSel.innerHTML = '<option value="">-- Select Doctor --</option>' +
      dData.doctors.map(d => `<option value="${d.doctor_id}">${_docEsc(d.first_name)} ${_docEsc(d.last_name)} (${_docEsc(d.specialization)})</option>`).join("");
  }
}

/** Build the API body from the real assign-doctor field IDs, matching the
 *  inline page's submitAssignment() payload exactly. Returns null when the
 *  form is absent. */
function buildAssignmentBody() {
  if (!document.getElementById("patientId") || !document.getElementById("doctorId")) return null;
  return {
    patient_id: parseInt(_docVal("patientId")),
    doctor_id: parseInt(_docVal("doctorId")),
    appointment_date: _docVal("appointmentDate"),
    room_number: _docTrim("roomNumber"),
    disease_id: _docVal("diseaseId") ? parseInt(_docVal("diseaseId")) : null,
    status: _docVal("assignStatus"),
    notes: _docTrim("notes"),
  };
}

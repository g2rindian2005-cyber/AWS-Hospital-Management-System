/* patients.js — shared library version for the patient pages.
 *
 * NOTE: Pages currently use inline scripts (see patients/view-patient.html,
 * patients/add-patient.html, patients/patient-history.html) and do NOT load
 * this file. These functions are the shared-library equivalents, aligned to
 * the REAL page element IDs and the existing API contract in js/api.js.
 * Nothing here auto-runs: there is deliberately no DOMContentLoaded handler,
 * so loading this file can never double-run a page's inline logic.
 * Every function is null-safe and no-ops when its elements/APIs are absent.
 */

/* ── Small guarded helpers (use ui.js globals when available) ── */
function _pEsc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }
function _pDate(d) { return typeof formatDate === "function" ? formatDate(d) : (d ? String(d).slice(0, 10) : "—"); }
function _pInitials(n) { return typeof initials === "function" ? initials(n) : "?"; }
function _pToast(m, t) { if (typeof showToast === "function") showToast(m, t); }
function _pVal(id) { const e = document.getElementById(id); return e ? e.value : ""; }
function _pTrim(id) { return String(_pVal(id) || "").trim(); }

/** Load and render the patients table (view-patient.html: tbody#patientTable). */
async function loadPatientsTable() {
  const tbody = document.getElementById("patientTable") || document.getElementById("patientsTableBody");
  if (!tbody || typeof PatientsAPI === "undefined") return;
  tbody.innerHTML = typeof skeletonRows === "function"
    ? skeletonRows(9, 5)
    : '<tr><td colspan="9"><div class="spinner"></div></td></tr>';
  const data = await PatientsAPI.list();
  if (!data) { tbody.innerHTML = ""; return; }
  const list = data.patients || [];
  if (!list.length) {
    tbody.innerHTML = '<tr><td colspan="9"><div class="empty-state"><h4>No patients found</h4><p>Register a patient to get started.</p></div></td></tr>';
    return;
  }
  tbody.innerHTML = list.map(p => `
    <tr>
      <td><div class="patient-cell"><div class="patient-avatar">${_pEsc(_pInitials((p.first_name || "") + " " + (p.last_name || "")))}</div>
        <div><div class="patient-name">${_pEsc(p.first_name)} ${_pEsc(p.last_name)}</div><div class="patient-id">${_pEsc(p.email || "—")}</div></div></div></td>
      <td><span class="badge badge-info">PID-${String(p.patient_id).padStart(4, "0")}</span></td>
      <td>${_pEsc(_pDate(p.date_of_birth))}</td>
      <td>${_pEsc(p.gender || "—")}</td>
      <td><span class="badge badge-gray">${_pEsc(p.blood_group || "—")}</span></td>
      <td>${_pEsc(p.phone || "—")}</td>
      <td>${_pEsc(p.email || "—")}</td>
      <td>${_pEsc(_pDate(p.registration_date))}</td>
      <td></td>
    </tr>`).join("");
}

/** Wire the add-patient form (add-patient.html: form#addPatientForm, id-based fields).
 *  The page itself submits via its inline submitForm()/submitBtn flow; call this
 *  only from a page that wants form-submit handling instead. Field names sent to
 *  the API match the inline page exactly. */
function initAddPatientForm() {
  const form = document.getElementById("addPatientForm");
  if (!form || typeof PatientsAPI === "undefined") return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const body = {
      first_name: _pTrim("firstName"),
      last_name: _pTrim("lastName"),
      date_of_birth: _pVal("dob"),
      gender: _pVal("gender"),
      blood_group: _pVal("bloodGroup"),
      phone: _pTrim("phone"),
      email: _pTrim("email"),
      address: _pTrim("address"),
      emergency_contact: _pTrim("emergencyName"),
      emergency_phone: _pTrim("emergencyPhone"),
      medical_notes: _pTrim("medicalNotes"),
    };
    if (!body.first_name || !body.last_name || !body.phone) { _pToast("Please fill in all required fields.", "warning"); return; }
    const res = await PatientsAPI.create(body);
    if (res) {
      _pToast("Patient registered! ID: PID-" + String(res.patient_id || res.id || "—").padStart(4, "0"), "success");
      form.reset();
    }
  });
}

/** Render a patient's synchronised history summary (patient-history.html:
 *  select#patientSelect, container#historyContent). Light card/badge theme —
 *  the page's own inline script fills the detailed profile sections; this
 *  library version renders a compact summary card into #historyContent. */
async function loadPatientHistory(patientId) {
  const select = document.getElementById("patientSelect");
  const container = document.getElementById("historyContent");
  if (!container || typeof PatientsAPI === "undefined") return;

  if (select && !select.options.length) {
    const data = await PatientsAPI.list();
    if (data && data.patients) {
      select.innerHTML = '<option value="">-- Select Patient --</option>' +
        data.patients.map(p => `<option value="${p.patient_id}">${_pEsc(p.first_name)} ${_pEsc(p.last_name)} (#${p.patient_id})</option>`).join("");
    }
  }

  const id = patientId || (select ? select.value : "");
  if (!id) return;
  const detail = await PatientsAPI.get(id);
  if (!detail || !detail.patient) return;
  const p = detail.patient;
  const s = detail.synchronised || {};
  const due = typeof formatCurrency === "function" ? formatCurrency(s.total_due || 0) : "₹" + Number(s.total_due || 0).toLocaleString("en-IN");
  container.style.display = "block";
  container.insertAdjacentHTML("afterbegin", `
    <div class="card" style="margin-bottom:20px;">
      <div class="card-body" style="display:flex;align-items:center;gap:14px;">
        <div class="patient-avatar" style="width:44px;height:44px;">${_pEsc(_pInitials((p.first_name || "") + " " + (p.last_name || "")))}</div>
        <div>
          <div class="fw-600">${_pEsc(p.first_name)} ${_pEsc(p.last_name)} <span class="badge badge-info">PID-${String(p.patient_id).padStart(4, "0")}</span></div>
          <div class="text-muted">${_pEsc(p.email || "")} • ${_pEsc(p.phone || "")} • Blood: ${_pEsc(p.blood_group || "—")}</div>
        </div>
      </div>
    </div>
    <div class="stat-grid" style="margin-bottom:20px;">
      <div class="stat-card stat-red"><div class="stat-info"><div class="stat-value">${due}</div><div class="stat-label">Total Pending Dues</div></div></div>
      <div class="stat-card stat-blue"><div class="stat-info"><div class="stat-value">${(s.bills || []).length}</div><div class="stat-label">Total Bills</div></div></div>
      <div class="stat-card stat-purple"><div class="stat-info"><div class="stat-value">${(s.diseases || []).length}</div><div class="stat-label">Disease Records</div></div></div>
      <div class="stat-card stat-teal"><div class="stat-info"><div class="stat-value">${(s.assignments || []).length}</div><div class="stat-label">Doctor Assignments</div></div></div>
    </div>`);
}

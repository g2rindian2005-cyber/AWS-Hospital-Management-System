/* diseases.js — shared library version for the disease pages.
 *
 * NOTE: Pages currently use inline scripts (see diseases/add-disease.html,
 * diseases/disease-history.html) and do NOT load this file. These functions
 * are the shared-library equivalents, aligned to the REAL page element IDs
 * and the existing API contract in js/api.js.
 * Nothing here auto-runs: there is deliberately no DOMContentLoaded handler,
 * so loading this file can never double-run a page's inline logic.
 * Every function is null-safe and no-ops when its elements/APIs are absent.
 */

function _dEsc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }
function _dDate(d) { return typeof formatDate === "function" ? formatDate(d) : (d ? String(d).slice(0, 10) : "—"); }
function _dBadge(s) { return typeof statusBadge === "function" ? statusBadge(s) : '<span class="badge badge-gray">' + _dEsc(s || "—") + "</span>"; }
function _dVal(id) { const e = document.getElementById(id); return e ? e.value : ""; }

/** Load diseases table (disease-history.html: tbody#diseaseTable). */
async function loadDiseasesTable() {
  const tbody = document.getElementById("diseaseTable") || document.getElementById("diseasesTableBody");
  if (!tbody || typeof DiseasesAPI === "undefined") return;
  tbody.innerHTML = typeof skeletonRows === "function" ? skeletonRows(8, 5) : '<tr><td colspan="8"><div class="spinner"></div></td></tr>';
  const data = await DiseasesAPI.list();
  if (!data) { tbody.innerHTML = ""; return; }
  const list = data.diseases || [];
  tbody.innerHTML = list.length ? list.map(d => `
    <tr>
      <td class="fw-600">#${d.disease_id}</td>
      <td>${_dEsc(d.patient_name || "Patient #" + d.patient_id)}</td>
      <td class="fw-600">${_dEsc(d.disease_name)}</td>
      <td>${_dBadge(d.severity)}</td>
      <td>${_dBadge(d.status)}</td>
      <td>${_dEsc(_dDate(d.diagnosis_date))}</td>
      <td>${_dEsc(_dDate(d.follow_up_date))}</td>
      <td></td>
    </tr>`).join("")
    : '<tr><td colspan="8"><div class="empty-state"><h4>No disease records</h4></div></td></tr>';
}

/** Populate patient + doctor dropdowns on the add-disease page
 *  (add-disease.html: select#patientId, select#assignedDoctor,
 *  form#addDiseaseForm). Submission itself is the page's inline
 *  submitDiagnosis() via button#submitBtn; this helper only fills selects,
 *  using the exact field IDs the inline page reads. */
async function initAddDiseaseForm() {
  const patSel = document.getElementById("patientId");
  const docSel = document.getElementById("assignedDoctor");
  if (!patSel && !docSel) return;
  const [pData, dData] = await Promise.all([
    typeof PatientsAPI !== "undefined" ? PatientsAPI.list() : Promise.resolve(null),
    typeof DoctorsAPI !== "undefined" ? DoctorsAPI.list() : Promise.resolve(null),
  ]);
  if (patSel && pData && pData.patients) {
    patSel.innerHTML = '<option value="">-- Select Patient --</option>' +
      pData.patients.map(p => `<option value="${p.patient_id}">${_dEsc(p.first_name)} ${_dEsc(p.last_name)} (#${p.patient_id})</option>`).join("");
  }
  if (docSel && dData && dData.doctors) {
    docSel.innerHTML = '<option value="">-- Select Doctor --</option>' +
      dData.doctors.map(d => `<option value="${d.doctor_id}">${_dEsc(d.first_name)} ${_dEsc(d.last_name)} (${_dEsc(d.specialization)})</option>`).join("");
  }
  const dateEl = document.getElementById("diagnosisDate");
  if (dateEl && !dateEl.value) dateEl.value = new Date().toISOString().split("T")[0];
}

/** Build the API body from the real add-disease field IDs, matching the
 *  inline page's submitDiagnosis() payload exactly. Returns null if the
 *  required fields are missing. Exported for reuse/testing. */
function buildDiseaseBody() {
  if (!document.getElementById("patientId") || !document.getElementById("diseaseName")) return null;
  return {
    patient_id: parseInt(_dVal("patientId")),
    disease_name: String(_dVal("diseaseName") || "").trim(),
    icd_code: String(_dVal("icdCode") || "").trim(),
    severity: _dVal("severity"),
    symptoms: String(_dVal("symptoms") || "").trim(),
    diagnosis_notes: String(_dVal("diagnosis") || "").trim(),
    treatment_details: String(_dVal("treatment") || "").trim(),
    diagnosis_date: _dVal("diagnosisDate"),
    follow_up_date: _dVal("followupDate"),
    status: _dVal("diseaseStatus"),
    assigned_doctor_id: _dVal("assignedDoctor") || null,
  };
}

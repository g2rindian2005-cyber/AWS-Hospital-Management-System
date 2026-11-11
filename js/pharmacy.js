/* pharmacy.js — shared library version for the pharmacy pages.
 *
 * NOTE: Pages currently use inline scripts (see pharmacy/*.html) and do
 * NOT load this file. These functions are the shared-library equivalents,
 * aligned to the REAL page element IDs and the API contract in js/api.js.
 * Nothing here auto-runs: there is deliberately no DOMContentLoaded handler,
 * so loading this file can never double-run a page's inline logic.
 * Every function is null-safe and no-ops when its elements/APIs are absent.
 */

function _pEsc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }
function _pDate(d) { return typeof formatDate === "function" ? formatDate(d) : (d ? String(d).slice(0, 10) : "—"); }
function _pBadge(s) { return typeof statusBadge === "function" ? statusBadge(s) : '<span class="badge badge-gray">' + _pEsc(s || "—") + "</span>"; }
function _pVal(id) { const e = document.getElementById(id); return e ? e.value : ""; }
function _pMoney(v) { return typeof formatCurrency === "function" ? formatCurrency(v) : "₹" + Number(v || 0).toLocaleString("en-IN"); }

/** Load the prescriptions table (prescriptions.html: tbody#rxTable). */
async function loadPrescriptionsTable() {
  const tbody = document.getElementById("rxTable") || document.getElementById("prescriptionsTableBody");
  if (!tbody || typeof PharmacyAPI === "undefined") return;
  tbody.innerHTML = typeof skeletonRows === "function" ? skeletonRows(8, 5) : '<tr><td colspan="8"><div class="spinner"></div></td></tr>';
  const data = await PharmacyAPI.listPrescriptions();
  if (!data) { tbody.innerHTML = ""; return; }
  const list = data.prescriptions || [];
  tbody.innerHTML = list.length ? list.map(r => `
    <tr>
      <td class="fw-600">#${r.prescription_id}</td>
      <td>${_pEsc(r.patient_name || "Patient #" + r.patient_id)}</td>
      <td class="fw-600">${_pEsc(r.medicine_name || "Medicine #" + r.medicine_id)}</td>
      <td>${r.quantity}</td>
      <td>${_pEsc(r.dosage || "—")}</td>
      <td>${_pMoney(r.total_amount)}</td>
      <td>${_pBadge(r.status)}</td>
      <td>${_pEsc(_pDate(r.prescribed_date))}</td>
      <td></td>
    </tr>`).join("")
    : '<tr><td colspan="9"><div class="empty-state"><h4>No prescriptions</h4></div></td></tr>';
}

/** Load the medicine catalog table (medicine-catalog.html: tbody#medicineTable). */
async function loadMedicinesTable() {
  const tbody = document.getElementById("medicineTable") || document.getElementById("medicinesTableBody");
  if (!tbody || typeof PharmacyAPI === "undefined") return;
  const data = await PharmacyAPI.listMedicines();
  if (!data) { tbody.innerHTML = ""; return; }
  const list = data.medicines || [];
  tbody.innerHTML = list.length ? list.map(m => `
    <tr>
      <td class="fw-600">${_pEsc(m.medicine_name)}</td>
      <td>${_pEsc(m.category || "—")}</td>
      <td>${_pEsc(m.unit || "—")}</td>
      <td>${_pMoney(m.unit_price)}</td>
      <td>${m.stock_quantity}</td>
      <td>${_pEsc(_pDate(m.expiry_date))}</td>
      <td></td>
    </tr>`).join("")
    : '<tr><td colspan="7"><div class="empty-state"><h4>No medicines in catalog</h4></div></td></tr>';
}

/** Populate patient / medicine / doctor dropdowns on the add-prescription
 *  page (add-prescription.html: select#patientId, select#medicineId,
 *  select#doctorId). */
async function initPrescriptionForm() {
  const patSel = document.getElementById("patientId");
  const medSel = document.getElementById("medicineId");
  const docSel = document.getElementById("doctorId");
  if (!patSel && !medSel && !docSel) return;
  const [pData, mData, dData] = await Promise.all([
    typeof PatientsAPI !== "undefined" ? PatientsAPI.list() : Promise.resolve(null),
    typeof PharmacyAPI !== "undefined" ? PharmacyAPI.listMedicines() : Promise.resolve(null),
    typeof DoctorsAPI !== "undefined" ? DoctorsAPI.list() : Promise.resolve(null),
  ]);
  if (patSel && pData && pData.patients) {
    patSel.innerHTML = '<option value="">— Select patient —</option>' +
      pData.patients.map(p => `<option value="${p.patient_id}">${_pEsc(p.first_name)} ${_pEsc(p.last_name)} (#${p.patient_id})</option>`).join("");
  }
  if (medSel && mData && mData.medicines) {
    medSel.innerHTML = '<option value="">— Select medicine —</option>' +
      mData.medicines.map(m => `<option value="${m.medicine_id}">${_pEsc(m.medicine_name)} — ₹${Number(m.unit_price || 0).toLocaleString("en-IN")} (Stock: ${m.stock_quantity})</option>`).join("");
  }
  if (docSel && dData && dData.doctors) {
    docSel.innerHTML = '<option value="">— Select doctor —</option>' +
      dData.doctors.map(d => `<option value="${d.doctor_id}">${_pEsc(d.first_name)} ${_pEsc(d.last_name)} (${_pEsc(d.specialization)})</option>`).join("");
  }
}

/** Build the API body from the add-prescription field IDs. Returns null
 *  when the required fields are missing. Exported for reuse/testing. */
function buildPrescriptionBody() {
  if (!document.getElementById("patientId") || !document.getElementById("medicineId")) return null;
  return {
    patient_id: parseInt(_pVal("patientId")),
    medicine_id: parseInt(_pVal("medicineId")),
    doctor_id: _pVal("doctorId") || null,
    quantity: parseInt(_pVal("quantity")) || 1,
    dosage: String(_pVal("dosage") || "").trim(),
    frequency: String(_pVal("frequency") || "").trim(),
    duration_days: parseInt(_pVal("durationDays")) || null,
    remarks: String(_pVal("remarks") || "").trim(),
  };
}

/* laboratory.js — shared library version for the laboratory pages.
 *
 * NOTE: Pages currently use inline scripts (see laboratory/*.html) and do
 * NOT load this file. These functions are the shared-library equivalents,
 * aligned to the REAL page element IDs and the API contract in js/api.js.
 * Nothing here auto-runs: there is deliberately no DOMContentLoaded handler,
 * so loading this file can never double-run a page's inline logic.
 * Every function is null-safe and no-ops when its elements/APIs are absent.
 */

function _lEsc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }
function _lDate(d) { return typeof formatDate === "function" ? formatDate(d) : (d ? String(d).slice(0, 10) : "—"); }
function _lBadge(s) { return typeof statusBadge === "function" ? statusBadge(s) : '<span class="badge badge-gray">' + _lEsc(s || "—") + "</span>"; }
function _lVal(id) { const e = document.getElementById(id); return e ? e.value : ""; }

/** Load the lab orders table (lab-orders.html: tbody#orderTable). */
async function loadLabOrdersTable() {
  const tbody = document.getElementById("orderTable") || document.getElementById("ordersTableBody");
  if (!tbody || typeof LabAPI === "undefined") return;
  tbody.innerHTML = typeof skeletonRows === "function" ? skeletonRows(8, 5) : '<tr><td colspan="8"><div class="spinner"></div></td></tr>';
  const data = await LabAPI.listOrders();
  if (!data) { tbody.innerHTML = ""; return; }
  const list = data.orders || [];
  tbody.innerHTML = list.length ? list.map(o => `
    <tr>
      <td class="fw-600">#${o.order_id}</td>
      <td>${_lEsc(o.patient_name || "Patient #" + o.patient_id)}</td>
      <td class="fw-600">${_lEsc(o.test_name || "Test #" + o.test_id)}</td>
      <td>${_lBadge(o.priority)}</td>
      <td>${_lBadge(o.status)}</td>
      <td>${_lEsc(o.result_value || "—")}</td>
      <td>${_lEsc(_lDate(o.order_date))}</td>
      <td></td>
    </tr>`).join("")
    : '<tr><td colspan="8"><div class="empty-state"><h4>No lab orders</h4></div></td></tr>';
}

/** Load the test catalog table (test-catalog.html: tbody#testTable). */
async function loadLabTestsTable() {
  const tbody = document.getElementById("testTable") || document.getElementById("testsTableBody");
  if (!tbody || typeof LabAPI === "undefined") return;
  const data = await LabAPI.listTests();
  if (!data) { tbody.innerHTML = ""; return; }
  const list = data.tests || [];
  tbody.innerHTML = list.length ? list.map(t => `
    <tr>
      <td class="fw-600">#${t.test_id}</td>
      <td class="fw-600">${_lEsc(t.test_name)}</td>
      <td>${_lEsc(t.category || "—")}</td>
      <td>${_lEsc(t.sample_type || "—")}</td>
      <td>${_lEsc(t.normal_range || "—")}</td>
      <td>₹${Number(t.price || 0).toLocaleString("en-IN")}</td>
      <td>${t.turnaround_hours || 24}h</td>
      <td></td>
    </tr>`).join("")
    : '<tr><td colspan="8"><div class="empty-state"><h4>No tests in catalog</h4></div></td></tr>';
}

/** Populate patient / test / doctor dropdowns on the order-test page
 *  (order-test.html: select#patientId, select#testId, select#orderedBy). */
async function initOrderTestForm() {
  const patSel = document.getElementById("patientId");
  const testSel = document.getElementById("testId");
  const docSel = document.getElementById("orderedBy");
  if (!patSel && !testSel && !docSel) return;
  const [pData, tData, dData] = await Promise.all([
    typeof PatientsAPI !== "undefined" ? PatientsAPI.list() : Promise.resolve(null),
    typeof LabAPI !== "undefined" ? LabAPI.listTests() : Promise.resolve(null),
    typeof DoctorsAPI !== "undefined" ? DoctorsAPI.list() : Promise.resolve(null),
  ]);
  if (patSel && pData && pData.patients) {
    patSel.innerHTML = '<option value="">— Select patient —</option>' +
      pData.patients.map(p => `<option value="${p.patient_id}">${_lEsc(p.first_name)} ${_lEsc(p.last_name)} (#${p.patient_id})</option>`).join("");
  }
  if (testSel && tData && tData.tests) {
    testSel.innerHTML = '<option value="">— Select test —</option>' +
      tData.tests.map(t => `<option value="${t.test_id}">${_lEsc(t.test_name)} — ₹${Number(t.price || 0).toLocaleString("en-IN")}</option>`).join("");
  }
  if (docSel && dData && dData.doctors) {
    docSel.innerHTML = '<option value="">— Select doctor —</option>' +
      dData.doctors.map(d => `<option value="${d.doctor_id}">${_lEsc(d.first_name)} ${_lEsc(d.last_name)} (${_lEsc(d.specialization)})</option>`).join("");
  }
}

/** Build the API body from the order-test field IDs. Returns null when
 *  the required fields are missing. Exported for reuse/testing. */
function buildLabOrderBody() {
  if (!document.getElementById("patientId") || !document.getElementById("testId")) return null;
  return {
    patient_id: parseInt(_lVal("patientId")),
    test_id: parseInt(_lVal("testId")),
    ordered_by: _lVal("orderedBy") || null,
    priority: _lVal("priority") || "Routine",
    remarks: String(_lVal("remarks") || "").trim(),
  };
}

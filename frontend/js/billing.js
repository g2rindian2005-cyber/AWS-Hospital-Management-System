/* billing.js — shared library version for the billing pages.
 *
 * NOTE: Pages currently use inline scripts (see billing/create-bill.html,
 * billing/payment.html, billing/pending-dues.html) and do NOT load this file.
 * These functions are the shared-library equivalents, aligned to the REAL
 * page element IDs and the existing API contract in js/api.js.
 * Nothing here auto-runs: there is deliberately no DOMContentLoaded handler,
 * so loading this file can never double-run a page's inline logic.
 * Every function is null-safe and no-ops when its elements/APIs are absent.
 */

function _bEsc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }
function _bCur(n) { return typeof formatCurrency === "function" ? formatCurrency(n) : "₹" + Number(n || 0).toLocaleString("en-IN"); }
function _bDate(d) { return typeof formatDate === "function" ? formatDate(d) : (d ? String(d).slice(0, 10) : "—"); }
function _bBadge(s) { return typeof statusBadge === "function" ? statusBadge(s) : '<span class="badge badge-gray">' + _bEsc(s || "—") + "</span>"; }
function _bToast(m, t) { if (typeof showToast === "function") showToast(m, t); }
function _bVal(id) { const e = document.getElementById(id); return e ? e.value : ""; }

/** Load bills table (create-bill.html: tbody#billTable). */
async function loadBillsTable() {
  const tbody = document.getElementById("billTable") || document.getElementById("billsTableBody");
  if (!tbody || typeof BillingAPI === "undefined") return;
  tbody.innerHTML = typeof skeletonRows === "function" ? skeletonRows(8, 5) : '<tr><td colspan="8"><div class="spinner"></div></td></tr>';
  const data = await BillingAPI.listBills();
  if (!data) { tbody.innerHTML = ""; return; }
  const list = data.bills || [];
  tbody.innerHTML = list.length ? list.map(b => `
    <tr>
      <td class="fw-600">#INV-${String(b.bill_id).padStart(5, "0")}</td>
      <td>${_bEsc(b.patient_name || "Patient #" + b.patient_id)}</td>
      <td>${_bEsc(b.description || "—")}</td>
      <td><span class="badge badge-gray">${_bEsc(b.category || "—")}</span></td>
      <td class="fw-600">${_bCur(b.net_amount != null ? b.net_amount : b.amount)}</td>
      <td>${_bBadge(b.status)}</td>
      <td>${_bEsc(_bDate(b.bill_date))}</td>
      <td></td>
    </tr>`).join("")
    : '<tr><td colspan="8"><div class="empty-state"><h4>No bills found</h4><p>Create a new invoice to get started.</p></div></td></tr>';
}

/** Populate the patient dropdown of the create-bill modal (create-bill.html:
 *  select#billPatient). The modal itself is submitted by the page's inline
 *  saveBill() via button#saveBillBtn; this helper only fills the select. */
async function initCreateBillForm() {
  const patientSel = document.getElementById("billPatient");
  if (!patientSel || typeof PatientsAPI === "undefined") return;
  const data = await PatientsAPI.list();
  if (data && data.patients) {
    patientSel.innerHTML = '<option value="">— Select patient —</option>' +
      data.patients.map(p => `<option value="${p.patient_id}">PID-${String(p.patient_id).padStart(4, "0")} — ${_bEsc(p.first_name)} ${_bEsc(p.last_name)}</option>`).join("");
  }
  const dateEl = document.getElementById("billDate");
  if (dateEl && !dateEl.value) dateEl.value = new Date().toISOString().split("T")[0];
}

/** Load pending dues table (pending-dues.html: tbody#dueTable, #totalDueAmt). */
async function loadPendingDues() {
  const tbody = document.getElementById("dueTable") || document.getElementById("duesTableBody");
  if (!tbody || typeof BillingAPI === "undefined") return;
  tbody.innerHTML = typeof skeletonRows === "function" ? skeletonRows(8, 5) : '<tr><td colspan="8"><div class="spinner"></div></td></tr>';
  const data = await BillingAPI.dues();
  if (!data) { tbody.innerHTML = ""; return; }
  const list = data.dues || [];
  let total = 0;
  tbody.innerHTML = list.length ? list.map(d => {
    total += Number(d.due_amount || 0);
    return `<tr>
      <td class="fw-600">#INV-${String(d.bill_id).padStart(5, "0")}</td>
      <td>${_bEsc(d.patient_name || "Patient #" + d.patient_id)}</td>
      <td>${_bEsc(d.description || "—")}</td>
      <td>${_bCur(d.net_amount)}</td>
      <td class="fw-600">${_bCur(d.due_amount)}</td>
      <td>${_bBadge(d.status)}</td>
      <td>${_bEsc(_bDate(d.bill_date))}</td>
      <td></td>
    </tr>`;
  }).join("")
    : '<tr><td colspan="8"><div class="empty-state"><h4>No pending dues</h4><p>All bills are settled.</p></div></td></tr>';
  const totalEl = document.getElementById("totalDueAmt") || document.getElementById("totalDues");
  if (totalEl) totalEl.textContent = _bCur(total);
}

/** Populate the bill dropdown of the payment modal (payment.html:
 *  select#payBillSelect). Recording is done by the page's inline
 *  recordPayment() via button#recordPayBtn using fields #payAmount,
 *  #payMethod, #payTxnId, #payDate — this helper only fills the select. */
async function initPaymentForm() {
  const billSel = document.getElementById("payBillSelect");
  if (!billSel || typeof BillingAPI === "undefined") return;
  const data = await BillingAPI.listBills();
  if (data && data.bills) {
    billSel.innerHTML = '<option value="">— Select bill —</option>' +
      data.bills.filter(b => b.status !== "Paid").map(b =>
        `<option value="${b.bill_id}">#INV-${String(b.bill_id).padStart(5, "0")} — ${_bEsc(b.patient_name || "Patient #" + b.patient_id)} (${_bCur(b.net_amount)})</option>`).join("");
  }
  const dateEl = document.getElementById("payDate");
  if (dateEl && !dateEl.value) dateEl.value = new Date().toISOString().split("T")[0];
}

/** Load payments table (payment.html: tbody#paymentTable). */
async function loadPaymentsTable() {
  const tbody = document.getElementById("paymentTable") || document.getElementById("paymentsTableBody");
  if (!tbody || typeof BillingAPI === "undefined") return;
  tbody.innerHTML = typeof skeletonRows === "function" ? skeletonRows(7, 5) : '<tr><td colspan="7"><div class="spinner"></div></td></tr>';
  const data = await BillingAPI.listPayments();
  if (!data) { tbody.innerHTML = ""; return; }
  const list = data.payments || [];
  tbody.innerHTML = list.length ? list.map(p => `
    <tr>
      <td class="fw-600">#${p.payment_id}</td>
      <td>${_bEsc(p.patient_name || "Patient #" + p.patient_id)}</td>
      <td>Bill #${p.bill_id}</td>
      <td class="fw-600">${_bCur(p.amount_paid)}</td>
      <td><span class="badge badge-info">${_bEsc(p.payment_method || "—")}</span></td>
      <td>${_bEsc(p.transaction_id || "—")}</td>
      <td>${_bEsc(_bDate(p.payment_date))}</td>
    </tr>`).join("")
    : '<tr><td colspan="7"><div class="empty-state"><h4>No payments found</h4></div></td></tr>';
}

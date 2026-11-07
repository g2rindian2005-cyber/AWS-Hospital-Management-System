/* billing.js — logic for create-bill, payment, pending-dues pages */

/** Load bills table (create-bill.html) */
async function loadBillsTable() {
  const tbody = document.getElementById("billsTableBody");
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="7"><div class="spinner"></div></td></tr>`;
  const data = await BillingAPI.listBills();
  if (!data) return;
  tbody.innerHTML = "";
  (data.bills || []).forEach(b => {
    const badge = b.status === "Paid" ? "badge-success" : b.status === "Partial" ? "badge-warning" : "badge-danger";
    tbody.insertAdjacentHTML("beforeend", `<tr>
      <td>#${b.bill_id}</td>
      <td>${b.patient_name || "Patient #" + b.patient_id}</td>
      <td>${b.description}</td>
      <td>${b.category || "—"}</td>
      <td>₹${Number(b.net_amount || b.amount).toFixed(2)}</td>
      <td><span class="badge ${badge}">${b.status}</span></td>
      <td>${(b.bill_date || "").toString().slice(0, 10)}</td>
    </tr>`);
  });
}

/** Init create-bill form — also loads patient dropdown */
async function initCreateBillForm() {
  const form = document.getElementById("createBillForm");
  const patientSel = document.getElementById("billPatient");
  if (!form) return;
  if (patientSel) {
    const data = await PatientsAPI.list();
    if (data?.patients) {
      patientSel.innerHTML = '<option value="">-- Select Patient --</option>' +
        data.patients.map(p => `<option value="${p.patient_id}">${p.first_name} ${p.last_name} (#${p.patient_id})</option>`).join("");
    }
  }
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    const body = Object.fromEntries(fd.entries());
    body.amount = parseFloat(body.amount);
    body.discount = parseFloat(body.discount) || 0;
    const res = await BillingAPI.createBill(body);
    if (res) { showToast(`Bill #${res.bill_id} created`, "success"); form.reset(); loadBillsTable(); }
  });
}

/** Load pending dues table (pending-dues.html) */
async function loadPendingDues() {
  const tbody = document.getElementById("duesTableBody");
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="6"><div class="spinner"></div></td></tr>`;
  const data = await BillingAPI.dues();
  if (!data) return;
  tbody.innerHTML = "";
  if (!data.dues?.length) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:rgba(255,255,255,0.4)">No pending dues 🎉</td></tr>`;
    return;
  }
  let total = 0;
  data.dues.forEach(d => {
    total += Number(d.due_amount);
    tbody.insertAdjacentHTML("beforeend", `<tr>
      <td>#${d.bill_id}</td>
      <td>${d.patient_name || "Patient #" + d.patient_id}</td>
      <td>${d.description}</td>
      <td>₹${Number(d.net_amount).toFixed(2)}</td>
      <td><span class="badge badge-danger">₹${Number(d.due_amount).toFixed(2)}</span></td>
      <td>${(d.bill_date || "").toString().slice(0,10)}</td>
    </tr>`);
  });
  const totalEl = document.getElementById("totalDues");
  if (totalEl) totalEl.textContent = `₹${total.toFixed(2)}`;
}

/** Init payment form (payment.html) */
async function initPaymentForm() {
  const form = document.getElementById("paymentForm");
  const billSel = document.getElementById("paymentBill");
  const patSel = document.getElementById("paymentPatient");
  if (!form) return;
  if (patSel) {
    const data = await PatientsAPI.list();
    if (data?.patients) {
      patSel.innerHTML = '<option value="">-- Select Patient --</option>' +
        data.patients.map(p => `<option value="${p.patient_id}">${p.first_name} ${p.last_name} (#${p.patient_id})</option>`).join("");
    }
  }
  if (billSel) {
    const data = await BillingAPI.listBills();
    if (data?.bills) {
      billSel.innerHTML = '<option value="">-- Select Bill --</option>' +
        data.bills.filter(b => b.status !== "Paid").map(b =>
          `<option value="${b.bill_id}" data-pid="${b.patient_id}">Bill #${b.bill_id} — ${b.description} (₹${b.net_amount})</option>`).join("");
    }
  }
  // auto-select patient when bill is chosen
  billSel?.addEventListener("change", () => {
    const opt = billSel.selectedOptions[0];
    if (opt && patSel) patSel.value = opt.dataset.pid;
  });
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    const body = Object.fromEntries(fd.entries());
    body.amount_paid = parseFloat(body.amount_paid);
    const res = await BillingAPI.recordPayment(body);
    if (res) {
      showToast(`Payment #${res.payment_id} recorded — receipt emailed`, "success");
      form.reset();
      loadPaymentsTable();
    }
  });
}

/** Load payments table (payment.html) */
async function loadPaymentsTable() {
  const tbody = document.getElementById("paymentsTableBody");
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="6"><div class="spinner"></div></td></tr>`;
  const data = await BillingAPI.listPayments();
  if (!data) return;
  tbody.innerHTML = "";
  (data.payments || []).forEach(p => {
    tbody.insertAdjacentHTML("beforeend", `<tr>
      <td>#${p.payment_id}</td>
      <td>${p.patient_name || "Patient #" + p.patient_id}</td>
      <td>Bill #${p.bill_id}</td>
      <td>₹${Number(p.amount_paid).toFixed(2)}</td>
      <td><span class="badge badge-info">${p.payment_method}</span></td>
      <td>${(p.payment_date || "").toString().slice(0,10)}</td>
    </tr>`);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  loadBillsTable();
  initCreateBillForm();
  loadPendingDues();
  initPaymentForm();
  loadPaymentsTable();
});

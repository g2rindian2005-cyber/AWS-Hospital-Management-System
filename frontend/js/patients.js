/* patients.js — logic for add-patient, view-patient, patient-history pages */

/** Load and render the patients table (view-patient.html) */
async function loadPatientsTable() {
  const tbody = document.getElementById("patientsTableBody");
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="6"><div class="spinner"></div></td></tr>`;
  const data = await PatientsAPI.list();
  if (!data) return;
  tbody.innerHTML = "";
  if (!data.patients?.length) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:rgba(255,255,255,0.4)">No patients found</td></tr>`;
    return;
  }
  data.patients.forEach(p => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>#${p.patient_id}</td>
      <td>${p.first_name} ${p.last_name}</td>
      <td>${p.date_of_birth || "—"}</td>
      <td><span class="badge ${p.gender === "Male" ? "badge-info" : "badge-purple"}">${p.gender}</span></td>
      <td>${p.phone}</td>
      <td>${p.blood_group || "—"}</td>`;
    tbody.appendChild(row);
  });
}

/** Handle add-patient form submit (add-patient.html) */
function initAddPatientForm() {
  const form = document.getElementById("addPatientForm");
  if (!form) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    const body = Object.fromEntries(fd.entries());
    const res = await PatientsAPI.create(body);
    if (res) {
      showToast(`Patient added successfully — ID: ${res.patient_id}`, "success");
      form.reset();
    }
  });
}

/** Render patient history with synchronised summary (patient-history.html) */
async function loadPatientHistory() {
  const select = document.getElementById("patientSelect");
  const container = document.getElementById("historyContent");
  if (!select || !container) return;

  // populate dropdown
  const data = await PatientsAPI.list();
  if (data?.patients) {
    select.innerHTML = '<option value="">-- Select Patient --</option>' +
      data.patients.map(p => `<option value="${p.patient_id}">${p.first_name} ${p.last_name} (#${p.patient_id})</option>`).join("");
  }

  select.addEventListener("change", async () => {
    const id = select.value;
    if (!id) { container.innerHTML = ""; return; }
    const detail = await PatientsAPI.get(id);
    if (!detail) return;
    const p = detail.patient;
    const s = detail.synchronised || {};
    container.innerHTML = `
      <div class="glass info-card fade-in" style="margin-bottom:20px;">
        <h3>${p.first_name} ${p.last_name} <span class="badge badge-info">#${p.patient_id}</span></h3>
        <p style="color:rgba(255,255,255,0.6)">${p.email || ""} • ${p.phone} • Blood: ${p.blood_group || "—"}</p>
      </div>
      <div class="stat-grid">
        <div class="glass stat-card gradient-orange">
          <div class="stat-icon">💰</div>
          <div class="stat-value">₹${Number(s.total_due || 0).toFixed(2)}</div>
          <div class="stat-label">Total Pending Dues</div>
        </div>
        <div class="glass stat-card gradient-blue">
          <div class="stat-icon">📋</div>
          <div class="stat-value">${(s.bills || []).length}</div>
          <div class="stat-label">Total Bills</div>
        </div>
        <div class="glass stat-card gradient-purple">
          <div class="stat-icon">🩺</div>
          <div class="stat-value">${(s.diseases || []).length}</div>
          <div class="stat-label">Disease Records</div>
        </div>
        <div class="glass stat-card gradient-green">
          <div class="stat-icon">👨‍⚕️</div>
          <div class="stat-value">${(s.assignments || []).length}</div>
          <div class="stat-label">Doctor Assignments</div>
        </div>
      </div>
      <div class="glass table-wrapper">
        <h3 style="color:#fff;margin-bottom:16px;">📋 Disease History</h3>
        <table>
          <thead><tr><th>Disease</th><th>Severity</th><th>Status</th><th>Diagnosed</th><th>Follow-up</th></tr></thead>
          <tbody>
            ${(s.diseases || []).map(d => `<tr>
              <td>${d.disease_name}</td>
              <td><span class="badge ${d.severity === "Critical" || d.severity === "Severe" ? "badge-danger" : d.severity === "Moderate" ? "badge-warning" : "badge-success"}">${d.severity}</span></td>
              <td><span class="badge badge-info">${d.status}</span></td>
              <td>${d.diagnosis_date}</td>
              <td>${d.follow_up_date || "—"}</td>
            </tr>`).join("") || `<tr><td colspan="5" style="text-align:center">No disease records</td></tr>`}
          </tbody>
        </table>
      </div>`;
  });
}

document.addEventListener("DOMContentLoaded", () => {
  loadPatientsTable();
  initAddPatientForm();
  loadPatientHistory();
});

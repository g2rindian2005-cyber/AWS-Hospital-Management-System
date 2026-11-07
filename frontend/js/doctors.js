/* doctors.js — logic for add-doctor, assign-doctor, appointments pages */

/** Load doctors table (add-doctor.html) */
async function loadDoctorsTable() {
  const tbody = document.getElementById("doctorsTableBody");
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="6"><div class="spinner"></div></td></tr>`;
  const data = await DoctorsAPI.list();
  if (!data) return;
  tbody.innerHTML = "";
  (data.doctors || []).forEach(d => {
    const availBadge = d.availability === "Available" ? "badge-success" : d.availability === "Busy" ? "badge-warning" : "badge-danger";
    tbody.insertAdjacentHTML("beforeend", `<tr>
      <td>#${d.doctor_id}</td>
      <td>${d.first_name} ${d.last_name}</td>
      <td>${d.specialization}</td>
      <td>${d.department || "—"}</td>
      <td>${d.phone}</td>
      <td><span class="badge ${availBadge}">${d.availability}</span></td>
    </tr>`);
  });
}

/** Init add-doctor form */
function initAddDoctorForm() {
  const form = document.getElementById("addDoctorForm");
  if (!form) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    const body = Object.fromEntries(fd.entries());
    body.consultation_fee = parseFloat(body.consultation_fee) || 0;
    const res = await DoctorsAPI.create(body);
    if (res) { showToast(`Doctor #${res.doctor_id} added`, "success"); form.reset(); loadDoctorsTable(); }
  });
}

/** Load assignments / appointments table (appointments.html) */
async function loadAssignmentsTable() {
  const tbody = document.getElementById("assignmentsTableBody");
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="7"><div class="spinner"></div></td></tr>`;
  const data = await DoctorsAPI.listAssignments();
  if (!data) return;
  tbody.innerHTML = "";
  (data.assignments || []).forEach(a => {
    const stBadge = a.status === "Active" ? "badge-success" : a.status === "Scheduled" ? "badge-info" :
                    a.status === "Completed" ? "badge-purple" : "badge-danger";
    tbody.insertAdjacentHTML("beforeend", `<tr>
      <td>#${a.assignment_id}</td>
      <td>${a.patient_name || "Patient #" + a.patient_id}</td>
      <td>${a.doctor_name || "Doctor #" + a.doctor_id}</td>
      <td>${a.specialization || "—"}</td>
      <td>${a.disease_name || "—"}</td>
      <td><span class="badge ${stBadge}">${a.status}</span></td>
      <td>${(a.appointment_date || "").toString().slice(0,16)}</td>
    </tr>`);
  });
}

/** Init assign-doctor form (assign-doctor.html) — needs patient, doctor, disease dropdowns */
async function initAssignDoctorForm() {
  const form = document.getElementById("assignDoctorForm");
  const patSel = document.getElementById("assignPatient");
  const docSel = document.getElementById("assignDoctor");
  const disSel = document.getElementById("assignDisease");
  if (!form) return;

  const [pData, dData, disData] = await Promise.all([PatientsAPI.list(), DoctorsAPI.list(), DiseasesAPI.list()]);
  if (pData?.patients && patSel) {
    patSel.innerHTML = '<option value="">-- Select Patient --</option>' +
      pData.patients.map(p => `<option value="${p.patient_id}">${p.first_name} ${p.last_name} (#${p.patient_id})</option>`).join("");
  }
  if (dData?.doctors && docSel) {
    docSel.innerHTML = '<option value="">-- Select Doctor --</option>' +
      dData.doctors.map(d => `<option value="${d.doctor_id}">${d.first_name} ${d.last_name} (${d.specialization})</option>`).join("");
  }
  if (disData?.diseases && disSel) {
    disSel.innerHTML = '<option value="">-- Select Disease (optional) --</option>' +
      disData.diseases.map(d => `<option value="${d.disease_id}">${d.disease_name} (Patient #${d.patient_id})</option>`).join("");
  }
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    const body = Object.fromEntries(fd.entries());
    const res = await DoctorsAPI.assign(body);
    if (res) {
      showToast(`Doctor assigned — confirmation emailed. Assignment #${res.assignment_id}`, "success");
      form.reset();
      loadAssignmentsTable();
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  loadDoctorsTable();
  initAddDoctorForm();
  loadAssignmentsTable();
  initAssignDoctorForm();
});

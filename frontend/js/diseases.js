/* diseases.js — logic for add-disease, disease-history pages */

/** Load diseases table (disease-history.html) */
async function loadDiseasesTable() {
  const tbody = document.getElementById("diseasesTableBody");
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="6"><div class="spinner"></div></td></tr>`;
  const data = await DiseasesAPI.list();
  if (!data) return;
  tbody.innerHTML = "";
  (data.diseases || []).forEach(d => {
    const sevBadge = d.severity === "Critical" || d.severity === "Severe" ? "badge-danger" :
                     d.severity === "Moderate" ? "badge-warning" : "badge-success";
    const stBadge = d.status === "Active" ? "badge-danger" : d.status === "Under Treatment" ? "badge-warning" :
                    d.status === "Chronic" ? "badge-purple" : "badge-success";
    tbody.insertAdjacentHTML("beforeend", `<tr>
      <td>#${d.disease_id}</td>
      <td>${d.patient_name || "Patient #" + d.patient_id}</td>
      <td>${d.disease_name}</td>
      <td><span class="badge ${sevBadge}">${d.severity}</span></td>
      <td><span class="badge ${stBadge}">${d.status}</span></td>
      <td>${(d.diagnosis_date || "").toString().slice(0,10)}</td>
    </tr>`);
  });
}

/** Init add-disease form with patient + doctor dropdowns */
async function initAddDiseaseForm() {
  const form = document.getElementById("addDiseaseForm");
  const patSel = document.getElementById("diseasePatient");
  const docSel = document.getElementById("diagnosedBy");
  if (!form) return;
  const [pData, dData] = await Promise.all([PatientsAPI.list(), DoctorsAPI.list()]);
  if (pData?.patients && patSel) {
    patSel.innerHTML = '<option value="">-- Select Patient --</option>' +
      pData.patients.map(p => `<option value="${p.patient_id}">${p.first_name} ${p.last_name} (#${p.patient_id})</option>`).join("");
  }
  if (dData?.doctors && docSel) {
    docSel.innerHTML = '<option value="">-- Select Doctor --</option>' +
      dData.doctors.map(d => `<option value="${d.doctor_id}">${d.first_name} ${d.last_name} (${d.specialization})</option>`).join("");
  }
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    const body = Object.fromEntries(fd.entries());
    const res = await DiseasesAPI.create(body);
    if (res) { showToast(`Disease record #${res.disease_id} created`, "success"); form.reset(); loadDiseasesTable(); }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  loadDiseasesTable();
  initAddDiseaseForm();
});

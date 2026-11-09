# Frontend Audit — AWS Hospital Management System (2026-11-09)
Repo: g2rindian2005-cyber/AWS-Hospital-Management-System, HEAD 83c129d "feat: complete premium frontend redesign"
Frontend: 14 HTML pages, css/style.css (1659 lines), js/{api,ui,patients,billing,diseases,doctors}.js (6207 lines total)

## P0 — Site is currently broken
- js/ui.js FAILS `node --check`: SyntaxError at line 461. buildPagination() has stray duplicated lines after its closing brace:
  `html += '</div>'; container.innerHTML = html; }` outside any function.
- Every page loads ui.js then calls initApp() inline. With ui.js unparseable, initApp / showToast / confirmDialog / buildPagination / statusBadge / initials / formatCurrency / formatDate are ALL undefined → every page's inline script crashes on load. Sidebar, topbar, toasts, pagination, modals all dead.

## API contract (MUST NOT CHANGE) — from js/api.js
Base: window.HMS_CONFIG.apiBase || https://abc123.execute-api.us-east-1.amazonaws.com/prod (placeholder)
Auth: localStorage hms_token, sent as Bearer. hms_user for display.
- Patients: GET/POST /patients, GET/PUT/DELETE /patients/{id} (get returns {patient, synchronised:{bills,diseases,assignments,total_due}})
- Billing: GET/POST /bills, GET/PUT/DELETE /bills/{id}, GET /bills/patient/{pid}, GET/POST /payments, GET /payments/patient/{pid}, GET /dues
- Diseases: GET/POST /diseases, GET/PUT/DELETE /diseases/{id}, GET /diseases/patient/{pid}, GET /diseases/active
- Doctors: GET/POST /doctors, GET/PUT/DELETE /doctors/{id}, GET/POST /assignments, GET/PUT/DELETE /assignments/{id}, GET /assignments/doctor/{did}, GET /assignments/patient/{pid}
Field names per module are built explicitly in each page's inline script (e.g. add-patient: first_name,last_name,date_of_birth,gender,blood_group,phone,email,address,emergency_contact,emergency_phone,medical_notes). Preserve exactly.

## Other findings
1. Dead/conflicting module JS: js/patients.js, billing.js, diseases.js, doctors.js are NOT loaded by any page. They target old element IDs (patientsTableBody vs real patientTable; createBillForm vs real modal saveBillBtn flow; paymentForm, assignDoctorForm vs real assignForm) and old FormData-by-name (pages use id-based fields, no name attributes). patients.js patient-history still renders the OLD dark glass theme + emoji icons. If ever loaded they'd break pages. → Rewrite them as correct, loadable modules OR remove after moving logic; do not leave conflicting duplicates.
2. Dashboard charts are HARDCODED fake data: revenue [42000,58000,47000,63000,72000,0], admissions [4,7,5,9,6,3,2]. Violates "no fake data". → Compute monthly revenue by grouping bills by bill_date; weekly admissions by grouping patients by registration_date.
3. Login is fake auth: hardcoded admin/admin123 in login.html, demo-token in localStorage, credentials printed on page. → Add AuthAPI.login() POST /auth/login storing the returned JWT; keep demo mode only behind explicit HMS_CONFIG.demoMode flag, remove printed credentials in production mode, remember-me = localStorage vs sessionStorage, forgot-password flow UI.
4. api.js mockFallback silently returns mock data on ANY network failure in production. → Gate behind HMS_CONFIG.devMock === true; otherwise show real error toast + return null.
5. sidebar.html is the legacy emoji sidebar, unused (ui.js injects its own). → Replace with the current MediCore markup or delete.
6. Sidebar spec gaps: No Reports page, no Settings page (topbar settings button is dead), sidebar not collapsible on desktop, Appointments only under Doctors. → Add reports.html (aggregates from existing APIs only) and settings.html (profile, API base URL config in localStorage, preferences), add Reports/Settings/Logout to sidebar, desktop collapse toggle.
7. Invoice: create-bill has itemised fees (consult/medicine/lab/treatment/other) + invoice modal + window.print with @media print CSS — good base. Invoice modal still uses an emoji in logo; PDF = print-to-PDF (no JS PDF lib). Keep, polish, remove emoji.
8. What is already GOOD and must be preserved: all 14 pages have rich inline logic — search/filter/pagination/edit-modal/delete-with-confirmDialog for patients, diseases, doctors/appointments, billing; patient-history profile layout; add-patient checklist + PID preview; style.css is a proper light Inter/blue/teal design system (1659 lines) with badges, cards, modals, skeletons, invoice + print styles.

## Redesign v2 plan (branch: redesign/premium-v2)
1. Fix ui.js syntax error; add desktop sidebar collapse; add Reports/Settings nav; keep all helper signatures identical.
2. api.js: devMock gating, AuthAPI (JWT), keep every endpoint/field identical.
3. Login: real JWT attempt first, demo only if configured, remember-me storage split, no printed credentials by default.
4. Dashboard: real-data charts (monthly revenue from bills, weekly admissions from patients, today's appointments count from assignments filtered by date).
5. Replace dead module JS with correct versions matching real page IDs, or consolidate — no conflicting DOMContentLoaded auto-runs with wrong IDs.
6. New pages: reports.html, settings.html using existing APIs only.
7. Polish: remove remaining emoji (invoice logo, sidebar.html), loading skeletons on tables, empty states already present.
8. Verify: node --check all JS, serve locally, smoke-test every page with mock data, confirm no API contract changes (diff api.js endpoints).
9. Push via GitHub MCP to branch redesign/premium-v2 and open PR — do NOT push straight to main.

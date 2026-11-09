/* ============================================================
   MediCore HMS — Shared UI Utilities
   Sidebar injection, Toast, Confirm Dialog, Helpers
   ============================================================ */

/* ── Path prefix: auto-detected from current page depth ───── */
function _prefix() {
  // If pathname has 2+ slashes (e.g. /patients/view-patient.html) we need ../
  const parts = window.location.pathname.split('/').filter(Boolean);
  return parts.length >= 2 ? '../' : '';
}

/* ── Build sidebar HTML with correct relative paths ──────── */
function buildSidebarHTML() {
  const p = _prefix();
  return `
<div class="sidebar-header">
  <div class="sidebar-logo-icon">
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
         fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
    </svg>
  </div>
  <span class="sidebar-brand-name">Medi<span>Core</span> HMS</span>
</div>

<nav class="sidebar-nav">
  <div class="nav-group">
    <span class="nav-group-label">Overview</span>
    <a href="${p}dashboard.html" class="nav-item" data-page="dashboard">
      <span class="nav-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/>
          <rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/>
        </svg>
      </span>
      Dashboard
    </a>
  </div>

  <div class="nav-group">
    <span class="nav-group-label">Patients</span>
    <a href="${p}patients/view-patient.html" class="nav-item" data-page="view-patient">
      <span class="nav-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
          <path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
        </svg>
      </span>
      All Patients
    </a>
    <a href="${p}patients/add-patient.html" class="nav-item" data-page="add-patient">
      <span class="nav-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
          <line x1="19" x2="19" y1="8" y2="14"/><line x1="22" x2="16" y1="11" y2="11"/>
        </svg>
      </span>
      Register Patient
    </a>
    <a href="${p}patients/patient-history.html" class="nav-item" data-page="patient-history">
      <span class="nav-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/><line x1="16" x2="8" y1="13" y2="13"/>
          <line x1="16" x2="8" y1="17" y2="17"/><line x1="10" x2="8" y1="9" y2="9"/>
        </svg>
      </span>
      Patient History
    </a>
  </div>

  <div class="nav-group">
    <span class="nav-group-label">Billing</span>
    <a href="${p}billing/create-bill.html" class="nav-item" data-page="create-bill">
      <span class="nav-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/>
        </svg>
      </span>
      Create Bill
    </a>
    <a href="${p}billing/payment.html" class="nav-item" data-page="payment">
      <span class="nav-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="12" x2="12" y1="1" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
        </svg>
      </span>
      Payments
    </a>
    <a href="${p}billing/pending-dues.html" class="nav-item" data-page="pending-dues">
      <span class="nav-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
          <path d="M12 9v4"/><path d="M12 17h.01"/>
        </svg>
      </span>
      Pending Dues
    </a>
  </div>

  <div class="nav-group">
    <span class="nav-group-label">Clinical</span>
    <a href="${p}diseases/disease-history.html" class="nav-item" data-page="disease-history">
      <span class="nav-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M8 2v4"/><path d="M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/>
          <path d="M3 10h18"/><path d="M8 14h.01"/><path d="M12 14h.01"/><path d="M16 14h.01"/>
          <path d="M8 18h.01"/><path d="M12 18h.01"/><path d="M16 18h.01"/>
        </svg>
      </span>
      Diseases
    </a>
    <a href="${p}diseases/add-disease.html" class="nav-item" data-page="add-disease">
      <span class="nav-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <path d="M8 12h8"/><path d="M12 8v8"/>
        </svg>
      </span>
      Add Disease
    </a>
  </div>

  <div class="nav-group">
    <span class="nav-group-label">Doctors</span>
    <a href="${p}doctors/add-doctor.html" class="nav-item" data-page="add-doctor">
      <span class="nav-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 9h18v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9Z"/>
          <path d="m3 9 2.45-4.9A2 2 0 0 1 7.24 3h9.52a2 2 0 0 1 1.8 1.1L21 9"/>
          <path d="M12 3v6"/><path d="M9 12h6"/><path d="M12 12v6"/>
        </svg>
      </span>
      Add Doctor
    </a>
    <a href="${p}doctors/assign-doctor.html" class="nav-item" data-page="assign-doctor">
      <span class="nav-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
          <circle cx="9" cy="7" r="4"/>
          <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
        </svg>
      </span>
      Assign Doctor
    </a>
    <a href="${p}doctors/appointments.html" class="nav-item" data-page="appointments">
      <span class="nav-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect width="18" height="18" x="3" y="4" rx="2"/><path d="M16 2v4"/><path d="M8 2v4"/>
          <path d="M3 10h18"/><path d="m9 16 2 2 4-4"/>
        </svg>
      </span>
      Appointments
    </a>
  </div>
</nav>

<div class="sidebar-footer">
  <div class="sidebar-user">
    <div class="sidebar-user-avatar" id="sidebarUserAvatar">A</div>
    <div class="sidebar-user-info">
      <div class="sidebar-user-name" id="sidebarUserName">Administrator</div>
      <div class="sidebar-user-role">Hospital Admin</div>
    </div>
  </div>
  <a href="${p}login.html" class="nav-item" id="logoutBtn" style="color:var(--red-600); margin-top:4px;">
    <span class="nav-icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
           fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
        <polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/>
      </svg>
    </span>
    Logout
  </a>
</div>`;
}

/* ── Topbar HTML ──────────────────────────────────────────── */
function buildTopbar(title, subtitle) {
  const p = _prefix();
  return `
  <button class="mobile-menu-btn" id="mobileMenuBtn">
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
         fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/>
      <line x1="4" x2="20" y1="18" y2="18"/>
    </svg>
  </button>
  <div class="topbar-left">
    <div>
      <div class="topbar-title">${title}</div>
      ${subtitle ? `<div class="topbar-breadcrumb"><a href="${p}dashboard.html">Dashboard</a><span>›</span><span>${subtitle}</span></div>` : ''}
    </div>
  </div>
  <div class="topbar-right">
    <div class="topbar-date" id="topbarDate"></div>
    <button class="topbar-btn" title="Notifications">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
           fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/>
        <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>
      </svg>
      <span class="dot"></span>
    </button>
    <button class="topbar-btn" title="Settings">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
           fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>
        <circle cx="12" cy="12" r="3"/>
      </svg>
    </button>
  </div>`;
}

/* ── App init ─────────────────────────────────────────────── */
function initApp(opts = {}) {
  const { page = '', title = 'Dashboard', subtitle = '' } = opts;

  /* Auth guard */
  if (!localStorage.getItem('hms_token')) {
    window.location.href = resolveRoot('login.html');
    return;
  }

  /* Inject sidebar overlay */
  const overlay = document.createElement('div');
  overlay.className = 'sidebar-overlay';
  overlay.id = 'sidebarOverlay';
  document.body.prepend(overlay);

  /* Inject sidebar */
  let sidebar = document.querySelector('.sidebar');
  if (!sidebar) {
    sidebar = document.createElement('aside');
    sidebar.className = 'sidebar';
    document.body.prepend(sidebar);
  }
  sidebar.innerHTML = buildSidebarHTML();

  /* Inject topbar */
  let topbar = document.querySelector('.topbar');
  if (!topbar) {
    topbar = document.createElement('header');
    topbar.className = 'topbar';
    document.body.prepend(topbar);
  }
  topbar.innerHTML = buildTopbar(title, subtitle);

  /* Inject toast container */
  if (!document.getElementById('toast-container')) {
    const tc = document.createElement('div');
    tc.id = 'toast-container';
    document.body.appendChild(tc);
  }

  /* Active nav item — resolve paths to filename */
  const filename = window.location.pathname.split('/').pop().replace('.html','');
  const active = sidebar.querySelector(`[data-page="${filename}"]`)
               || sidebar.querySelector(`[data-page="${page}"]`);
  if (active) active.classList.add('active');

  /* User display */
  const u = localStorage.getItem('hms_user') || 'Admin';
  const el = document.getElementById('sidebarUserName');
  if (el) el.textContent = u;
  const av = document.getElementById('sidebarUserAvatar');
  if (av) av.textContent = u[0].toUpperCase();

  /* Logout */
  document.getElementById('logoutBtn')?.addEventListener('click', () => {
    localStorage.removeItem('hms_token');
    localStorage.removeItem('hms_user');
  });

  /* Mobile toggle */
  document.getElementById('mobileMenuBtn')?.addEventListener('click', () => {
    sidebar.classList.toggle('open');
    overlay.classList.toggle('show');
  });
  overlay.addEventListener('click', () => {
    sidebar.classList.remove('open');
    overlay.classList.remove('show');
  });

  /* Date */
  const dateEl = document.getElementById('topbarDate');
  if (dateEl) {
    dateEl.textContent = new Date().toLocaleDateString('en-IN', {
      weekday: 'short', year: 'numeric', month: 'short', day: 'numeric'
    });
  }
}

/* ── Resolve root path (works from sub-dirs) ──────────────── */
function resolveRoot(path) {
  return _prefix() + path;
}

/* ── Toast notification ───────────────────────────────────── */
function showToast(msg, type = 'info', title = null) {
  const icons = {
    success: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>`,
    error:   `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" x2="6" y1="6" y2="18"/><line x1="6" x2="18" y1="6" y2="18"/></svg>`,
    warning: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>`,
    info:    `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>`,
  };
  const titles = { success: 'Success', error: 'Error', warning: 'Warning', info: 'Info' };

  let tc = document.getElementById('toast-container');
  if (!tc) {
    tc = document.createElement('div');
    tc.id = 'toast-container';
    document.body.appendChild(tc);
  }

  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.innerHTML = `
    <div class="toast-icon">${icons[type] || icons.info}</div>
    <div class="toast-body">
      <div class="toast-title">${title || titles[type]}</div>
      <div class="toast-msg">${msg}</div>
    </div>`;
  tc.appendChild(t);

  setTimeout(() => {
    t.classList.add('removing');
    setTimeout(() => t.remove(), 350);
  }, 3800);
}

/* ── Confirm dialog ───────────────────────────────────────── */
function confirmDialog(opts = {}) {
  const {
    title   = 'Are you sure?',
    message = 'This action cannot be undone.',
    confirmText = 'Confirm',
    cancelText  = 'Cancel',
    type = 'danger'
  } = opts;

  return new Promise((resolve) => {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay show';
    overlay.innerHTML = `
      <div class="modal modal-sm fade-in">
        <div class="modal-body" style="padding-top:32px;">
          <div class="confirm-modal-icon ${type}">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
                 fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
              <path d="M12 9v4"/><path d="M12 17h.01"/>
            </svg>
          </div>
          <div class="confirm-modal-title">${title}</div>
          <div class="confirm-modal-text">${message}</div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline btn-sm" id="confirmCancel">${cancelText}</button>
          <button class="btn btn-danger btn-sm" id="confirmOk">${confirmText}</button>
        </div>
      </div>`;
    document.body.appendChild(overlay);

    overlay.querySelector('#confirmCancel').addEventListener('click', () => {
      overlay.remove(); resolve(false);
    });
    overlay.querySelector('#confirmOk').addEventListener('click', () => {
      overlay.remove(); resolve(true);
    });
  });
}

/* ── Avatar initials helper ───────────────────────────────── */
function initials(name) {
  return (name || '?').split(' ').slice(0,2).map(w => w[0]).join('').toUpperCase();
}

/* ── Format currency ──────────────────────────────────────── */
function formatCurrency(n) {
  return '₹' + Number(n || 0).toLocaleString('en-IN');
}

/* ── Format date ──────────────────────────────────────────── */
function formatDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-IN', { day:'2-digit', month:'short', year:'numeric' });
}

/* ── Skeleton rows ────────────────────────────────────────── */
function skeletonRows(cols, count = 5) {
  return Array.from({ length: count }, () =>
    `<tr>${Array.from({ length: cols }, () =>
      `<td><div class="skeleton skeleton-text" style="width:${60+Math.random()*30}%"></div></td>`
    ).join('')}</tr>`
  ).join('');
}

/* ── Status badge helper ──────────────────────────────────── */
function statusBadge(status) {
  const map = {
    'Paid':             'badge-success',
    'Active':           'badge-success',
    'Available':        'badge-success',
    'Recovered':        'badge-success',
    'Partial':          'badge-warning',
    'Scheduled':        'badge-info',
    'Under Treatment':  'badge-info',
    'Pending':          'badge-danger',
    'Busy':             'badge-warning',
    'On Leave':         'badge-gray',
    'Chronic':          'badge-purple',
    'Mild':             'badge-teal',
    'Moderate':         'badge-warning',
    'Severe':           'badge-danger',
  };
  const cls = map[status] || 'badge-gray';
  return `<span class="badge ${cls}"><span class="badge-dot"></span>${status}</span>`;
}

/* ── Pagination helper ────────────────────────────────────── */
const _paginationCbs = {};
function buildPagination(container, total, page, perPage, onPage) {
  const pages = Math.ceil(total / perPage);
  if (pages <= 1) { container.innerHTML = ''; return; }
  const start = (page - 1) * perPage + 1;
  const end   = Math.min(page * perPage, total);

  /* Store callback in registry so it's accessible from onclick */
  const cbKey = '_pagCb_' + container.id;
  window[cbKey] = onPage;

  let html = `<span class="pagination-info">Showing ${start}–${end} of ${total}</span><div class="pagination-controls">`;
  html += `<button class="page-btn" ${page===1?'disabled':''} onclick="${cbKey}(${page-1})">‹</button>`;
  for (let i = 1; i <= pages; i++) {
    if (i===1 || i===pages || Math.abs(i-page)<=1)
      html += `<button class="page-btn${i===page?' active':''}" onclick="${cbKey}(${i})">${i}</button>`;
    else if (Math.abs(i-page)===2)
      html += `<span class="page-btn" style="pointer-events:none">…</span>`;
  }
  html += `<button class="page-btn" ${page===pages?'disabled':''} onclick="${cbKey}(${page+1})">›</button>`;
  html += '</div>';
  container.innerHTML = html;
}
  html += '</div>';
  container.innerHTML = html;
}

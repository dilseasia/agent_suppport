const API_BASE = "http://localhost:8000"; // Update if your backend runs elsewhere

// Elements
const createBtn = document.getElementById('createBtn');
const createBtn2 = document.getElementById('createBtn2');
const connectorModal = document.getElementById('connectorModal');
const connectorsGrid = document.getElementById('connectorsGrid');
const modalSearch = document.getElementById('modalSearch');
const modalCategories = document.getElementById('modalCategories');
const closeConnector = document.getElementById('closeConnector');
const closeConnector2 = document.getElementById('closeConnector2');

const authTableBody = document.getElementById('authTableBody');
const emptyState = document.getElementById('emptyState');
const searchInput = document.getElementById('searchInput');
const categorySelect = document.getElementById('categorySelect');
const refreshBtn = document.getElementById('refreshBtn');

const confirmDialog = document.getElementById('confirmDialog');
const confirmMessage = document.getElementById('confirmMessage');
const confirmYes = document.getElementById('confirmYes');
const confirmNo = document.getElementById('confirmNo');

const toast = document.getElementById('toast');

let connectorsCache = [];
let authConfigsCache = [];

// Helpers
function showToast(msg, timeout = 3000) {
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), timeout);
}

function showModal(modal) {
  modal.setAttribute('aria-hidden','false');
  modal.style.display='flex';
}

function hideModal(modal) {
  modal.setAttribute('aria-hidden','true');
  modal.style.display='none';
}

function confirmAction(message) {
  return new Promise(resolve => {
    confirmMessage.textContent = message;
    confirmDialog.setAttribute('aria-hidden','false');
    confirmDialog.style.display='flex';
    const onYes = () => { clean(); resolve(true); };
    const onNo = () => { clean(); resolve(false); };
    confirmYes.addEventListener('click', onYes, {once:true});
    confirmNo.addEventListener('click', onNo, {once:true});
    function clean() {
      confirmDialog.setAttribute('aria-hidden','true');
      confirmDialog.style.display='none';
    }
  });
}

function debounce(fn, wait=300){
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(()=>fn(...args), wait); };
}

// Fetch connectors
async function loadConnectors({search='', category=''} = {}) {
  connectorsGrid.innerHTML = `<div class="muted" style="padding:18px">Loading connectors…</div>`;
  try {
    const payload = { search_term: search };
    const r = await fetch(`${API_BASE}/connectors/search-toolkits`, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(payload)
    });
    if (!r.ok) throw new Error(await r.text());
    const data = await r.json();
    connectorsCache = Array.isArray(data) ? data : [];
    if (category) {
      connectorsCache = connectorsCache.filter(c => (c.category || '').toLowerCase() === category.toLowerCase());
    }
    renderConnectorCards(connectorsCache);
  } catch (err) {
    connectorsGrid.innerHTML = `<div class="muted" style="padding:18px">Could not load connectors — ${err.message}</div>`;
  }
}

function renderConnectorCards(list) {
  if (!list || list.length === 0) {
    connectorsGrid.innerHTML = `<div class="muted" style="padding:18px">No connectors found.</div>`;
    return;
  }
  connectorsGrid.innerHTML = '';
  list.forEach(c => {
    const card = document.createElement('div');
    card.className = 'card';
    const iconBG = c.color || '#2563eb';
    const iconText = (c.name || 'C').split(' ').map(s=>s[0]).slice(0,2).join('');
    card.innerHTML = `
      <div class="icon" style="background:${iconBG}">${iconText}</div>
      <div style="flex:1">
        <h4>${c.name || c.id}</h4>
        <p>${c.description || c.summary || c.category || ''}</p>
      </div>
      <div>
        <button class="btn primary small" data-id="${c.slug || c.id}">Connect</button>
      </div>
    `;
    card.querySelector('button')?.addEventListener('click', () => createAuthConfig(c.slug || c.id));
    connectorsGrid.appendChild(card);
  });
}

// ✅ Create auth config
async function createAuthConfig(toolkitSlug) {
  try {
    const createPayload = { toolkit_slug: toolkitSlug, auth_type: "OAUTH2" };
    const r = await fetch(`${API_BASE}/auth/create-auth-config`, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(createPayload)
    });
    const created = await r.json();
    if (!r.ok) throw new Error(created?.detail || JSON.stringify(created));
    showToast('Auth config created.');
    hideModal(connectorModal);
    loadAuthConfigs();
  } catch (err) {
    showToast(`Error: ${err.message}`);
    console.error(err);
  }
}

// Load auth configs
async function loadAuthConfigs() {
  authTableBody.innerHTML = `<tr><td colspan="8" style="padding:18px">Loading…</td></tr>`;
  try {
    const r = await fetch(`${API_BASE}/auth/list-auth-configs`);
    if (!r.ok) throw new Error(await r.text());
    const data = await r.json();
    authConfigsCache = data.items || [];
    renderAuthTable(authConfigsCache);
  } catch (err) {
    authTableBody.innerHTML = `<tr><td colspan="8" style="padding:18px">Failed to load: ${err.message}</td></tr>`;
  }
}

// ✅ Render Auth Table with Connect/Delete/Enable/Disable
function renderAuthTable(list) {
  if (!list || list.length === 0) {
    authTableBody.innerHTML = '';
    emptyState.hidden = false;
    return;
  }
  emptyState.hidden = true;
  authTableBody.innerHTML = '';
  list.forEach(cfg => {
    const id = cfg.nanoid || cfg.id;
    if (!id) return;

    const name = cfg.name || cfg.toolkit?.slug || id;
    const connCount = cfg.connections_count || 0;
    const authType = cfg.auth_scheme || 'OAUTH2';
    const lastUpdated = cfg.updated_at ? new Date(cfg.updated_at).toLocaleString() : '-';
    const status = cfg.status || 'ENABLED';

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${name}</td>
      <td>${cfg.toolkit?.slug || '-'}</td>
      <td>${connCount}</td>
      <td><span class="badge type">${authType}</span></td>
      <td>${lastUpdated}</td>
      <td><span class="badge ${status === 'ENABLED' ? 'success' : 'danger'}">${status}</span></td>
      <td>
        <button class="btn success small" data-connect="${id}">⚡ Connect</button>
        <button class="btn warning small" data-toggle="${id}">${status === 'ENABLED' ? 'Disable' : 'Enable'}</button>
        <button class="btn danger small" data-delete="${id}">🗑 Delete</button>
      </td>
    `;

    // Connect button → open Google OAuth and refresh count
    tr.querySelector('[data-connect]')?.addEventListener('click', async () => {
      try {
        const r = await fetch(`${API_BASE}/auth/connect-auth-config`, {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify({ auth_config_id: id })
        });
        const resp = await r.json();
        if (!r.ok) throw new Error(resp?.detail || JSON.stringify(resp));
        if (resp.redirect_url) {
          window.open(resp.redirect_url, '_blank');
        }
        // ✅ Refresh to update connection count
        setTimeout(loadAuthConfigs, 2000);
      } catch (err) {
        showToast('Error: ' + err.message);
      }
    });

    // ✅ Status toggle button → Enable/Disable in place
    tr.querySelector('[data-toggle]')?.addEventListener('click', async (e) => {
      const btn = e.currentTarget;
      const statusBadge = tr.querySelector('td:nth-child(6) .badge');
      const currentStatus = statusBadge.textContent.trim();
      const newStatus = currentStatus === 'ENABLED' ? 'DISABLED' : 'ENABLED';
      try {
        const r = await fetch(`${API_BASE}/auth/set-auth-config-status`, {
          method: 'PATCH',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify({ nanoid: id, status: newStatus })
        });
        const resp = await r.json();
        if (!r.ok) throw new Error(resp?.detail || JSON.stringify(resp));
        // update UI instantly
        statusBadge.textContent = newStatus;
        statusBadge.className = `badge ${newStatus === 'ENABLED' ? 'success' : 'danger'}`;
        btn.textContent = newStatus === 'ENABLED' ? 'Disable' : 'Enable';
        showToast(`Status updated to ${newStatus}`);
      } catch(err) {
        showToast('Error: ' + err.message);
      }
    });

    // Delete button
    tr.querySelector('[data-delete]')?.addEventListener('click', async () => {
      const confirmed = await confirmAction('Delete this auth config?');
      if (!confirmed) return;
      try {
        const res = await fetch(`${API_BASE}/auth/delete-auth-config/${id}`, {
          method: 'DELETE'
        });
        if (!res.ok) throw new Error(await res.text());
        showToast('Deleted successfully.');
        loadAuthConfigs();
      } catch(err) {
        showToast('Error: ' + err.message);
      }
    });

    authTableBody.appendChild(tr);
  });
}

// UI wiring
createBtn.addEventListener('click', () => { showModal(connectorModal); loadConnectors(); });
createBtn2?.addEventListener('click', () => { showModal(connectorModal); loadConnectors(); });
closeConnector.addEventListener('click', () => hideModal(connectorModal));
closeConnector2.addEventListener('click', () => hideModal(connectorModal));
refreshBtn.addEventListener('click', () => loadAuthConfigs());

modalCategories.querySelectorAll('.chip').forEach(chip => {
  chip.addEventListener('click', () => {
    modalCategories.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    loadConnectors({category: chip.dataset.cat || ''});
  });
});

modalSearch.addEventListener('input', debounce(() =>
  loadConnectors({
    search: modalSearch.value,
    category: document.querySelector('.chip.active')?.dataset?.cat || ''
  }), 300
));

searchInput.addEventListener('input', debounce(() => loadAuthConfigs(), 400));
categorySelect.addEventListener('change', () => loadAuthConfigs());

document.addEventListener('DOMContentLoaded', () => {
  loadAuthConfigs();
});

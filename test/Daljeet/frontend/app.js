const API_BASE = "http://localhost:8000"; // backend

// Default static IDs (hidden from user)
const ORG_ID = "org_123";   
const USER_ID = "user_123"; 

// Elements
const createBtn = document.getElementById('createBtn');
const connectorsGrid = document.getElementById('connectorsGrid');
const connectorModal = document.getElementById('connectorModal');
const closeConnector = document.getElementById('closeConnector');
const authTableBody = document.getElementById('authTableBody');
const emptyState = document.getElementById('emptyState');
const refreshBtn = document.getElementById('refreshBtn');
const toast = document.getElementById('toast');
const searchConnectorInput = document.getElementById('searchConnector');

// Toast helper
function showToast(msg) {
  toast.textContent = msg;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 3000);
}

// Modal helpers
function showModal(modal) { modal.style.display = "flex"; }
function hideModal(modal) { modal.style.display = "none"; }

// Load connectors
async function loadConnectors(search = "") {
  connectorsGrid.innerHTML = `<p>Loading...</p>`;
  try {
    const r = await fetch(`${API_BASE}/routes/toolkits/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ search_term: search })
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || "Error loading connectors");
    renderConnectorCards(data.items || []);
  } catch (err) {
    connectorsGrid.innerHTML = `<p style="color:red">${err.message}</p>`;
  }
}

// Render connector cards
function renderConnectorCards(connectors) {
  connectorsGrid.innerHTML = "";
  connectors.forEach(c => {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <img src="${c.logo || 'https://via.placeholder.com/80'}" alt="${c.name}">
      <h4>${c.name || c.slug}</h4>
      <p style="font-size:12px;color:#555;">${c.description || ""}</p>
      <button class="btn primary" data-slug="${c.slug}">Create</button>
    `;
    card.querySelector("button").addEventListener("click", () => createAuthConfig(c.slug));
    connectorsGrid.appendChild(card);
  });
}

// Search connectors
searchConnectorInput?.addEventListener("input", (e) => loadConnectors(e.target.value));

// Create auth config
async function createAuthConfig(toolkitSlug) {
  try {
    const r = await fetch(`${API_BASE}/routes/create-auth-config`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        organization_id: ORG_ID,
        toolkit_slug: toolkitSlug,
        auth_type: "OAUTH2",
        user_id: USER_ID
      })
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || "Failed");
    showToast("Auth config created!");
    hideModal(connectorModal);
    loadAuthConfigs();
  } catch (err) {
    showToast(err.message);
  }
}

// Load auth configs
async function loadAuthConfigs() {
  authTableBody.innerHTML = `<tr><td colspan="5">Loading...</td></tr>`;
  try {
    const r = await fetch(`${API_BASE}/routes/list-auth-configs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ organization_id: ORG_ID })
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || "Error");
    renderAuthTable(data.items || []);
  } catch (err) {
    authTableBody.innerHTML = `<tr><td colspan="5" style="color:red">${err.message}</td></tr>`;
  }
}

// Render auth table
function renderAuthTable(list) {
  if (!list.length) {
    authTableBody.innerHTML = "";
    emptyState.style.display = "block";
    return;
  }
  emptyState.style.display = "none";
  authTableBody.innerHTML = "";
  list.forEach(cfg => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${cfg.name || cfg.auth_config_id}</td>
      <td>${cfg.toolkit_slug || "-"}</td>
      <td>${cfg.connections_count || 0}</td>
      <td>${cfg.status}</td>
      <td>
        <button class="btn small success" data-connect="${cfg.auth_config_id}">Connect</button>
        <button class="btn small warning" data-toggle="${cfg.auth_config_id}">${cfg.status === "ENABLED" ? "Disable" : "Enable"}</button>
        <button class="btn small danger" data-delete="${cfg.auth_config_id}">Delete</button>
      </td>
    `;
    tr.querySelector("[data-connect]").addEventListener("click", () => connectAuth(cfg.auth_config_id));
    tr.querySelector("[data-toggle]").addEventListener("click", () => toggleStatusInPlace(tr, cfg.auth_config_id));
    tr.querySelector("[data-delete]").addEventListener("click", () => deleteAuthConfig(cfg.auth_config_id));
    authTableBody.appendChild(tr);
  });
}

// Connect Gmail
async function connectAuth(authConfigId) {
  try {
    const r = await fetch(`${API_BASE}/routes/gmail/connect`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        organization_id: ORG_ID,
        auth_config_id: authConfigId,
        user_id: USER_ID
      })
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || "Failed");
    if (data.redirect_url) window.open(data.redirect_url, "_blank");
    showToast("Connect flow started!");
  } catch (err) {
    showToast(err.message);
  }
}

// Toggle status in-place
async function toggleStatusInPlace(row, authConfigId) {
  try {
    const currentStatus = row.querySelector("td:nth-child(4)").textContent;
    const newStatus = currentStatus === "ENABLED" ? "DISABLED" : "ENABLED";
    const r = await fetch(`${API_BASE}/routes/set-status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nanoid: authConfigId, status: newStatus })
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || "Failed");
    row.querySelector("td:nth-child(4)").textContent = newStatus;
    row.querySelector(`[data-toggle="${authConfigId}"]`).textContent = newStatus === "ENABLED" ? "Disable" : "Enable";
    showToast(`Status updated to ${newStatus}`);
  } catch (err) {
    showToast(err.message);
  }
}

// Delete config
async function deleteAuthConfig(authConfigId) {
  try {
    const r = await fetch(`${API_BASE}/routes/delete-auth-config`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        organization_id: ORG_ID,
        nanoid: authConfigId
      })
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || "Failed");
    showToast("Deleted!");
    loadAuthConfigs();
  } catch (err) {
    showToast(err.message);
  }
}

// Events
createBtn.addEventListener("click", () => { showModal(connectorModal); loadConnectors(); });
closeConnector.addEventListener("click", () => hideModal(connectorModal));
refreshBtn.addEventListener("click", () => loadAuthConfigs());

// Init
document.addEventListener("DOMContentLoaded", () => { loadAuthConfigs(); });

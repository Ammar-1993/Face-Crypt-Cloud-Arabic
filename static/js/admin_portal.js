const API_BASE = "http://127.0.0.1:8080";
function show(elem) {
  elem.classList.remove("hidden");
}
function hide(elem) {
  elem.classList.add("hidden");
}
function setText(id, msg) {
  document.getElementById(id).innerHTML = msg;
}

let allAuditLogs = [];
let currentPage = 1;
const rowsPerPage = 10;

async function adminLogin() {
  const password = document.getElementById("adminPassword").value;
  const res = await fetch(`${API_BASE}/admin/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  });
  const data = await res.json();
  if (res.ok) {
    setText(
      "loginMessage",
      `<span class="text-success">✅ ${data.message}</span>`
    );
    hide(document.getElementById("loginSection"));
    show(document.getElementById("adminPanel"));
    await loadUsers();
    await fetchAuditLogs();
    await refreshStats();
  } else {
    setText(
      "loginMessage",
      `<span class="text-danger">❌ ${data.error}</span>`
    );
  }
}

async function addUser() {
  const userId = document.getElementById("newUserId").value.trim();
  if (!userId) {
    setText(
      "addUserMessage",
      `<span class="text-danger">❌ Please enter a User ID.</span>`
    );
    return;
  }

  const name = document.getElementById("newUserName").value.trim();
  if (!name) {
    setText(
      "addUserMessage",
      `<span class="text-danger">❌ Please enter the Name.</span>`
    );
    return;
  }

  const email = document.getElementById("newUserEmail").value.trim();
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!email) {
    setText(
      "addUserMessage",
      `<span class="text-danger">❌ Please enter the Email address.</span>`
    );
    return;
  }
  if (!emailPattern.test(email)) {
    setText(
      "addUserMessage",
      `<span class="text-danger">❌ Please enter a valid Email address.</span>`
    );
    return;
  }

  const image = document.getElementById("newUserImage").files[0];
  if (!image) {
    setText(
      "addUserMessage",
      `<span class="text-danger">❌ Please choose an Image.</span>`
    );
    return;
  }

  const formData = new FormData();
  formData.append("user_id", userId);
  formData.append("name", name);
  formData.append("email", email);
  formData.append("image", image);

  const res = await fetch(`${API_BASE}/admin/add_user`, {
    method: "POST",
    body: formData,
  });
  const data = await res.json();
  if (res.ok) {
    setText(
      "addUserMessage",
      `<span class="text-success">✅ ${data.message}</span>`
    );
    await loadUsers();
  } else {
    setText(
      "addUserMessage",
      `<span class="text-danger">❌ ${data.error}</span>`
    );
  }
}

async function loadUsers() {
  const select = document.getElementById("deleteUserId");
  select.innerHTML = "";
  const res = await fetch(`${API_BASE}/admin/list_users`);
  const data = await res.json();

  data.users.forEach((user) => {
    const option = document.createElement("option");
    option.value = user.id;
    option.text = `${user.name} (${user.id})`;
    select.add(option);
  });
}

async function deleteUser() {
  const userId = document.getElementById("deleteUserId").value;
  if (!userId) {
    setText(
      "deleteUserMessage",
      `<span class="text-danger">❌ Please select a user to delete.</span>`
    );
    return;
  }

  const res = await fetch(`${API_BASE}/admin/delete_user`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId }),
  });

  const data = await res.json();
  if (res.ok) {
    setText(
      "deleteUserMessage",
      `<span class="text-success">✅ ${data.message}</span>`
    );
    await loadUsers();
  } else {
    setText(
      "deleteUserMessage",
      `<span class="text-danger">❌ ${data.error}</span>`
    );
  }
}

async function fetchAuditLogs() {
  const res = await fetch(`${API_BASE}/admin/audit_logs`);
  const data = await res.json();

  // 🟢 Sort descending by timestamp
  allAuditLogs = data.logs.sort((a, b) => {
    return new Date(b.timestamp) - new Date(a.timestamp);
  });

  currentPage = 1;
  renderAuditLogs(allAuditLogs);
}

function renderAuditLogs(logs) {
  const table = document.getElementById("auditLogsTable");
  const pageIndicator = document.getElementById("pageIndicator");
  const totalPages = Math.ceil(logs.length / rowsPerPage);

  const start = (currentPage - 1) * rowsPerPage;
  const end = start + rowsPerPage;
  const pageData = logs.slice(start, end);

  pageIndicator.textContent = `Page ${currentPage} of ${totalPages}`;

  if (!pageData || pageData.length === 0) {
    table.innerHTML =
      '<tr><td colspan="4" class="text-center">No logs found.</td></tr>';
    return;
  }

  table.innerHTML = "";
  pageData.forEach((log) => {
    const row = document.createElement("tr");

    // ✨ زر الفك
    let statusCell = log.status || "";
    if (log.status === "blocked") {
      statusCell += ` <button class="btn btn-sm btn-outline-success ms-2" onclick="unblockUser('${log.user_id}')">🔓</button>`;
    }

    row.innerHTML = `
      <td>${log.event || ""}</td>
      <td>${statusCell}</td>
      <td>${log.user_id || ""}</td>
      <td>${formatTimestamp(log.timestamp)}</td>
    `;
    table.appendChild(row);
  });
}

function formatTimestamp(ts) {
  if (!ts) return '';

  // Split at T
  const parts = ts.split('T');
  if (parts.length < 2) return ts;

  const date = parts[0];
  let time = parts[1];

  // Optional: remove microseconds for clarity
  time = time.split('.')[0];

  return `${date}   ${time}`;
}


function nextPage() {
  const totalPages = Math.ceil(allAuditLogs.length / rowsPerPage);
  if (currentPage < totalPages) {
    currentPage++;
    renderAuditLogs(allAuditLogs);
  }
}

function prevPage() {
  if (currentPage > 1) {
    currentPage--;
    renderAuditLogs(allAuditLogs);
  }
}

function filterAuditLogs() {
  const query = document.getElementById("auditSearch").value.toLowerCase();
  const filtered = allAuditLogs.filter(
    (log) =>
      (log.event || "").toLowerCase().includes(query) ||
      (log.status || "").toLowerCase().includes(query) ||
      (log.user_id || "").toLowerCase().includes(query) ||
      (log.timestamp || "").toLowerCase().includes(query)
  );
  currentPage = 1;
  renderAuditLogs(filtered);
}

async function refreshStats() {
  try {
    const res = await fetch(`${API_BASE}/admin/stats`);
    const data = await res.json();
    if (res.ok) {
      document.getElementById("statTotal").textContent =
        data.total_attempts ?? 0;
      document.getElementById("statSuccess").textContent =
        data.success_attempts ?? 0;
      document.getElementById("statFailed").textContent =
        data.failed_attempts ?? 0;
      document.getElementById("statBlockedEvents").textContent =
        data.blocked_events ?? 0;
      document.getElementById("statSoftBlockEvents").textContent =
        data.soft_block_events ?? 0;
      document.getElementById("statBlockedUsers").textContent =
        data.blocked_users_count ?? 0;
      document.getElementById("statSoftBlockedUsers").textContent =
        data.soft_blocked_users_count ?? 0;
      document.getElementById("statTotalUsers").textContent =
        data.total_users ?? 0; // Added for total users
    } else {
      alert("❌ Failed to fetch stats");
    }
  } catch (e) {
    console.error(e);
    alert("❌ Error fetching stats");
  }
}

async function refreshAuditLogs() {
  try {
    setText(
      "auditLogsTable",
      '<tr><td colspan="4" class="text-center">Loading...</td></tr>'
    );
    await fetchAuditLogs();
  } catch (e) {
    console.error(e);
    setText(
      "auditLogsTable",
      '<tr><td colspan="4" class="text-center text-danger">❌ Failed to refresh logs.</td></tr>'
    );
  }
}

async function unblockUser(userId) {
  if (!confirm(`Are you sure you want to unblock user ${userId}?`)) return;

  try {
    const res = await fetch(`${API_BASE}/admin/unblock_user`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId }),
    });

    const data = await res.json();
    if (res.ok) {
      alert(data.message);
      await fetchAuditLogs();
      await refreshStats();
    } else {
      alert(`❌ Error: ${data.error}`);
    }
  } catch (e) {
    console.error(e);
    alert("❌ Error unblocking user");
  }
}

async function clearAuditLogs() {
  if (
    !confirm(
      "⚠️ Are you sure you want to delete ALL audit logs? This cannot be undone."
    )
  )
    return;

  try {
    const res = await fetch(`${API_BASE}/admin/clear_audit_logs`, {
      method: "POST",
    });

    const data = await res.json();
    if (res.ok) {
      alert(data.message);
      await fetchAuditLogs();
      await refreshStats();
    } else {
      alert(`❌ Error: ${data.error}`);
    }
  } catch (e) {
    console.error(e);
    alert("❌ Error clearing audit logs.");
  }
}

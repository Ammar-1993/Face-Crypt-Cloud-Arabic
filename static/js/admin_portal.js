const API_BASE = "http://127.0.0.1:8080";

// Translation Helpers
function translateStatus(status) {
  if (!status) return "";
  const s = status.toLowerCase();
  if (s === "success") return "نجاح";
  if (s === "failed" || s === "failure") return "فشل";
  if (s === "blocked") return "محظور";
  if (s === "soft_block") return "حظر مؤقت";
  return status;
}

function translateEvent(event) {
  if (!event) return "";
  const e = event.toLowerCase();
  if (e === "user_login") return "دخول مستخدم";
  if (e === "admin_login") return "دخول مسؤول";
  if (e === "add_user") return "إضافة مستخدم";
  if (e === "delete_user") return "حذف مستخدم";
  if (e === "unblock_user" || e === "admin_unblock") return "فك حظر مستخدم";
  if (e === "clear_logs" || e === "clear_audit_logs") return "مسح سجلات التدقيق";
  return event;
}

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
      `<span class="text-danger">❌ يرجى إدخال معرف المستخدم.</span>`
    );
    return;
  }

  const name = document.getElementById("newUserName").value.trim();
  if (!name) {
    setText(
      "addUserMessage",
      `<span class="text-danger">❌ يرجى إدخال الاسم.</span>`
    );
    return;
  }

  const email = document.getElementById("newUserEmail").value.trim();
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!email) {
    setText(
      "addUserMessage",
      `<span class="text-danger">❌ يرجى إدخال البريد الإلكتروني.</span>`
    );
    return;
  }
  if (!emailPattern.test(email)) {
    setText(
      "addUserMessage",
      `<span class="text-danger">❌ يرجى إدخال بريد إلكتروني صالح.</span>`
    );
    return;
  }

  const image = document.getElementById("newUserImage").files[0];
  if (!image) {
    setText(
      "addUserMessage",
      `<span class="text-danger">❌ يرجى اختيار صورة.</span>`
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
  
  const defaultOption = document.createElement("option");
  defaultOption.text = "اختر مستخدماً للحذف...";
  defaultOption.value = "";
  defaultOption.disabled = true;
  defaultOption.selected = true;
  select.add(defaultOption);

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
      `<span class="text-danger">❌ يرجى تحديد مستخدم لحذفه.</span>`
    );
    return;
  }

  const result = await Swal.fire({
    title: "⚠️ هل أنت متأكد من حذف هذا المستخدم نهائياً؟ لا يمكن التراجع عن هذه الخطوة.",
    icon: 'warning',
    showCancelButton: true,
    confirmButtonText: 'نعم',
    cancelButtonText: 'إلغاء'
  });
  if (!result.isConfirmed) return;

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

  pageIndicator.textContent = `صفحة ${currentPage} من ${totalPages}`;

  if (!pageData || pageData.length === 0) {
    table.innerHTML =
      '<tr><td colspan="4" class="text-center">لم يتم العثور على سجلات.</td></tr>';
    return;
  }

  table.innerHTML = "";
  pageData.forEach((log) => {
    const row = document.createElement("tr");

    // ✨ زر الفك
    let statusCell = translateStatus(log.status);
    if (log.status === "blocked") {
      statusCell += ` <button class="btn btn-sm btn-outline-success ms-2" onclick="unblockUser('${log.user_id}')">🔓</button>`;
    }

    row.innerHTML = `
      <td>${translateEvent(log.event)}</td>
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
      (translateEvent(log.event) || "").toLowerCase().includes(query) ||
      (translateStatus(log.status) || "").toLowerCase().includes(query) ||
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
      alert("❌ فشل في جلب الإحصائيات");
    }
  } catch (e) {
    console.error(e);
    alert("❌ خطأ في جلب الإحصائيات");
  }
}

async function refreshAuditLogs() {
  try {
    setText(
      "auditLogsTable",
      '<tr><td colspan="4" class="text-center">جاري التحميل...</td></tr>'
    );
    await fetchAuditLogs();
  } catch (e) {
    console.error(e);
    setText(
      "auditLogsTable",
      '<tr><td colspan="4" class="text-center text-danger">❌ فشل في تحديث السجلات.</td></tr>'
    );
  }
}

async function unblockUser(userId) {
  if (!confirm(`هل أنت متأكد أنك تريد فك حظر المستخدم ${userId}؟`)) return;

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
      alert(`❌ خطأ: ${data.error}`);
    }
  } catch (e) {
    console.error(e);
    alert("❌ خطأ في فك حظر المستخدم");
  }
}

async function clearAuditLogs() {
  if (
    !confirm(
      "⚠️ هل أنت متأكد من رغبتك في حذف جميع سجلات التدقيق؟ لا يمكن التراجع عن هذا الإجراء."
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
      alert(`❌ خطأ: ${data.error}`);
    }
  } catch (e) {
    console.error(e);
    alert("❌ خطأ في مسح سجلات التدقيق.");
  }
}

// Custom File Upload Label Logic
document.addEventListener('DOMContentLoaded', () => {
  const newUserImageInput = document.getElementById("newUserImage");
  const fileLabel = document.getElementById("fileLabel");
  
  if (newUserImageInput && fileLabel) {
    newUserImageInput.addEventListener("change", (e) => {
      if (e.target.files.length > 0) {
        fileLabel.innerText = '📷 ' + e.target.files[0].name;
      } else {
        fileLabel.innerText = "📷 اختر صورة بصمة الوجه...";
      }
    });
  }
});

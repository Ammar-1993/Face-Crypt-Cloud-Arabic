const API_BASE = "";
let csrfToken = "";

async function adminFetch(url, options = {}) {
  options.credentials = "include";
  if (!options.headers) {
    options.headers = {};
  }
  if (csrfToken) {
    options.headers["X-CSRFToken"] = csrfToken;
  }
  const res = await fetch(url, options);
  if (res.status === 401) {
    Swal.fire({ text: 'انتهت الجلسة. يرجى تسجيل الدخول مجدداً.', icon: 'warning', confirmButtonText: 'حسناً' }).then(() => {
      hide(document.getElementById("adminPanel"));
      show(document.getElementById("loginSection"));
    });
    throw new Error('Unauthorized');
  }
  return res;
}

async function adminLogout() {
  try {
    await fetch(`${API_BASE}/admin/logout`, { method: "POST", credentials: "include" });
  } catch (e) {
    console.error(e);
  }
  hide(document.getElementById("adminPanel"));
  show(document.getElementById("loginSection"));
  document.getElementById("adminPassword").value = "";
  csrfToken = "";
}



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
let auditCursor = null;

async function adminLogin() {
  const passwordInput = document.getElementById("adminPassword");
  const password = passwordInput.value.trim();

  if (!password) {
    setText(
      "loginMessage",
      `<span class="text-danger">❌ الرجاء إدخال كلمة المرور أولاً.</span>`
    );
    setTimeout(() => {
      setText("loginMessage", "");
    }, 3000);
    return;
  }

  const loginBtn = document.getElementById("adminLoginBtn");
  const originalBtnText = loginBtn.innerHTML;

  loginBtn.disabled = true;
  loginBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> جاري التحقق...`;

  try {
    const res = await fetch(`${API_BASE}/admin/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ password }),
    });
    const data = await res.json();
    if (res.ok) {
      if (data.csrf_token) {
        csrfToken = data.csrf_token;
      }
      // Professional & Distinctive Welcome Message
      Swal.fire({
        icon: 'success',
        title: 'تم التحقق بنجاح',
        html: `<div class="text-center"><h5>${data.message}</h5><p class="text-muted mt-2">جاري تحويلك إلى لوحة التحكم خلال 5 ثوانٍ...</p></div>`,
        timer: 5000,
        timerProgressBar: true,
        showConfirmButton: false,
        allowOutsideClick: false,
        showClass: {
          popup: 'animate__animated animate__fadeInDown'
        },
        willClose: () => {
          hide(document.getElementById("loginSection"));
          show(document.getElementById("adminPanel"));
        }
      });

      await loadUsers();
      await fetchAuditLogs();
      await refreshStats();
    } else {
      setText(
        "loginMessage",
        `<span class="text-danger">❌ ${data.error}</span>`
      );
    }
  } catch (error) {
    console.error(error);
    setText(
      "loginMessage",
      `<span class="text-danger">❌ خطأ في الشبكة أو خادم الويب غير متصل.</span>`
    );
  } finally {
    loginBtn.disabled = false;
    loginBtn.innerHTML = originalBtnText;
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

  const res = await adminFetch(`${API_BASE}/admin/add_user`, {
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

let loadedUsersList = [];

async function loadUsers() {
  const res = await adminFetch(`${API_BASE}/admin/list_users`);
  const data = await res.json();

  loadedUsersList = data.users;
  renderDeleteUserOptions(loadedUsersList);
  
  // Clear any existing search query when reloading users
  const searchInput = document.getElementById("deleteUserSearch");
  if (searchInput) searchInput.value = "";
}

function renderDeleteUserOptions(users) {
  const select = document.getElementById("deleteUserId");
  select.innerHTML = "";
  
  const defaultOption = document.createElement("option");
  defaultOption.text = "اختر مستخدماً للحذف...";
  defaultOption.value = "";
  defaultOption.disabled = true;
  defaultOption.selected = true;
  select.add(defaultOption);

  users.forEach((user) => {
    const option = document.createElement("option");
    option.value = user.id;
    option.text = `${user.name} (${user.id})`;
    select.add(option);
  });
}

function filterDeleteUserSelect() {
  const query = document.getElementById("deleteUserSearch").value.toLowerCase();
  const filtered = loadedUsersList.filter(user => 
    user.name.toLowerCase().includes(query) || user.id.toLowerCase().includes(query)
  );
  renderDeleteUserOptions(filtered);
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

  Swal.fire({
    title: 'تأكيد الإجراء',
    text: '⚠️ هل أنت متأكد من حذف هذا المستخدم نهائياً؟ لا يمكن التراجع عن هذه الخطوة.',
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#d33',
    cancelButtonColor: '#3085d6',
    confirmButtonText: 'نعم، متأكد',
    cancelButtonText: 'إلغاء'
  }).then(async (result) => {
    if (result.isConfirmed) {
      const res = await adminFetch(`${API_BASE}/admin/delete_user`, {
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
  });
}

async function fetchAuditLogs(loadMore = false) {
  if (!loadMore) {
    auditCursor = null;
    allAuditLogs = [];
    document.getElementById("auditLogsTable").innerHTML = '<tr><td colspan="5" class="text-center">جاري التحميل...</td></tr>';
  }

  let url = `${API_BASE}/admin/audit_logs?limit=50`;
  if (auditCursor) {
    url += `&start_after=${encodeURIComponent(auditCursor)}`;
  }

  const res = await adminFetch(url);
  const data = await res.json();

  allAuditLogs.push(...data.logs);
  auditCursor = data.next_cursor;

  renderAuditLogs(data.logs, loadMore);

  const btn = document.getElementById("loadMoreLogsBtn");
  if (btn) {
    btn.style.display = data.has_more ? "inline-block" : "none";
  }
}

function renderAuditLogs(logs, append = false) {
  const table = document.getElementById("auditLogsTable");

  if (!append) {
    table.innerHTML = "";
    if (!logs || logs.length === 0) {
      table.innerHTML = '<tr><td colspan="5" class="text-center">لم يتم العثور على سجلات.</td></tr>';
      return;
    }
  }

  logs.forEach((log) => {
    const row = document.createElement("tr");

    // 🏷️ Status Badges Logic
    let badgeClass = "bg-secondary";
    const status = log.status;
    if (status === "success") badgeClass = "bg-success";
    else if (status === "failure") badgeClass = "bg-danger";
    else if (status === "soft_block") badgeClass = "bg-warning text-dark";
    else if (status === "blocked") badgeClass = "bg-dark";

    const statusBadge = `<span class="badge ${badgeClass}">${translateStatus(status)}</span>`;

    // 🛠️ Dedicated Actions Column Logic
    const tdAction = document.createElement("td");
    tdAction.className = "text-center";
    if (status === "blocked") {
      const btn = document.createElement("button");
      btn.className = "btn btn-sm btn-outline-success rounded-pill px-3";
      btn.textContent = "فك الحظر";
      btn.onclick = () => unblockUser(log.user_id);
      tdAction.appendChild(btn);
    }

    const tdEvent = document.createElement("td");
    tdEvent.textContent = translateEvent(log.event);

    const tdStatus = document.createElement("td");
    tdStatus.className = "text-center";
    tdStatus.innerHTML = statusBadge;

    const tdUserId = document.createElement("td");
    tdUserId.textContent = log.user_id || "";

    const tdTime = document.createElement("td");
    tdTime.className = "text-center";
    tdTime.dir = "ltr";
    tdTime.style.unicodeBidi = "plaintext";
    tdTime.textContent = formatTimestamp(log.timestamp);

    row.appendChild(tdEvent);
    row.appendChild(tdStatus);
    row.appendChild(tdUserId);
    row.appendChild(tdTime);
    row.appendChild(tdAction);
    
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




function filterAuditLogs() {
  const query = document.getElementById("auditSearch").value.toLowerCase();
  const filtered = allAuditLogs.filter(
    (log) =>
      (translateEvent(log.event) || "").toLowerCase().includes(query) ||
      (translateStatus(log.status) || "").toLowerCase().includes(query) ||
      (log.user_id || "").toLowerCase().includes(query) ||
      (log.timestamp || "").toLowerCase().includes(query)
  );
  renderAuditLogs(filtered, false);
}

async function refreshStats() {
  try {
    const res = await adminFetch(`${API_BASE}/admin/stats`);
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
      Swal.fire({ text: "❌ فشل في جلب الإحصائيات", icon: 'error', confirmButtonText: 'حسناً' });
    }
  } catch (e) {
    console.error(e);
    Swal.fire({ text: "❌ خطأ في جلب الإحصائيات", icon: 'error', confirmButtonText: 'حسناً' });
  }
}

async function refreshAuditLogs() {
  try {
    setText(
      "auditLogsTable",
      '<tr><td colspan="5" class="text-center">جاري التحميل...</td></tr>'
    );
    await fetchAuditLogs();
  } catch (e) {
    console.error(e);
    setText(
      "auditLogsTable",
      '<tr><td colspan="5" class="text-center text-danger">❌ فشل في تحديث السجلات.</td></tr>'
    );
  }
}

async function unblockUser(userId) {
  Swal.fire({
    title: 'تأكيد الإجراء',
    text: `هل أنت متأكد أنك تريد فك حظر المستخدم ${userId}؟`,
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#d33',
    cancelButtonColor: '#3085d6',
    confirmButtonText: 'نعم، متأكد',
    cancelButtonText: 'إلغاء'
  }).then(async (result) => {
    if (result.isConfirmed) {
      try {
        const res = await adminFetch(`${API_BASE}/admin/unblock_user`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: userId }),
        });

        const data = await res.json();
        if (res.ok) {
          Swal.fire({ text: data.message, icon: 'success', confirmButtonText: 'حسناً' });
          await fetchAuditLogs();
          await refreshStats();
        } else {
          Swal.fire({ text: `❌ خطأ: ${data.error}`, icon: 'error', confirmButtonText: 'حسناً' });
        }
      } catch (e) {
        console.error(e);
        Swal.fire({ text: "❌ خطأ في فك حظر المستخدم", icon: 'error', confirmButtonText: 'حسناً' });
      }
    }
  });
}

async function clearAuditLogs() {
  Swal.fire({
    title: 'تأكيد الإجراء',
    text: '⚠️ هل أنت متأكد من رغبتك في حذف جميع سجلات التدقيق؟ لا يمكن التراجع عن هذا الإجراء.',
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#d33',
    cancelButtonColor: '#3085d6',
    confirmButtonText: 'نعم، متأكد',
    cancelButtonText: 'إلغاء'
  }).then(async (result) => {
    if (result.isConfirmed) {
      try {
        const res = await adminFetch(`${API_BASE}/admin/clear_audit_logs`, {
          method: "POST",
        });

        const data = await res.json();
        if (res.ok) {
          Swal.fire({ text: data.message, icon: 'success', confirmButtonText: 'حسناً' });
          await fetchAuditLogs();
          await refreshStats();
        } else {
          Swal.fire({ text: `❌ خطأ: ${data.error}`, icon: 'error', confirmButtonText: 'حسناً' });
        }
      } catch (e) {
        console.error(e);
        Swal.fire({ text: "❌ خطأ في مسح سجلات التدقيق.", icon: 'error', confirmButtonText: 'حسناً' });
      }
    }
  });
}

// Initialization and UI Logic
document.addEventListener("DOMContentLoaded", () => {
  // 1. Initialize Bootstrap Tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map((tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl));

  // 2. Custom File Upload Label Logic
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

  // Password Visibility Toggle Logic
  const togglePassword = document.getElementById("togglePassword");
  const toggleIcon = document.getElementById("toggleIcon");
  const adminPasswordInput = document.getElementById("adminPassword");

  if (togglePassword && adminPasswordInput) {
    togglePassword.addEventListener("click", function () {
      const type = adminPasswordInput.getAttribute("type") === "password" ? "text" : "password";
      adminPasswordInput.setAttribute("type", type);
      
      // Toggle Icons
      if (type === "password") {
        toggleIcon.classList.remove("bi-eye-slash-fill");
        toggleIcon.classList.add("bi-eye-fill");
      } else {
        toggleIcon.classList.remove("bi-eye-fill");
        toggleIcon.classList.add("bi-eye-slash-fill");
      }
    });
  }

  // 3. Admin Password Complexity & Keyboard Check Logic
  const arabicWarning = document.getElementById("arabicWarning");
  
  let arabicWarningTimeout = null;

  if (adminPasswordInput) {
    adminPasswordInput.addEventListener("input", function () {
      let val = this.value;

      // Block Arabic Characters
      if (/[\u0600-\u06FF]/.test(val)) {
        this.value = val.replace(/[\u0600-\u06FF]/g, '');
        if (arabicWarning) {
          arabicWarning.classList.remove("d-none");
          if (arabicWarningTimeout) clearTimeout(arabicWarningTimeout);
          arabicWarningTimeout = setTimeout(() => arabicWarning.classList.add("d-none"), 3000);
        }
        val = this.value;
      }
    });
  }
});

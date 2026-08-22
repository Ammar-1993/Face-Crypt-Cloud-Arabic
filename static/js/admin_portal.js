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
    Swal.fire({ text: t('session_expired'), icon: 'warning', confirmButtonText: t('ok_btn'), customClass: { popup: 'swal-dark-popup' } }).then(() => {
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
  // Hide nav logout button
  const navLogout = document.getElementById("navLogoutBtn");
  if (navLogout) hide(navLogout);
}



// Translation Helpers
function translateStatus(status) {
  if (!status) return "";
  const s = status.toLowerCase();
  if (s === "success") return t('status_success');
  if (s === "failed" || s === "failure") return t('status_failed');
  if (s === "blocked") return t('status_blocked');
  if (s === "soft_block") return t('status_soft_block');
  return status;
}

function translateEvent(event) {
  if (!event) return "";
  const e = event.toLowerCase();
  if (e === "user_login") return t('event_user_login');
  if (e === "admin_login") return t('event_admin_login');
  if (e === "add_user") return t('event_add_user');
  if (e === "delete_user") return t('event_delete_user');
  if (e === "unblock_user" || e === "admin_unblock") return t('event_unblock_user');
  if (e === "clear_logs" || e === "clear_audit_logs") return t('event_clear_logs');
  if (e === "update_tolerance") return t('event_update_tolerance');
  if (e === "spoofing_attempt") return t('event_spoofing');
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
      `<div class="custom-alert custom-alert-danger">${t('enter_password_first')}</div>`
    );
    setTimeout(() => {
      setText("loginMessage", "");
    }, 3000);
    return;
  }

  const loginBtn = document.getElementById("adminLoginBtn");
  const originalBtnText = loginBtn.innerHTML;

  loginBtn.disabled = true;
  loginBtn.innerHTML = t('admin_verifying_html');

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
        title: t('verify_success'),
        html: `<div class=\"text-center\"><h5>${data.message}</h5><p class=\"text-muted mt-2\">${t('redirecting_admin')}</p></div>`,
        timer: 5000,
        timerProgressBar: true,
        showConfirmButton: false,
        allowOutsideClick: false,
        customClass: { popup: 'swal-dark-popup' },
        showClass: {
          popup: 'animate__animated animate__fadeInDown'
        },
        willClose: () => {
          hide(document.getElementById("loginSection"));
          show(document.getElementById("adminPanel"));
          // Show nav logout button
          const navLogout = document.getElementById("navLogoutBtn");
          if (navLogout) show(navLogout);
        }
      });

      await loadUsers();
      await fetchAuditLogs();
      await refreshStats();
      await loadTolerance();
    } else {
      setText(
        "loginMessage",
        `<div class="custom-alert custom-alert-danger">${data.error}</div>`
      );
    }
  } catch (error) {
    console.error(error);
    setText(
      "loginMessage",
      `<div class="custom-alert custom-alert-danger">${t('admin_network_error')}</div>`
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
      `<div class="custom-alert custom-alert-danger">${t('enter_user_id')}</div>`
    );
    return;
  }

  const name = document.getElementById("newUserName").value.trim();
  if (!name) {
    setText(
      "addUserMessage",
      `<div class="custom-alert custom-alert-danger">${t('enter_name')}</div>`
    );
    return;
  }

  const email = document.getElementById("newUserEmail").value.trim();
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!email) {
    setText(
      "addUserMessage",
      `<div class="custom-alert custom-alert-danger">${t('enter_email')}</div>`
    );
    return;
  }
  if (!emailPattern.test(email)) {
    setText(
      "addUserMessage",
      `<div class="custom-alert custom-alert-danger">${t('enter_valid_email')}</div>`
    );
    return;
  }

  const image = document.getElementById("newUserImage").files[0];
  if (!image) {
    setText(
      "addUserMessage",
      `<div class="custom-alert custom-alert-danger">${t('choose_image')}</div>`
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
      `<div class="custom-alert custom-alert-success">${data.message}</div>`
    );
    await loadUsers();
  } else {
    setText(
      "addUserMessage",
      `<div class="custom-alert custom-alert-danger">${data.error}</div>`
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
  defaultOption.text = t('select_user_to_delete');
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
      `<div class="custom-alert custom-alert-danger">${t('select_user_first')}</div>`
    );
    return;
  }

  Swal.fire({
    title: t('confirm_action'),
    text: t('confirm_delete_user'),
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#d33',
    cancelButtonColor: '#3085d6',
    confirmButtonText: t('yes_sure'),
    cancelButtonText: t('cancel'),
    customClass: { popup: 'swal-dark-popup' }
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
          `<div class="custom-alert custom-alert-success">${data.message}</div>`
        );
        await loadUsers();
      } else {
        setText(
          "deleteUserMessage",
          `<div class="custom-alert custom-alert-danger">${data.error}</div>`
        );
      }
    }
  });
}

async function fetchAuditLogs(loadMore = false) {
  if (!loadMore) {
    auditCursor = null;
    allAuditLogs = [];
    document.getElementById("auditLogsTable").innerHTML = t('loading_table_row');
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
      table.innerHTML = t('no_logs_found_row');
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
      btn.textContent = t('unblock');
      btn.onclick = () => unblockUser(log.user_id);
      tdAction.appendChild(btn);
    }

    const tdEvent = document.createElement("td");
    tdEvent.textContent = translateEvent(log.event);

    const tdStatus = document.createElement("td");
    tdStatus.className = "text-center";
    tdStatus.innerHTML = statusBadge;

    const tdUserId = document.createElement("td");
    let displayUserId = log.user_id || "";
    if (displayUserId === "unknown_user") {
      displayUserId = t('unknown_user');
    } else if (displayUserId === "admin") {
      displayUserId = t('the_admin');
    }
    tdUserId.textContent = displayUserId;

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
      Swal.fire({ text: t('failed_fetch_stats'), icon: 'error', confirmButtonText: t('ok_btn'), customClass: { popup: 'swal-dark-popup' } });
    }
  } catch (e) {
    console.error(e);
    Swal.fire({ text: t('error_fetch_stats'), icon: 'error', confirmButtonText: t('ok_btn'), customClass: { popup: 'swal-dark-popup' } });
  }
}

async function loadTolerance() {
  const toleranceSlider = document.getElementById('tolerance-slider');
  const toleranceDisplay = document.getElementById('tolerance-display');
  if (toleranceSlider && toleranceDisplay) {
    try {
      const res = await adminFetch(`${API_BASE}/admin/api/settings/tolerance`);
      const data = await res.json();
      if (data && data.tolerance !== undefined) {
        toleranceSlider.value = data.tolerance;
        toleranceDisplay.textContent = parseFloat(data.tolerance).toFixed(2);
      }
    } catch (err) {
      console.error("Error fetching tolerance:", err);
    }
  }
}

async function refreshAuditLogs() {
  try {
    setText(
      "auditLogsTable",
      t('loading_table_row')
    );
    await fetchAuditLogs();
  } catch (e) {
    console.error(e);
    setText(
      "auditLogsTable",
      t('failed_refresh_logs_row')
    );
  }
}

async function unblockUser(userId) {
  Swal.fire({
    title: t('confirm_action'),
    text: t('confirm_unblock_user_prefix') + userId + '?',
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#d33',
    cancelButtonColor: '#3085d6',
    confirmButtonText: t('yes_sure'),
    cancelButtonText: t('cancel'),
    customClass: { popup: 'swal-dark-popup' }
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
          Swal.fire({ text: data.message, icon: 'success', confirmButtonText: t('ok_btn'), customClass: { popup: 'swal-dark-popup' } });
          await fetchAuditLogs();
          await refreshStats();
        } else {
          Swal.fire({ text: t('error_prefix') + data.error, icon: 'error', confirmButtonText: t('ok_btn'), customClass: { popup: 'swal-dark-popup' } });
        }
      } catch (e) {
        console.error(e);
        Swal.fire({ text: t('error_unblock'), icon: 'error', confirmButtonText: t('ok_btn'), customClass: { popup: 'swal-dark-popup' } });
      }
    }
  });
}

async function clearAuditLogs() {
  Swal.fire({
    title: t('confirm_action'),
    text: t('confirm_clear_logs'),
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#d33',
    cancelButtonColor: '#3085d6',
    confirmButtonText: t('yes_sure'),
    cancelButtonText: t('cancel'),
    customClass: { popup: 'swal-dark-popup' }
  }).then(async (result) => {
    if (result.isConfirmed) {
      try {
        const res = await adminFetch(`${API_BASE}/admin/clear_audit_logs`, {
          method: "POST",
        });

        const data = await res.json();
        if (res.ok) {
          Swal.fire({ text: data.message, icon: 'success', confirmButtonText: t('ok_btn'), customClass: { popup: 'swal-dark-popup' } });
          await fetchAuditLogs();
          await refreshStats();
        } else {
          Swal.fire({ text: t('error_prefix') + data.error, icon: 'error', confirmButtonText: t('ok_btn'), customClass: { popup: 'swal-dark-popup' } });
        }
      } catch (e) {
        console.error(e);
        Swal.fire({ text: t('error_clear_logs'), icon: 'error', confirmButtonText: t('ok_btn'), customClass: { popup: 'swal-dark-popup' } });
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
        fileLabel.innerText = t('choose_face_image_label');
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

  // ==========================================
  // Tolerance Slider Logic
  // ==========================================
  const toleranceSlider = document.getElementById('tolerance-slider');
  const toleranceDisplay = document.getElementById('tolerance-display');
  const saveToleranceBtn = document.getElementById('save-tolerance-btn');

  if (toleranceSlider && toleranceDisplay && saveToleranceBtn) {
      // (The value will now be fetched after a successful login via loadTolerance)

      // 2. Update badge number locally as admin slides it
      toleranceSlider.addEventListener('input', (e) => {
          toleranceDisplay.textContent = parseFloat(e.target.value).toFixed(2);
      });

      // 3. Save new value to backend
      saveToleranceBtn.addEventListener('click', async () => {
          const newTolerance = parseFloat(toleranceSlider.value);
          
          // Add a spinning loading state to button
          const originalText = saveToleranceBtn.innerHTML;
          saveToleranceBtn.innerHTML = t('saving_html');
          saveToleranceBtn.disabled = true;

          try {
              const res = await adminFetch("/admin/api/settings/tolerance", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ tolerance: newTolerance })
              });
              
              const data = await res.json();

              if (data.message) {
                  Swal.fire({
                      icon: "success",
                      title: t('saved'),
                      text: data.message,
                      background: '#1a1a2e',
                      color: '#fff',
                      confirmButtonColor: '#4facfe',
                      customClass: { popup: 'swal-dark-popup' }
                  });
              } else if (data.error) {
                  throw new Error(data.error);
              }
          } catch (error) {
              Swal.fire({
                  icon: "error",
                  title: t('error'),
                  text: error.message || t('error_save_settings'),
                  background: '#1a1a2e',
                  color: '#fff',
                  confirmButtonColor: '#e74c3c',
                  customClass: { popup: 'swal-dark-popup' }
              });
          } finally {
              // Restore button state
              saveToleranceBtn.innerHTML = originalText;
              saveToleranceBtn.disabled = false;
          }
      });
  }
});

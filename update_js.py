import re

with open('static/js/admin_portal.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Define new functions
new_funcs = """
async function adminFetch(url, options = {}) {
  options.credentials = "include";
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
}

"""

# Prepend new functions to the file right after API_BASE
content = content.replace('const API_BASE = "http://127.0.0.1:8080";', 'const API_BASE = "http://127.0.0.1:8080";\n' + new_funcs)

# Replace fetch with adminFetch in specific functions
# We need to replace fetch with adminFetch, but ONLY for the ones that need it.
# Actually, replacing all `await fetch(` with `await adminFetch(` except in adminFetch and adminLogout is safe, because those are all the API calls.

content = content.replace('await fetch(', 'await adminFetch(')
# Put back the original fetch for adminFetch and adminLogout
content = content.replace('const res = await adminFetch(url, options);', 'const res = await fetch(url, options);')
content = content.replace('await adminFetch(`${API_BASE}/admin/logout`', 'await fetch(`${API_BASE}/admin/logout`')
content = content.replace('await adminFetch(`${API_BASE}/admin/login`', 'await fetch(`${API_BASE}/admin/login`')

with open('static/js/admin_portal.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated JS")

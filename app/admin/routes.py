from flask import Blueprint, request, jsonify, render_template, session
from flask_babel import _
from functools import wraps
from app.config import ADMIN_PASSWORD, db
from utils import face_utils, firebase_utils
import app.config as config
import re
import hmac


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({"error": _("غير مصرح لك بالوصول")}), 401
        return f(*args, **kwargs)
    return decorated_function
# ✅ إنشاء الـ Blueprint
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.before_request
def csrf_protect():
    if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
        if request.path == "/admin/login":
            return
        client_token = request.headers.get('X-CSRFToken')
        server_token = session.get('csrf_token')

        if not client_token or not server_token or not hmac.compare_digest(client_token, server_token):
            return jsonify({"error": _("رمز التحقق (CSRF token) مفقود أو غير صالح.")}), 403



from app.limiter import limiter

# ✅ صفحة Admin Portal
@admin_bp.route("/", methods=["GET"])
@limiter.exempt
def admin_portal():
    return render_template("index_admin.html")


# ✅ /admin/login
@admin_bp.route("/login", methods=["POST"])
def admin_login():
    data = request.get_json()
    if not data or "password" not in data:
        firebase_utils.log_audit_event(
            "admin", "Admin_Login", status="failure", ip_address=request.remote_addr
        )
        return jsonify({"error": _("❌ كلمة المرور مطلوبة")}), 400

    password = data["password"]
    if hmac.compare_digest(password, ADMIN_PASSWORD):
        session.permanent = True
        session['admin_logged_in'] = True
        import secrets
        csrf_token = secrets.token_hex(32)
        session['csrf_token'] = csrf_token
        firebase_utils.log_audit_event(
            "admin", "Admin_Login", status="success", ip_address=request.remote_addr
        )
        return jsonify({"message": _("✅ أهلاً بك أيها المسؤول"), "csrf_token": csrf_token}), 200
    else:
        firebase_utils.log_audit_event(
            "admin", "Admin_Login", status="failure", ip_address=request.remote_addr
        )
        return jsonify({"error": _("كلمة مرور غير صالحة")}), 403


# ✅ /admin/add_user
@admin_bp.route("/add_user", methods=["POST"])
@login_required
def admin_add_user():
    user_id = request.form.get("user_id")
    name = request.form.get("name")
    email = request.form.get("email")
    image_file = request.files.get("image")

    if not user_id or not name or not email or not image_file:
        return jsonify({"error": _("❌ حقول مطلوبة مفقودة")}), 400

    # Server-side validation against XSS / invalid characters
    if len(user_id) > 50 or not re.match(r"^[\w\-]+$", user_id):
        return jsonify({"error": _("❌ معرف المستخدم غير صالح (أحرف، أرقام، شرطات فقط). ومحدود بـ 50 حرف.")}), 400
    if len(name) > 100 or re.search(r"[<>\'\"]", name):
        return jsonify({"error": _("❌ الاسم يحتوي على رموز غير مسموحة.")}), 400

    try:
        image_array = face_utils.load_image_from_request(image_file)
        encoding = face_utils.extract_face_encoding(image_array)

        user_data = {
            "name": name,
            "email": email,
            # When adding a new user from the Admin Portal:
            # ✔️ The encoding is stored as an array of numbers
            # "face_encoding": encoding.tolist(),

            # When adding a new user from the Admin Portal:
            # ✔️ The encoding will not be stored as an array of numbers.
            # ✔️ It will be stored as a very long ciphertext.
            # ✔️ Firestore will display it as a single string.
            # "face_encoding": face_utils.encrypt_encoding(encoding.tolist()),

            "face_encoding": face_utils.encrypt_encoding(encoding.tolist()),
            "failed_attempts": 0,
            "soft_block": False,
            "blocked": False,
        }

        firebase_utils.add_user_to_firestore(user_id, user_data)
        return jsonify({"message": _("تم إضافة المستخدم بنجاح")}), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400


# ✅ /admin/delete_user
@admin_bp.route("/delete_user", methods=["POST"])
@login_required
def admin_delete_user():
    data = request.get_json()
    if not data or "user_id" not in data:
        return jsonify({"error": _("❌ معرف المستخدم مطلوب")}), 400

    user_id = data["user_id"]
    firebase_utils.delete_user_from_firestore(user_id)
    return jsonify({"message": _("تم حذف المستخدم بنجاح")}), 200


# ✅ /admin/list_users
@admin_bp.route("/list_users", methods=["GET"])
@login_required
def admin_list_users():
    users = firebase_utils.get_all_users_summary()
    response = [
        {
            "id": user.get("id"),
            "name": user.get("name"),
            "email": user.get("email"),
            "blocked": user.get("blocked", False),
            "soft_block": user.get("soft_block", False),
            "failed_attempts": user.get("failed_attempts", 0),
        }
        for user in users
    ]

    return jsonify({"users": response}), 200


@admin_bp.route("/audit_logs", methods=["GET"])
@login_required
def admin_audit_logs():
    limit = request.args.get("limit", default=50, type=int)
    if limit > 200:
        limit = 200

    start_after_id = request.args.get("start_after")
    
    logs_ref = db.collection("audit_logs").order_by("timestamp", direction="DESCENDING")
    
    if start_after_id:
        doc = db.collection("audit_logs").document(start_after_id).get()
        if doc.exists:
            logs_ref = logs_ref.start_after(doc)
            
    # Fetch limit + 1 to know if there's a next page
    docs = logs_ref.limit(limit + 1).stream()
    
    logs = []
    for doc in docs:
        log = doc.to_dict()
        log["id"] = doc.id
        logs.append(log)
        
    has_more = len(logs) > limit
    if has_more:
        logs = logs[:limit]
        
    next_cursor = logs[-1]["id"] if logs else None

    return jsonify({"logs": logs, "has_more": has_more, "next_cursor": next_cursor}), 200

@admin_bp.route('/stats', methods=['GET'])
@login_required
def admin_stats():
    # 📌 قراءة سجلات الأحداث باستخدام استعلامات التجميع (Aggregation Queries)
    logs_ref = config.db.collection('audit_logs')
    
    def get_count(query):
        return len(list(query.stream()))

    total = get_count(logs_ref)
    success = get_count(logs_ref.where('status', '==', 'success'))
    failure = get_count(logs_ref.where('status', '==', 'failure'))
    blocked_events = get_count(logs_ref.where('status', '==', 'blocked'))
    soft_block_events = get_count(logs_ref.where('status', '==', 'soft_block'))

    # 📌 قراءة حالات المستخدمين بمسار واحد
    users_ref = config.db.collection('users').stream()
    blocked_users = 0
    soft_blocked_users = 0
    total_users = 0

    for doc in users_ref:
        u = doc.to_dict()
        total_users += 1
        if u.get('blocked', False):
            blocked_users += 1
        if u.get('soft_block', False):
            soft_blocked_users += 1

    # 📌 إرجاع النتيجة
    return jsonify({
        "total_attempts": total,
        "success_attempts": success,
        "failed_attempts": failure,
        "blocked_events": blocked_events,
        "soft_block_events": soft_block_events,
        "blocked_users_count": blocked_users,
        "total_users": total_users,
        "soft_blocked_users_count": soft_blocked_users
    })
    
@admin_bp.route('/unblock_user', methods=['POST'])
@login_required
def admin_unblock_user():
    data = request.get_json()
    if not data or 'user_id' not in data:
        return jsonify({"error": _("❌ معرف المستخدم مطلوب")}), 400

    user_id = data['user_id']
    from google.api_core.exceptions import NotFound
    
    try:
        # تحديث حالة المستخدم في Firestore
        firebase_utils.update_user_fields(user_id, {
            "blocked": False,
            "failed_attempts": 0,
            "soft_block": False,
            "soft_block_time": None
        })
    except NotFound:
        return jsonify({"error": _("❌ لا يمكن فك الحظر: هذا المستخدم غير مسجل في قاعدة البيانات.")}), 404

    # سجل في Audit Logs
    firebase_utils.log_audit_event(
        user_id,
        "Admin_Unblock",
        status="success",
        ip_address=request.remote_addr
    )

    return jsonify({"message": _("✅ تم فك حظر المستخدم بنجاح")}), 200

# @admin_bp.route('/clear_audit_logs', methods=['POST'])
# def admin_clear_audit_logs():
#     try:
#         logs_ref = config.db.collection('audit_logs').stream()
#         count = 0
#         for doc in logs_ref:
#             doc.reference.delete()
#             count += 1

#         # سجّل عملية المسح في السجل نفسه
#         firebase_utils.log_audit_event(
#             'admin',
#             'Clear_Audit_Logs',
#             status='success'
#         )

#         return jsonify({"message": f"✅ Deleted {count} audit logs."}), 200

#     except Exception as e:
#         return jsonify({"error": f"❌ Internal server error: {str(e)}"}), 500



@admin_bp.route('/clear_audit_logs', methods=['POST'])
@login_required
def admin_clear_audit_logs():
    logs_ref = config.db.collection('audit_logs')
    docs = list(logs_ref.stream())
    total_count = len(docs)
    batch_size = 500

    # حذف على دفعات batch
    for i in range(0, total_count, batch_size):
        batch = config.db.batch()
        batch_docs = docs[i:i + batch_size]
        for doc in batch_docs:
            batch.delete(doc.reference)
        batch.commit()

    # سجّل عملية المسح في السجل نفسه
    firebase_utils.log_audit_event(
        'admin',
        'Clear_Audit_Logs',
        status='success'
    )

    return jsonify({"message": _("✅ تم مسح %(total_count)s من سجلات التدقيق.", total_count=total_count)}), 200

@admin_bp.route('/logout', methods=['POST'])
def admin_logout():
    session.clear()
    return jsonify({"message": _("✅ تم تسجيل الخروج بنجاح")}), 200

@admin_bp.route('/api/settings/tolerance', methods=['GET'])
@login_required
def get_tolerance():
    config = firebase_utils.get_security_config()
    return jsonify({"tolerance": config.get("tolerance", 0.6)}), 200

@admin_bp.route('/api/settings/tolerance', methods=['POST'])
@login_required
def update_tolerance():
    data = request.get_json(silent=True)
    if not data or 'tolerance' not in data:
        return jsonify({"success": False, "error": _("❌ المعلمة tolerance مطلوبة")}), 400
        
    try:
        tolerance = float(data['tolerance'])
        if not (0.1 <= tolerance <= 1.0):
            return jsonify({"success": False, "error": _("❌ يجب أن تكون القيمة بين 0.1 و 1.0")}), 400
            
        firebase_utils.update_security_config({"tolerance": tolerance})
        
        firebase_utils.log_audit_event(
            "admin", 
            "Update_Tolerance", 
            status="success", 
            ip_address=request.remote_addr
        )
        return jsonify({"success": True, "message": _("✅ تم تحديث دقة التعرف على الوجه بنجاح")}), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

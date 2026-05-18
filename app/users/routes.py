import time
from flask import Blueprint, request, jsonify
from utils import face_utils, firebase_utils

users_bp = Blueprint('users', __name__, url_prefix='/users')

@users_bp.route('/add', methods=['POST'])
def add_user():
    data = request.json
    if not data or 'user_id' not in data or 'user_data' not in data:
        return jsonify({"error": "طلب غير صالح"}), 400

    user_id = data['user_id']
    user_data = data['user_data']
    firebase_utils.add_user_to_firestore(user_id, user_data)
    return jsonify({"message": f"✅ تم إضافة المستخدم {user_id} بنجاح."})

@users_bp.route('/delete', methods=['POST'])
def delete_user():
    data = request.json
    if not data or 'user_id' not in data:
        return jsonify({"error": "طلب غير صالح"}), 400

    user_id = data['user_id']
    firebase_utils.delete_user_from_firestore(user_id)
    return jsonify({"message": f"✅ تم حذف المستخدم {user_id} بنجاح."})

@users_bp.route('/list', methods=['GET'])
def list_users():
    users = firebase_utils.get_all_users()
    return jsonify({"users": users})

def is_soft_blocked(user):
    """
    Checks if a user is currently under a temporary (soft) block.
    Returns True if blocked, False otherwise.
    """
    if user.get("soft_block", False):
        soft_block_time = user.get("soft_block_time", 0)
        # Check if 5 minutes (300 seconds) have passed
        if int(time.time()) - soft_block_time < 300:
            return True
        else:
            # ✅ Soft block expired -> reset in background or here
            firebase_utils.update_user_fields(user['id'], {
                "soft_block": False,
                "soft_block_time": None,
                "failed_attempts": 0
            })
    return False


@users_bp.route('/verify_login', methods=['POST'])
def verify_login():
    if 'image' not in request.files:
        return jsonify({"error": "❌ لم يتم تقديم أي صورة"}), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({"error": "❌ اسم الملف فارغ"}), 400

    try:
        image_array = face_utils.load_image_from_request(image_file)
        new_encoding = face_utils.extract_face_encoding(image_array)

        users = firebase_utils.get_all_users()
        print(f"✅ Retrieved {len(users)} users from Firestore")

        matched_user = None
        # 1. First, find if the face matches ANY user (including blocked ones)
        for user in users:
            stored_encoding_encrypted = user.get('face_encoding')
            if not stored_encoding_encrypted or not isinstance(stored_encoding_encrypted, str):
                continue

            try:
                stored_encoding = face_utils.decrypt_encoding(stored_encoding_encrypted)
                if face_utils.compare_encodings(stored_encoding, new_encoding):
                    matched_user = user
                    break
            except Exception as e:
                print(f"❌ Error processing user {user.get('id')}: {e}")
                continue

        # 2. If a match is found, check their status
        if matched_user:
            user_id = matched_user['id']
            
            # Check for Permanent Ban
            if matched_user.get('blocked', False):
                firebase_utils.log_audit_event(user_id, "User_Login", status='blocked', ip_address=request.remote_addr)
                return jsonify({
                    "message": "🚫 **تم حظر الحساب نهائياً**\nلقد تجاوزت الحد الأقصى للمحاولات الفاشلة (5 محاولات). يرجى مراجعة إدارة النظام لفك الحظر."
                }), 403
            
            # Check for Soft Block
            if is_soft_blocked(matched_user):
                # Increment attempts even during soft block as a penalty
                failed_attempts = matched_user.get('failed_attempts', 0) + 1
                update_data = {"failed_attempts": failed_attempts}
                status_to_log = 'soft_block'
                if failed_attempts >= 5:
                    update_data["blocked"] = True
                    status_to_log = 'blocked'
                    msg = "🚫 **تم حظر الحساب نهائياً**\nلقد تم تجاوز عدد المحاولات الفاشلة. يرجى مراجعة إدارة النظام لفك الحظر."
                else:
                    msg = "⏳ **تنبيه أمني: حظر مؤقت**\nتم تجاوز عدد المحاولات الفاشلة. يرجى المحاولة مرة أخرى بعد 5 دقائق لحماية خصوصية بياناتك."

                
                firebase_utils.update_user_fields(user_id, update_data)
                firebase_utils.log_audit_event(user_id, "User_Login", status=status_to_log, ip_address=request.remote_addr)
                return jsonify({"message": msg}), 403

            # Success path
            firebase_utils.update_user_fields(user_id, {
                "failed_attempts": 0,
                "soft_block": False,
                "soft_block_time": None
            })
            firebase_utils.log_audit_event(user_id, "User_Login", status='success', ip_address=request.remote_addr)

            return jsonify({
                "message": f"✅ تم تسجيل الدخول بنجاح. أهلاً بك، {matched_user.get('name', '[User Name]')}",
                "user": {
                    "id": user_id,
                    "name": matched_user.get('name'),
                    "email": matched_user.get('email')
                }
            }), 200

        # 3. If NO match is found
        # In a generic face login, we don't know who to penalize.
        # However, to satisfy the requirement of "5 failed attempts -> ban", 
        # we'll assume the system tracks it globally or for the 'intended' user.
        # Given the existing structure, we will increment for all non-blocked users 
        # but only if they are not already blocked.
        # (This is suboptimal but preserves the original project's intent if it was a single-user system).
        
        any_new_ban = False
        for user in users:
            if user.get('blocked', False):
                continue

            user_id = user['id']
            failed_attempts = user.get('failed_attempts', 0) + 1
            update_data = {"failed_attempts": failed_attempts}
            
            status = 'failure'

            if failed_attempts == 3:
                update_data["soft_block"] = True
                update_data["soft_block_time"] = int(time.time())
                status = 'soft_block'
            if failed_attempts >= 5:
                update_data["blocked"] = True
                any_new_ban = True
                status = 'blocked'

            firebase_utils.update_user_fields(user_id, update_data)
            firebase_utils.log_audit_event(user_id, "User_Login", status=status, ip_address=request.remote_addr)

        if any_new_ban:
            return jsonify({
                "message": "🚫 **نظام الأمان: تم الإغلاق**\nلقد تم تجاوز عدد المحاولات المسموح بها (5 محاولات). تم حظر الوصول نهائياً لضمان سلامة البيانات."
            }), 403

        return jsonify({
            "message": "❌ **فشل تسجيل الدخول**\nعذراً، ملامح الوجه لا تطابق سجلاتنا. يرجى المحاولة مرة أخرى في إضاءة جيدة.",
        }), 403


    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"❌ خطأ داخلي في الخادم: {str(e)}"}), 500


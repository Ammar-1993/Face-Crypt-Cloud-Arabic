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

def is_ip_banned(ip_address):
    status = firebase_utils.get_ip_status(ip_address)
    
    if status.get("blocked", False):
        return True, "permanent"
    
    if status.get("soft_block", False):
        soft_block_time = status.get("soft_block_time", 0)
        if int(time.time()) - soft_block_time < 300:
            return True, "temporary"
        else:
            # Reset soft block if time expired
            firebase_utils.reset_ip_status(ip_address)
            
    return False, None


@users_bp.route('/verify_login', methods=['POST'])
def verify_login():
    ip_address = request.remote_addr
    
    # 1. Check IP Ban Status
    banned, ban_type = is_ip_banned(ip_address)
    if banned:
        if ban_type == "permanent":
            return jsonify({
                "error": "❌ تم حظر هذا الجهاز بشكل دائم لتجاوز عدد المحاولات المسموح بها. يرجى مراجعة المسؤول."
            }), 403
        else:
            return jsonify({
                "error": "❌ تم حظر المحاولات مؤقتاً. يرجى المحاولة مرة أخرى بعد 5 دقائق."
            }), 403

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
        for user in users:
            if user.get('blocked', False):
                continue

            stored_encoding_encrypted = user.get('face_encoding')
            if not stored_encoding_encrypted or not isinstance(stored_encoding_encrypted, str):
                continue

            try:
                stored_encoding = face_utils.decrypt_encoding(stored_encoding_encrypted)
            except Exception as e:
                print(f"❌ Failed to decrypt user {user.get('id')}: {e}")
                continue

            if not stored_encoding or not isinstance(stored_encoding, list):
                print(f"⚠️ Skipping user {user.get('id')}: invalid decrypted encoding")
                continue

            try:
                if face_utils.compare_encodings(stored_encoding, new_encoding):
                    matched_user = user
                    break
            except Exception as e:
                print(f"❌ Comparison error for user {user.get('id')}: {e}")
                continue

        if matched_user:
            user_id = matched_user['id']
            # Reset IP status on success
            firebase_utils.reset_ip_status(ip_address)
            
            # Reset user fields
            firebase_utils.update_user_fields(user_id, {
                "failed_attempts": 0,
                "soft_block": False,
                "soft_block_time": None
            })
            firebase_utils.log_audit_event(user_id, "User_Login", status='success', ip_address=ip_address)

            return jsonify({
                "message": f"✅ تم تسجيل الدخول بنجاح. أهلاً بك، {matched_user.get('name', '[User Name]')}",
                "user": {
                    "id": matched_user['id'],
                    "name": matched_user.get('name'),
                    "email": matched_user.get('email')
                }
            }), 200

        # 2. Handle Failure and Increment IP Attempts
        status = firebase_utils.get_ip_status(ip_address)
        failed_attempts = status.get('failed_attempts', 0) + 1
        
        update_data = {"failed_attempts": failed_attempts}
        
        if failed_attempts == 3:
            update_data["soft_block"] = True
            update_data["soft_block_time"] = int(time.time())
            msg = "❌ فشل التحقق (3 محاولات). تم حظرك مؤقتاً لمدة 5 دقائق."
        elif failed_attempts >= 5:
            update_data["blocked"] = True
            msg = "❌ تم حظر هذا الجهاز بشكل دائم بعد 5 محاولات فاشلة."
        else:
            msg = f"❌ فشل التحقق. المحاولات الفاشلة: {failed_attempts} من 5."

        firebase_utils.update_ip_status(ip_address, update_data)
        firebase_utils.log_audit_event("unknown", "User_Login", status='failure', ip_address=ip_address)

        return jsonify({"error": msg}), 403

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"❌ خطأ داخلي في الخادم: {str(e)}"}), 500

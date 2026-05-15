import time
from flask import Blueprint, request, jsonify
from utils import face_utils, firebase_utils

users_bp = Blueprint('users', __name__, url_prefix='/users')

@users_bp.route('/add', methods=['POST'])
def add_user():
    data = request.json
    if not data or 'user_id' not in data or 'user_data' not in data:
        return jsonify({"error": "Invalid request"}), 400

    user_id = data['user_id']
    user_data = data['user_data']
    firebase_utils.add_user_to_firestore(user_id, user_data)
    return jsonify({"message": f"✅ User {user_id} added successfully."})

@users_bp.route('/delete', methods=['POST'])
def delete_user():
    data = request.json
    if not data or 'user_id' not in data:
        return jsonify({"error": "Invalid request"}), 400

    user_id = data['user_id']
    firebase_utils.delete_user_from_firestore(user_id)
    return jsonify({"message": f"✅ User {user_id} deleted successfully."})

@users_bp.route('/list', methods=['GET'])
def list_users():
    users = firebase_utils.get_all_users()
    return jsonify({"users": users})

def is_soft_blocked(user):
    if user.get("soft_block", False):
        soft_block_time = user.get("soft_block_time", 0)
        if int(time.time()) - soft_block_time < 300:
            # ✅ زيادة المحاولة أثناء soft_block
            failed_attempts = user.get('failed_attempts', 0) + 1
            update_data = {"failed_attempts": failed_attempts}

            if failed_attempts >= 5:
                update_data["blocked"] = True
                status = 'blocked'
            else:
                status = 'soft_block'

            firebase_utils.update_user_fields(user['id'], update_data)
            firebase_utils.log_audit_event(user['id'], "User_Login", status=status, ip_address=request.remote_addr)
            return True
        else:
            # ✅ انتهت مدة soft_block -> إعادة التعيين
            firebase_utils.update_user_fields(user['id'], {
                "soft_block": False,
                "soft_block_time": None,
                "failed_attempts": 0
            })
    return False


@users_bp.route('/verify_login', methods=['POST'])
def verify_login():
    if 'image' not in request.files:
        return jsonify({"error": "❌ No image provided"}), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({"error": "❌ Empty file name"}), 400

    try:
        image_array = face_utils.load_image_from_request(image_file)
        new_encoding = face_utils.extract_face_encoding(image_array)

        users = firebase_utils.get_all_users()
        print(f"✅ Retrieved {len(users)} users from Firestore")

        for user in users:
            if is_soft_blocked(user):
                firebase_utils.log_audit_event(user['id'], "User_Login", status='soft_block', ip_address=request.remote_addr)
                return jsonify({
                    "message": "❌ Too many failed attempts. Please try again in 5 minutes."
                }), 403

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
            firebase_utils.update_user_fields(user_id, {
                "failed_attempts": 0,
                "soft_block": False,
                "soft_block_time": None
            })
            firebase_utils.log_audit_event(user_id, "User_Login", status='success', ip_address=request.remote_addr)

            return jsonify({
                "message": f"✅ Login successful. Welcome, {matched_user.get('name', '[User Name]')}",
                "user": {
                    "id": matched_user['id'],
                    "name": matched_user.get('name'),
                    "email": matched_user.get('email')
                }
            }), 200

        for user in users:
            user_id = user['id']
            if user.get('blocked', False):
                continue

            failed_attempts = user.get('failed_attempts', 0) + 1
            update_data = {"failed_attempts": failed_attempts}

            if failed_attempts == 3:
                update_data["soft_block"] = True
                update_data["soft_block_time"] = int(time.time())

            if failed_attempts >= 5:
                update_data["blocked"] = True

            firebase_utils.update_user_fields(user_id, update_data)
            firebase_utils.log_audit_event(user_id, "User_Login", status='failure', ip_address=request.remote_addr)

        return jsonify({
            "message": "❌ Login failed. Face does not match our records.",
        }), 403

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"❌ Internal server error: {str(e)}"}), 500

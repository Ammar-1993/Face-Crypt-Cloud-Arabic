import time
import logging
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)
from utils import face_utils, firebase_utils
from app.config import ENABLE_LIVENESS_CHECK
from app.limiter import limiter

users_bp = Blueprint('users', __name__, url_prefix='/users')

GENERIC_ERROR_MSG = "❌ **فشل تسجيل الدخول**\nالرجاء المحاولة مرة أخرى، أو التواصل مع إدارة النظام إذا استمرت المشكلة."

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
@limiter.limit("10 per minute")
@limiter.limit("30 per hour")
def verify_login():
    if 'image' not in request.files:
        return jsonify({"error": "❌ لم يتم تقديم أي صورة"}), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({"error": "❌ اسم الملف فارغ"}), 400

    image2_file = request.files.get('image2')

    try:
        image_array = face_utils.load_image_from_request(image_file)
        
        new_encoding = face_utils.extract_face_encoding(image_array)

        users = firebase_utils.get_all_users()
        logger.info("✅ Retrieved %d users from Firestore", len(users))

        matched_user = None
        # 1. First, find if the face matches ANY user (including blocked ones)
        decrypted_encodings = []
        valid_users = []
        for user in users:
            stored_encoding_encrypted = user.get('face_encoding')
            if not stored_encoding_encrypted or not isinstance(stored_encoding_encrypted, str):
                continue

            try:
                stored_encoding = face_utils.decrypt_encoding(stored_encoding_encrypted)
                decrypted_encodings.append(stored_encoding)
                valid_users.append(user)
            except Exception as e:
                logger.warning("❌ Error processing user %s: %s", user.get('id'), e)
                continue
                
        if valid_users:
            best_match_idx = face_utils.find_best_match(decrypted_encodings, new_encoding)
            if best_match_idx is not None:
                matched_user = valid_users[best_match_idx]

        # 2. If a match is found, check their status
        if matched_user:
            user_id = matched_user['id']
            
            # Check for Permanent Ban
            if matched_user.get('blocked', False):
                firebase_utils.log_audit_event(user_id, "User_Login", status='blocked', ip_address=request.remote_addr)
                return jsonify({"message": GENERIC_ERROR_MSG}), 403
            
            # Check for Soft Block
            if is_soft_blocked(matched_user):
                failed_attempts = matched_user.get('failed_attempts', 0) + 1
                update_data = {"failed_attempts": failed_attempts}
                status_to_log = 'soft_block'
                if failed_attempts >= 5:
                    update_data["blocked"] = True
                    status_to_log = 'blocked'

                firebase_utils.update_user_fields(user_id, update_data)
                firebase_utils.log_audit_event(user_id, "User_Login", status=status_to_log, ip_address=request.remote_addr)
                return jsonify({"message": GENERIC_ERROR_MSG}), 403

            # 🛡️ Liveness Check Flow
            if ENABLE_LIVENESS_CHECK:
                import face_recognition
                face_locations_1 = face_recognition.face_locations(image_array)
                image_array_2 = face_utils.load_image_from_request(image2_file) if image2_file else None
                face_locations_2 = face_recognition.face_locations(image_array_2) if image_array_2 is not None else None
                is_live, reason = face_utils.check_liveness(
                    image_array, image_array_2,
                    face_locations_1=face_locations_1,
                    face_locations_2=face_locations_2
                )
                if not is_live:
                    # Penalize targeted user for spoofing attempt
                    failed_attempts = matched_user.get('failed_attempts', 0) + 1
                    update_data = {"failed_attempts": failed_attempts}
                    status_to_log = 'failure'
                    
                    if failed_attempts >= 5:
                        update_data["blocked"] = True
                        status_to_log = 'blocked'
                    elif failed_attempts >= 3:
                        update_data["soft_block"] = True
                        update_data["soft_block_time"] = int(time.time())
                        status_to_log = 'soft_block'
                        
                    firebase_utils.update_user_fields(user_id, update_data)
                    firebase_utils.log_audit_event(user_id, "Spoofing_Attempt", status=status_to_log, ip_address=request.remote_addr)
                    return jsonify({"message": f"🚨 **فشل الأمان (مكافحة الانتحال):**\n{reason}"}), 403

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
        # PREVIOUS DESIGN FLAW: 
        # The previous design incorrectly looped through all users and penalized them
        # for a single failed login attempt. This was highly unsafe as it allowed
        # one brute-force attack to lock out every single user in the system.
        # We now use Flask-Limiter for IP-based rate limiting instead of global user penalization.
        
        # Log the unknown login attempt for auditing without associating it to a specific user
        firebase_utils.log_audit_event("unknown_user", "User_Login", status='failure', ip_address=request.remote_addr)

        return jsonify({"message": GENERIC_ERROR_MSG}), 403


    except ValueError as e:
        return jsonify({"error": str(e)}), 400

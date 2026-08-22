import time
import logging
from flask import Blueprint, request, jsonify, session
from flask_babel import _
from webauthn import generate_registration_options, verify_registration_response, generate_authentication_options, verify_authentication_response
from webauthn.helpers.structs import RegistrationCredential, AuthenticationCredential
from webauthn.helpers import bytes_to_base64url, base64url_to_bytes
import os

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
        return jsonify({"error": _("❌ لم يتم تقديم أي صورة")}), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({"error": _("❌ اسم الملف فارغ")}), 400

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
                return jsonify({"message": _(GENERIC_ERROR_MSG)}), 403
            
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
                return jsonify({"message": _(GENERIC_ERROR_MSG)}), 403

            # 🛡️ Liveness Check Flow
            if ENABLE_LIVENESS_CHECK:
                import face_recognition
                face_locations_1 = face_recognition.face_locations(image_array)
                image_array_2 = face_utils.load_image_from_request(image2_file) if image2_file else None
                face_locations_2 = face_recognition.face_locations(image_array_2) if image_array_2 is not None else None
                challenge = request.form.get("challenge")
                is_live, reason = face_utils.check_liveness(
                    image_array, image_array_2,
                    face_locations_1=face_locations_1,
                    face_locations_2=face_locations_2,
                    challenge=challenge
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
                    return jsonify({"message": _("🚨 **فشل الأمان (مكافحة الانتحال):**\n%(reason)s", reason=reason)}), 403

            # Success path
            firebase_utils.update_user_fields(user_id, {
                "failed_attempts": 0,
                "soft_block": False,
                "soft_block_time": None
            })
            firebase_utils.log_audit_event(user_id, "User_Login", status='success', ip_address=request.remote_addr)
            
            # Establish session for subsequent authenticated actions (like WebAuthn registration)
            session['user_id'] = user_id

            return jsonify({
                "message": _("✅ تم تسجيل الدخول بنجاح. أهلاً بك، %(name)s", name=matched_user.get('name', '[User Name]')),
                "user": {
                    "id": user_id,
                    "name": matched_user.get('name'),
                    "email": matched_user.get('email')
                }
            }), 200

        # 3. If NO match is found
        firebase_utils.log_audit_event("unknown_user", "User_Login", status='failure', ip_address=request.remote_addr)
        return jsonify({"message": _(GENERIC_ERROR_MSG)}), 403

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@users_bp.route('/webauthn/register/begin', methods=['POST'])
def webauthn_register_begin():
    if 'user_id' not in session:
        return jsonify({"error": _("غير مصرح لك بالوصول")}), 401
    
    # Retrieve user to get their info
    user_id = session['user_id']
    users = firebase_utils.get_all_users()
    user = next((u for u in users if u['id'] == user_id), None)
    if not user:
        return jsonify({"error": _("المستخدم غير موجود")}), 404

    # Generate registration options
    rp_id = request.host.split(':')[0]
    rp_name = "Face-Crypt-Cloud"
    user_name = user.get('email', user_id)
    
    options = generate_registration_options(
        rp_id=rp_id,
        rp_name=rp_name,
        user_id=user_id.encode("utf-8"),
        user_name=user_name,
        user_display_name=user.get('name', user_name),
    )
    
    session['webauthn_challenge'] = bytes_to_base64url(options.challenge)
    
    import json
    # Use json.loads(options.json()) since py_webauthn options object provides a json() method
    return jsonify(json.loads(options.json()))

@users_bp.route('/webauthn/register/complete', methods=['POST'])
def webauthn_register_complete():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": _("غير مصرح لك بالوصول")}), 401

    challenge = session.get('webauthn_challenge')
    if not challenge:
        return jsonify({"error": _("لا توجد عملية تسجيل قيد التقدم")}), 400

    try:
        credential_data = request.json
        rp_id = request.host.split(':')[0]

        verification = verify_registration_response(
            credential=credential_data,
            expected_challenge=base64url_to_bytes(challenge),
            expected_origin=request.host_url.rstrip("/"),
            expected_rp_id=rp_id
        )
        
        # Save the credential for the user
        firebase_utils.update_user_fields(user_id, {
            "webauthn_credential_id": bytes_to_base64url(verification.credential_id),
            "webauthn_public_key": bytes_to_base64url(verification.credential_public_key),
            "webauthn_sign_count": getattr(verification, 'sign_count', 0)
        })

        # Clear challenge
        session.pop('webauthn_challenge', None)
        
        return jsonify({"status": "success", "message": _("تم تسجيل مفتاح المرور بنجاح!")})
    except Exception as e:
        logger.error(f"WebAuthn registration failed: {e}")
        return jsonify({"error": _("حدث خطأ أثناء معالجة الطلب.")}), 400

@users_bp.route('/webauthn/login/begin', methods=['POST'])
@limiter.limit("10 per minute")
@limiter.limit("30 per hour")
def webauthn_login_begin():
    rp_id = request.host.split(':')[0]
    options = generate_authentication_options(
        rp_id=rp_id,
        user_verification="preferred"
    )
    session['webauthn_challenge'] = bytes_to_base64url(options.challenge)
    import json
    return jsonify(json.loads(options.json()))

@users_bp.route('/webauthn/login/complete', methods=['POST'])
@limiter.limit("10 per minute")
@limiter.limit("30 per hour")
def webauthn_login_complete():
    challenge = session.get('webauthn_challenge')
    if not challenge:
        return jsonify({"error": _("لا توجد عملية تسجيل دخول قيد التقدم")}), 400

    try:
        credential_data = request.json
        credential_id = credential_data.get('id')
        
        matched_user = firebase_utils.get_user_by_webauthn_credential_id(credential_id)
                
        if not matched_user:
            return jsonify({"error": _("بيانات الاعتماد غير مسجلة")}), 404

        rp_id = request.host.split(':')[0]

        verification = verify_authentication_response(
            credential=credential_data,
            expected_challenge=base64url_to_bytes(challenge),
            expected_origin=request.host_url.rstrip("/"),
            expected_rp_id=rp_id,
            credential_public_key=base64url_to_bytes(matched_user['webauthn_public_key']),
            credential_current_sign_count=matched_user.get('webauthn_sign_count', 0)
        )

        user_id = matched_user['id']

        firebase_utils.update_user_fields(user_id, {
            "failed_attempts": 0,
            "soft_block": False,
            "soft_block_time": None,
            "webauthn_sign_count": getattr(verification, 'new_sign_count', 0)
        })
        firebase_utils.log_audit_event(user_id, "User_Login", status='success', ip_address=request.remote_addr)
        
        session['user_id'] = user_id
        session.pop('webauthn_challenge', None)

        return jsonify({
            "message": _("✅ تم تسجيل الدخول بنجاح. أهلاً بك، %(name)s", name=matched_user.get('name', '[User Name]')),
            "user": {
                "id": user_id,
                "name": matched_user.get('name'),
                "email": matched_user.get('email')
            }
        }), 200

    except Exception as e:
        logger.error(f"WebAuthn login failed: {e}")
        return jsonify({"error": _("حدث خطأ أثناء معالجة الطلب.")}), 400

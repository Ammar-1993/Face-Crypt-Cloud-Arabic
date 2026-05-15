from app.config import initialize_firebase
from utils import firebase_utils

# تهيئة Firebase مرة واحدة
initialize_firebase()

# 1️⃣ اختبار إضافة مستخدم
test_user_id = "test_user_123"
test_user_data = {
    "name": "Test User",
    "email": "testuser@example.com"
}
firebase_utils.add_user_to_firestore(test_user_id, test_user_data)

# 2️⃣ اختبار جلب المستخدمين
users = firebase_utils.get_all_users()
print("📋 Users:", users)

# 3️⃣ اختبار تسجيل حدث تدقيق
firebase_utils.log_audit_event({
    "event": "test_event",
    "details": "This is a test audit log."
})

# 4️⃣ اختبار حذف المستخدم
firebase_utils.delete_user_from_firestore(test_user_id)

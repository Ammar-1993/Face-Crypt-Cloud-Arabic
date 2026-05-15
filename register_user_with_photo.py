import os
from utils import face_utils
from utils import firebase_utils
from app import config

# ✅ ابدأ بتهيئة Firebase
config.initialize_firebase()

# ✅ حدد بيانات المستخدم الجديد
user_id = "test_user_999"
name = "Test User 999"
email = "testuser999@example.com"
image_path = "test_images/user1.png"  # ← ضع هنا مسار صورتك

# ✅ 1️⃣ حمّل الصورة واستخرج encoding
from PIL import Image
import numpy as np

print(f"✅ Loading image from: {image_path}")
with open(image_path, 'rb') as f:
    image_array = face_utils.load_image_from_request(f)

encoding = face_utils.extract_face_encoding(image_array)
print("✅ Face encoding extracted.")

# ✅ 2️⃣ تجهيز البيانات
user_data = {
    "name": name,
    "email": email,
    "face_encoding": encoding.tolist()
}

# ✅ 3️⃣ أضف إلى Firestore
firebase_utils.add_user_to_firestore(user_id, user_data)

print(f"✅ User {user_id} successfully added to Firestore with face_encoding.")

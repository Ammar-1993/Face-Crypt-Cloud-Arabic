from utils import face_utils

# استبدل هذه المسارات بصورك المحلية لاختبار حقيقي
IMAGE_PATH_1 = "test_images/Ammar.jpg"
IMAGE_PATH_2 = "test_images/user1.png"

def load_image_from_path(path):
    from PIL import Image
    import numpy as np

    # افتح وحول إلى RGB مؤكد
    image = Image.open(path).convert('RGB')

    # تأكيد حجم مناسب (اختياري)
    image = image.resize((500, 500))

    # تحويل إلى مصفوفة NumPy 8-bit RGB
    image_array = np.asarray(image, dtype=np.uint8)

    # ضمان contiguous في الذاكرة
    image_array = np.ascontiguousarray(image_array)

    print(f"✅ Loaded {path}, shape: {image_array.shape}, dtype: {image_array.dtype}, contiguous: {image_array.flags['C_CONTIGUOUS']}")
    return image_array


# 1️⃣ تحميل الصورتين
img1 = load_image_from_path(IMAGE_PATH_1)
img2 = load_image_from_path(IMAGE_PATH_2)

# 2️⃣ استخراج Face Encoding مع التعامل الآمن
try:
    encoding1 = face_utils.extract_face_encoding(img1)
    print("✅ Encoding 1:", encoding1)
    # print(encoding1.tolist())

except Exception as e:
    print("❌ Error in Encoding 1:", e)
    encoding1 = None

try:
    encoding2 = face_utils.extract_face_encoding(img2)
    print("✅ Encoding 2:", encoding2)
except Exception as e:
    print("❌ Error in Encoding 2:", e)
    encoding2 = None

# 3️⃣ مقارنة إذا الاثنين نجحوا
if encoding1 is not None and encoding2 is not None:
    result = face_utils.compare_encodings(encoding1, encoding2)
    print("✅ Match Result:", result)
else:
    print("⚠️ Could not compare encodings because one or both failed.")


import numpy as np
import face_recognition
import cv2
import math
import json
from PIL import Image
from io import BytesIO
from cryptography.fernet import Fernet
import os
import onnxruntime as ort
import time
import logging

from app.config import SECRET_KEY
from utils import firebase_utils
fernet = Fernet(SECRET_KEY.encode())

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'minifasnet_v2.onnx')
try:
    fas_session = ort.InferenceSession(MODEL_PATH)
    fas_input_name = fas_session.get_inputs()[0].name
except Exception as e:
    logging.getLogger(__name__).error(f"Failed to load MiniFASNet model: {e}")
    fas_session = None


def load_image_from_request(file):
    """
    Loads an image from a Flask request file object.
    Ensures RGB format and converts to a NumPy array.
    """
    file.seek(0)
    data = file.read()
    if not data:
        raise ValueError("❌ لم يتم استلام أي بيانات للصورة.")
        
    image = Image.open(BytesIO(data)).convert('RGB')
    image = image.resize((500, 500))  # Optional resize to standardize
    image_array = np.asarray(image, dtype=np.uint8)
    image_array = np.ascontiguousarray(image_array)
    return image_array

def extract_face_encoding(image_array, face_locations=None):
    """
    Safely extracts the face encoding from a given image (NumPy array).
    Returns the first encoding found or raises ValueError.
    """
    try:
        if image_array.dtype != np.uint8:
            raise ValueError(f"نوع البيانات غير مدعوم: {image_array.dtype}")
        if len(image_array.shape) != 3 or image_array.shape[2] != 3:
            raise ValueError(f"شكل غير مدعوم: {image_array.shape}")
        
        encodings = face_recognition.face_encodings(image_array, known_face_locations=face_locations)
        if len(encodings) == 0:
            raise ValueError("لم يتم اكتشاف أي وجه. يرجى المحاولة مرة أخرى بصورة واضحة.")
        return encodings[0]
    except Exception as e:
        raise ValueError(f"فشل في ترميز الوجه: {str(e)}")


def compare_encodings(known_encoding, unknown_encoding, tolerance=None):
    """
    Compares two face encodings.
    Returns True if they match within the given tolerance.
    """
    if tolerance is None:
        tolerance = firebase_utils.get_security_config().get("tolerance", 0.6)
        
    if known_encoding is None or unknown_encoding is None:
        raise ValueError("❌ أحد التشفيرات أو كلاهما غير صالح.")
    results = face_recognition.compare_faces([known_encoding], unknown_encoding, tolerance=tolerance)
    return results[0]

def find_best_match(known_encodings_list, unknown_encoding, tolerance=None):
    """
    Finds the best match for an unknown encoding against a list of known encodings.
    Returns the index of the best match within the tolerance, or None if no match is found.
    """
    if tolerance is None:
        tolerance = firebase_utils.get_security_config().get("tolerance", 0.6)
        
    if not known_encodings_list:
        return None
    
    known_encodings_array = np.array(known_encodings_list)
    distances = face_recognition.face_distance(known_encodings_array, unknown_encoding)
    best_match_idx = np.argmin(distances)
    
    if distances[best_match_idx] <= tolerance:
        return best_match_idx
    return None

def encrypt_encoding(encoding):
    """
    Takes a list of floats, serializes and encrypts it.
    Returns a string.
    """
    serialized = json.dumps(encoding).encode()
    encrypted = fernet.encrypt(serialized)
    return encrypted.decode()

def decrypt_encoding(encrypted_str):
    """
    Takes an encrypted string, decrypts and deserializes it to list of floats.
    """
    decrypted = fernet.decrypt(encrypted_str.encode())
    decoded = json.loads(decrypted.decode())
    return decoded

def check_liveness(image_array_1, image_array_2=None, face_locations_1=None, face_locations_2=None, challenge=None):
    """
    Basic anti-spoofing liveness check.
    If image_array_2 is provided, checks for natural head movement (landmark distance).
    If a challenge is provided, it explicitly verifies the requested movement (smile, raise_eyebrows, turn_right).
    This defends against PRE-RECORDED replay attacks specifically (a fixed video can't react to a random prompt).
    It does NOT defend against real-time deepfake puppeteering, which is a harder and costlier threat model out of scope here.
    If only one image is provided, falls back to a texture heuristic (Laplacian variance) to reject extremely flat/blurry photos.
    Returns: (is_live: bool, reason: str)
    """
    # 1. Texture heuristic (Single frame fallback)
    # A printed photo or screen might be blurrier or have different edge characteristics
    # compared to a live 3D face in focus.
    gray1 = cv2.cvtColor(image_array_1, cv2.COLOR_RGB2GRAY)
    laplacian_var = cv2.Laplacian(gray1, cv2.CV_64F).var()
    
    # Threshold for blur (very modest to allow regular webcams)
    if laplacian_var < 30.0:
        return False, "الصورة غير واضحة أو تبدو كصورة مطبوعة."

    # 2. Active Challenge (Two frames)
    if image_array_2 is not None:
        try:
            landmarks1 = face_recognition.face_landmarks(image_array_1, face_locations=face_locations_1)
            landmarks2 = face_recognition.face_landmarks(image_array_2, face_locations=face_locations_2)
            
            if not landmarks1 or not landmarks2:
                return False, "لم يتم اكتشاف الوجه في الإطارين."
                
            l1 = landmarks1[0]
            l2 = landmarks2[0]
            
            def get_distance(pt1, pt2):
                return math.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)
                
            # Compare distance between nose tip and chin bottom
            dist1 = get_distance(l1['nose_tip'][2], l1['chin'][8])
            dist2 = get_distance(l2['nose_tip'][2], l2['chin'][8])
            
            diff = abs(dist1 - dist2)
            
            # If the difference is extremely small, it's a static printed photo or a screen
            if diff < 0.5:
                return False, "لم يتم اكتشاف أي حركة طبيعية للوجه (صورة ثابتة)."

            # Verify the specific random challenge if provided
            # This defends against pre-recorded replay attacks.
            if challenge:
                if challenge == "smile":
                    mouth_w1 = get_distance(l1['top_lip'][0], l1['top_lip'][6])
                    mouth_w2 = get_distance(l2['top_lip'][0], l2['top_lip'][6])
                    mouth_h1 = get_distance(l1['top_lip'][3], l1['bottom_lip'][3])
                    mouth_h2 = get_distance(l2['top_lip'][3], l2['bottom_lip'][3])
                    # Require mouth to widen or open
                    if mouth_w2 - mouth_w1 < 1.0 and mouth_h2 - mouth_h1 < 1.0:
                        return False, "لم يتم تنفيذ التحدي المطلوب (الابتسامة)."
                elif challenge == "raise_eyebrows":
                    brow_dist1 = l1['left_eye'][0][1] - l1['left_eyebrow'][2][1]
                    brow_dist2 = l2['left_eye'][0][1] - l2['left_eyebrow'][2][1]
                    # Require eyebrows to go up (distance from eye increases)
                    if brow_dist2 - brow_dist1 < 1.0:
                        return False, "لم يتم تنفيذ التحدي المطلوب (رفع الحاجبين)."
                elif challenge == "turn_right":
                    nose_x1 = l1['nose_tip'][2][0]
                    nose_x2 = l2['nose_tip'][2][0]
                    # Require horizontal nose movement
                    if abs(nose_x2 - nose_x1) < 3.0:
                        return False, "لم يتم تنفيذ التحدي المطلوب (تحريك الرأس)."
                
        except Exception as e:
            return False, f"خطأ أثناء الفحص: {str(e)}"
            
    # 3. MiniFASNet Anti-Spoofing Check
    if fas_session is not None:
        try:
            start_time = time.time()
            face_img = cv2.resize(image_array_1, (80, 80))
            face_img = np.transpose(face_img, (2, 0, 1)).astype(np.float32)
            face_img = face_img / 255.0
            face_img = np.expand_dims(face_img, axis=0)
            
            out = fas_session.run(None, {fas_input_name: face_img})[0][0]
            
            def softmax(x):
                e_x = np.exp(x - np.max(x))
                return e_x / e_x.sum()
            
            probs = softmax(out)
            predicted_class = np.argmax(probs)
            real_prob = probs[1]
            
            latency = (time.time() - start_time) * 1000
            logging.getLogger(__name__).info(f"MiniFASNet inference latency: {latency:.2f}ms, real_prob: {real_prob:.4f}, class: {predicted_class}")
            
            # Require class 1 (real face) and high probability
            if predicted_class != 1 or real_prob < 0.6:
                return False, "تم اكتشاف محاولة احتيال (فحص النماذج)."
                
        except Exception as e:
            return False, f"خطأ أثناء فحص الاحتيال: {str(e)}"
            
    return True, "نجاح"



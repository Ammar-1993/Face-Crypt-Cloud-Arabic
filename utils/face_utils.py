import numpy as np
import face_recognition
import json
from PIL import Image
from io import BytesIO
from cryptography.fernet import Fernet
from app.config import SECRET_KEY
fernet = Fernet(SECRET_KEY.encode())


def load_image_from_request(file):
    """
    Loads an image from a Flask request file object.
    Ensures RGB format and converts to a NumPy array.
    """
    image = Image.open(BytesIO(file.read())).convert('RGB')
    image = image.resize((500, 500))  # Optional resize to standardize
    image_array = np.asarray(image, dtype=np.uint8)
    image_array = np.ascontiguousarray(image_array)
    return image_array

def extract_face_encoding(image_array):
    """
    Safely extracts the face encoding from a given image (NumPy array).
    Returns the first encoding found or raises ValueError.
    """
    try:
        if image_array.dtype != np.uint8:
            raise ValueError(f"Unsupported dtype: {image_array.dtype}")
        if len(image_array.shape) != 3 or image_array.shape[2] != 3:
            raise ValueError(f"Unsupported shape: {image_array.shape}")
        encodings = face_recognition.face_encodings(image_array)
        if len(encodings) == 0:
            raise ValueError("No face was detected. Please try again with a clear photo.")
        return encodings[0]
    except Exception as e:
        raise ValueError(f"Face encoding failed: {str(e)}")


def compare_encodings(known_encoding, unknown_encoding, tolerance=0.6):
    """
    Compares two face encodings.
    Returns True if they match within the given tolerance.
    """
    if known_encoding is None or unknown_encoding is None:
        raise ValueError("❌ One or both encodings are invalid.")
    results = face_recognition.compare_faces([known_encoding], unknown_encoding, tolerance=tolerance)
    return results[0]

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


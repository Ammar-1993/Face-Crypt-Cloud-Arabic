import firebase_admin
from firebase_admin import credentials, firestore, storage
from dotenv import load_dotenv
import os

# ✅ تحميل متغيرات البيئة
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# ✅ قراءة القيم
ADMIN_PASSWORD = os.environ.get('FACECRYPT_ADMIN_PASSWORD')
SERVICE_ACCOUNT_PATH = os.environ.get('FACECRYPT_SERVICE_ACCOUNT_PATH')
STORAGE_BUCKET = os.environ.get('FACECRYPT_STORAGE_BUCKET')
SECRET_KEY = os.environ.get('FACECRYPT_SECRET_KEY')

print(f"✅ Loaded SECRET_KEY = {SECRET_KEY}")
print(f"✅ Loaded ADMIN_PASSWORD: {ADMIN_PASSWORD}")
print(f"✅ Loaded SERVICE_ACCOUNT_PATH: {SERVICE_ACCOUNT_PATH}")
print(f"✅ Loaded STORAGE_BUCKET: {STORAGE_BUCKET}")

# ✅ إعداد Firebase
firebase_app = None
db = None
bucket = None

def initialize_firebase():
    global firebase_app, db, bucket

    if not firebase_admin._apps:
        cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
        firebase_app = firebase_admin.initialize_app(cred, {
            'storageBucket': STORAGE_BUCKET
        })
        print("✅ Firebase Admin SDK initialized in config.py")

    db = firestore.client()
    bucket = storage.bucket()

# ⚡ التهيئة التلقائية وقت الاستيراد!
initialize_firebase()

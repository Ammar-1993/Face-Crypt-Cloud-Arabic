import firebase_admin
from firebase_admin import credentials, firestore, storage
from dotenv import load_dotenv
import os
import logging

logger = logging.getLogger(__name__)

# ✅ تحميل متغيرات البيئة
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# ✅ قراءة القيم
ADMIN_PASSWORD = os.environ.get('FACECRYPT_ADMIN_PASSWORD')
SERVICE_ACCOUNT_PATH = os.environ.get('FACECRYPT_SERVICE_ACCOUNT_PATH')
STORAGE_BUCKET = os.environ.get('FACECRYPT_STORAGE_BUCKET')
SECRET_KEY = os.environ.get('FACECRYPT_SECRET_KEY')
FLASK_SECRET_KEY = os.environ.get('FACECRYPT_FLASK_SECRET_KEY')

missing_vars = []
if not ADMIN_PASSWORD: missing_vars.append('FACECRYPT_ADMIN_PASSWORD')
if not SERVICE_ACCOUNT_PATH: missing_vars.append('FACECRYPT_SERVICE_ACCOUNT_PATH')
if not STORAGE_BUCKET: missing_vars.append('FACECRYPT_STORAGE_BUCKET')
if not SECRET_KEY: missing_vars.append('FACECRYPT_SECRET_KEY')
if not FLASK_SECRET_KEY: missing_vars.append('FACECRYPT_FLASK_SECRET_KEY')

if missing_vars:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}")

logger.info("✅ SECRET_KEY loaded: %s", bool(SECRET_KEY))
logger.info("✅ ADMIN_PASSWORD loaded: %s", bool(ADMIN_PASSWORD))
logger.info("✅ Loaded SERVICE_ACCOUNT_PATH: %s", SERVICE_ACCOUNT_PATH)
logger.info("✅ Loaded STORAGE_BUCKET: %s", STORAGE_BUCKET)

ENABLE_LIVENESS_CHECK = os.environ.get('FACECRYPT_ENABLE_LIVENESS_CHECK', 'False').lower() in ('true', '1', 't')
logger.info("✅ ENABLE_LIVENESS_CHECK: %s", ENABLE_LIVENESS_CHECK)

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
        logger.info("✅ Firebase Admin SDK initialized in config.py")

    db = firestore.client()
    bucket = storage.bucket()

# ⚡ التهيئة التلقائية وقت الاستيراد!
initialize_firebase()

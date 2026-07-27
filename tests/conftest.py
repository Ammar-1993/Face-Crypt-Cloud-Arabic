import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Mock firebase_admin before importing the app to avoid real initialization
sys.modules['firebase_admin'] = MagicMock()
sys.modules['firebase_admin.credentials'] = MagicMock()
sys.modules['firebase_admin.firestore'] = MagicMock()
sys.modules['firebase_admin.storage'] = MagicMock()

# Set dummy environment variables to pass the configuration validation in app/config.py
os.environ.setdefault('FACECRYPT_ADMIN_PASSWORD', 'test_admin_password')
os.environ.setdefault('FACECRYPT_SERVICE_ACCOUNT_PATH', 'test_path.json')
os.environ.setdefault('FACECRYPT_STORAGE_BUCKET', 'test.appspot.com')
os.environ.setdefault('FACECRYPT_SECRET_KEY', 'R7kyQt7z69lzAyu1NQEFYvJYb0preezrytAENnh7src=')
os.environ.setdefault('FACECRYPT_FLASK_SECRET_KEY', 'R7kyQt7z69lzAyu1NQEFYvJYb0preezrytAENnh7src=')

from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_firebase():
    with patch('utils.firebase_utils.add_user_to_firestore') as mock_add_user, \
         patch('utils.firebase_utils.delete_user_from_firestore') as mock_delete_user, \
         patch('utils.firebase_utils.get_all_users') as mock_get_all, \
         patch('utils.firebase_utils.update_user_fields') as mock_update_user, \
         patch('utils.firebase_utils.log_audit_event') as mock_log_audit:
        
        # Configure default return values
        mock_get_all.return_value = []

        yield {
            'add_user_to_firestore': mock_add_user,
            'delete_user_from_firestore': mock_delete_user,
            'get_all_users': mock_get_all,
            'update_user_fields': mock_update_user,
            'log_audit_event': mock_log_audit
        }

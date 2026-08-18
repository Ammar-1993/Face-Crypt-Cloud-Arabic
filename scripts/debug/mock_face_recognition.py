import sys
from unittest.mock import MagicMock
sys.modules['face_recognition'] = MagicMock()
import app.config as config
from app import create_app

app = create_app()

with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['admin_logged_in'] = True
    
    response = client.get('/admin/stats')
    print("Status:", response.status_code)
    print("Data:", response.get_json())

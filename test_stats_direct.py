from app import create_app
from flask import json
import app.config as config

app = create_app()

with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['admin_logged_in'] = True
    
    response = client.get('/admin/stats')
    print("Status:", response.status_code)
    print("Data:", response.get_json())

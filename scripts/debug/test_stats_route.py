from app import create_app
from flask import session

app = create_app()

with app.test_client() as client:
    # Need to simulate login
    with client.session_transaction() as sess:
        sess['admin_logged_in'] = True
    
    response = client.get('/admin/stats')
    print("Response JSON:")
    print(response.json)

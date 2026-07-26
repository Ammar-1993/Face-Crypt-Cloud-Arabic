with open('tests/test_admin_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add a fixture for authenticated client or modify existing tests.
# Instead of complex AST manipulation, let's just use string replace.

# 1. Update test_admin_list_users
test_admin_list_users_new = """def test_admin_list_users_unauthenticated(client, mock_firebase):
    response = client.get('/admin/list_users')
    assert response.status_code == 401

def test_admin_list_users(client, mock_firebase):
    \"\"\"Test /admin/list_users GET request.\"\"\"
    # Mock the return data from firebase_utils
    mock_firebase['get_all_users'].return_value = [
        {'id': 'test_user_1', 'name': 'John Doe', 'email': 'john@example.com', 'blocked': False}
    ]
    
    with client.session_transaction() as sess:
        sess['admin_logged_in'] = True
    response = client.get('/admin/list_users')
    assert response.status_code == 200
"""
content = content.replace('def test_admin_list_users(client, mock_firebase):\n    """Test /admin/list_users GET request."""\n    # Mock the return data from firebase_utils\n    mock_firebase[\'get_all_users\'].return_value = [\n        {\'id\': \'test_user_1\', \'name\': \'John Doe\', \'email\': \'john@example.com\', \'blocked\': False}\n    ]', test_admin_list_users_new.split('\n    response = client.get')[0])

# 2. Update test_admin_delete_user
test_admin_delete_user_new = """def test_admin_delete_user_unauthenticated(client, mock_firebase):
    response = client.post('/admin/delete_user', json={'user_id': 'test_user_123'})
    assert response.status_code == 401

def test_admin_delete_user(client, mock_firebase):
    \"\"\"Test /admin/delete_user POST request.\"\"\"
    with client.session_transaction() as sess:
        sess['admin_logged_in'] = True
    response = client.post('/admin/delete_user', json={'user_id': 'test_user_123'})"""
content = content.replace('def test_admin_delete_user(client, mock_firebase):\n    """Test /admin/delete_user POST request."""\n    response = client.post(\'/admin/delete_user\', json={\'user_id\': \'test_user_123\'})', test_admin_delete_user_new)

# 3. Update test_admin_audit_logs
test_admin_audit_logs_new = """def test_admin_audit_logs_unauthenticated(client, mock_firebase):
    response = client.get('/admin/audit_logs')
    assert response.status_code == 401

@patch('app.admin.routes.db')
def test_admin_audit_logs(mock_db, client, mock_firebase):
    \"\"\"Test /admin/audit_logs GET request.\"\"\"
    # Setup mock to return an empty list when stream() is called
    mock_stream = MagicMock()
    mock_stream.stream.return_value = []
    mock_db.collection.return_value = mock_stream
    
    with client.session_transaction() as sess:
        sess['admin_logged_in'] = True
    response = client.get('/admin/audit_logs')"""
content = content.replace('@patch(\'app.admin.routes.db\')\ndef test_admin_audit_logs(mock_db, client, mock_firebase):\n    """Test /admin/audit_logs GET request."""\n    # Setup mock to return an empty list when stream() is called\n    mock_stream = MagicMock()\n    mock_stream.stream.return_value = []\n    mock_db.collection.return_value = mock_stream\n    \n    response = client.get(\'/admin/audit_logs\')', test_admin_audit_logs_new)

# 4. Update test_admin_stats
test_admin_stats_new = """def test_admin_stats_unauthenticated(client, mock_firebase):
    response = client.get('/admin/stats')
    assert response.status_code == 401

@patch('app.admin.routes.config.db')
def test_admin_stats(mock_config_db, client, mock_firebase):
    \"\"\"Test /admin/stats GET request.\"\"\"
    # Setup mock to return an empty list when stream() is called for logs and users
    mock_stream = MagicMock()
    mock_stream.stream.return_value = []
    mock_config_db.collection.return_value = mock_stream
    
    # Setup mock_firebase get_all_users to return empty for total_users calculation
    mock_firebase['get_all_users'].return_value = []
    
    with client.session_transaction() as sess:
        sess['admin_logged_in'] = True
    response = client.get('/admin/stats')"""
content = content.replace('@patch(\'app.admin.routes.config.db\')\ndef test_admin_stats(mock_config_db, client, mock_firebase):\n    """Test /admin/stats GET request."""\n    # Setup mock to return an empty list when stream() is called for logs and users\n    mock_stream = MagicMock()\n    mock_stream.stream.return_value = []\n    mock_config_db.collection.return_value = mock_stream\n    \n    # Setup mock_firebase get_all_users to return empty for total_users calculation\n    mock_firebase[\'get_all_users\'].return_value = []\n    \n    response = client.get(\'/admin/stats\')', test_admin_stats_new)

with open('tests/test_admin_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated tests")

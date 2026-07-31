import pytest
from unittest.mock import patch, MagicMock

def test_admin_login_success(client, mock_firebase):
    """Test /admin/login with correct password."""
    with patch('app.admin.routes.ADMIN_PASSWORD', 'secret_pass'):
        response = client.post('/admin/login', json={'password': 'secret_pass'})
        assert response.status_code == 200
        assert 'message' in response.json

def test_admin_login_failure(client, mock_firebase):
    """Test /admin/login with incorrect password."""
    with patch('app.admin.routes.ADMIN_PASSWORD', 'secret_pass'):
        response = client.post('/admin/login', json={'password': 'wrong_pass'})
        assert response.status_code == 403
        assert 'error' in response.json

def test_admin_list_users_unauthenticated(client, mock_firebase):
    response = client.get('/admin/list_users')
    assert response.status_code == 401
    
    data = response.json
    assert 'error' in data

def test_admin_list_users(client, mock_firebase):
    """Test /admin/list_users GET request."""
    mock_firebase['get_all_users'].return_value = [
        {'name': 'John Doe', 'id': 'test_user_1'}
    ]
    with client.session_transaction() as sess:
        sess['admin_logged_in'] = True
    response = client.get('/admin/list_users')
    assert response.status_code == 200
    
    data = response.json
    assert 'users' in data
    assert len(data['users']) == 1
    assert data['users'][0]['name'] == 'John Doe'
    assert data['users'][0]['id'] == 'test_user_1'

def test_admin_delete_user_unauthenticated(client, mock_firebase):
    response = client.post('/admin/delete_user', json={'user_id': 'test_user_123'})
    assert response.status_code == 403

def test_admin_delete_user(client, mock_firebase):
    """Test /admin/delete_user POST request."""
    with client.session_transaction() as sess:
        sess['admin_logged_in'] = True
        sess['csrf_token'] = 'test_token'
    response = client.post('/admin/delete_user', json={'user_id': 'test_user_123'}, headers={'X-CSRFToken': 'test_token'})
    assert response.status_code == 200
    assert 'message' in response.json
    
    # Assert that our mock was called exactly once with the correct parameter
    mock_firebase['delete_user_from_firestore'].assert_called_once_with('test_user_123')

def test_admin_audit_logs_unauthenticated(client, mock_firebase):
    response = client.get('/admin/audit_logs')
    assert response.status_code == 401

@patch('app.admin.routes.db')
def test_admin_audit_logs(mock_db, client, mock_firebase):
    """Test /admin/audit_logs GET request."""
    # Setup mock to return an empty list when stream() is called
    mock_stream = MagicMock()
    mock_stream.stream.return_value = []
    mock_db.collection.return_value = mock_stream
    
    with client.session_transaction() as sess:
        sess['admin_logged_in'] = True
    response = client.get('/admin/audit_logs')
    assert response.status_code == 200
    
    data = response.json
    assert 'logs' in data
    assert isinstance(data['logs'], list)

def test_admin_stats_unauthenticated(client, mock_firebase):
    response = client.get('/admin/stats')
    assert response.status_code == 401

@patch('app.admin.routes.config.db')
def test_admin_stats(mock_config_db, client, mock_firebase):
    """Test /admin/stats GET request."""
    mock_collection = MagicMock()
    mock_config_db.collection.return_value = mock_collection
    
    mock_count = MagicMock()
    mock_get = MagicMock()
    mock_agg_result = MagicMock()
    mock_agg_result.value = 0
    mock_get.return_value = [[mock_agg_result]]
    mock_count.get = mock_get
    
    mock_collection.count.return_value = mock_count
    mock_collection.where.return_value.count.return_value = mock_count
    mock_collection.stream.return_value = []
    
    with client.session_transaction() as sess:
        sess['admin_logged_in'] = True
    response = client.get('/admin/stats')
    assert response.status_code == 200
    
    data = response.json
    expected_keys = [
        "total_attempts", "success_attempts", "failed_attempts", 
        "blocked_events", "soft_block_events", "blocked_users_count", 
        "total_users", "soft_blocked_users_count"
    ]
    
    for key in expected_keys:
        assert key in data

def test_admin_add_user_xss_prevention(client, mock_firebase):
    import io
    with client.session_transaction() as sess:
        sess['admin_logged_in'] = True
        sess['csrf_token'] = 'test_token'
    data = {
        'user_id': '<script>alert(1)</script>',
        'name': 'Test Name',
        'email': 'test@test.com',
        'image': (io.BytesIO(b"fake image data"), 'test.jpg')
    }
    response = client.post('/admin/add_user', data=data, content_type='multipart/form-data', headers={'X-CSRFToken': 'test_token'})
    assert response.status_code == 400
    assert 'غير صالح' in response.json['error']

    data['user_id'] = 'valid_id'
    data['name'] = '<img src=x onerror=alert(1)>'
    data['image'] = (io.BytesIO(b"fake image data"), 'test.jpg')
    response = client.post('/admin/add_user', data=data, content_type='multipart/form-data', headers={'X-CSRFToken': 'test_token'})
    assert response.status_code == 400
    assert 'رموز غير مسموحة' in response.json['error']

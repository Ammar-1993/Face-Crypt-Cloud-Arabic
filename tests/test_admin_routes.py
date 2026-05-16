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

def test_admin_list_users(client, mock_firebase):
    """Test /admin/list_users GET request."""
    # Mock the return data from firebase_utils
    mock_firebase['get_all_users'].return_value = [
        {'id': 'test_user_1', 'name': 'John Doe', 'email': 'john@example.com', 'blocked': False}
    ]
    
    response = client.get('/admin/list_users')
    assert response.status_code == 200
    
    data = response.json
    assert 'users' in data
    assert len(data['users']) == 1
    assert data['users'][0]['name'] == 'John Doe'
    assert data['users'][0]['id'] == 'test_user_1'

def test_admin_delete_user(client, mock_firebase):
    """Test /admin/delete_user POST request."""
    response = client.post('/admin/delete_user', json={'user_id': 'test_user_123'})
    assert response.status_code == 200
    assert 'message' in response.json
    
    # Assert that our mock was called exactly once with the correct parameter
    mock_firebase['delete_user_from_firestore'].assert_called_once_with('test_user_123')

@patch('app.admin.routes.db')
def test_admin_audit_logs(mock_db, client, mock_firebase):
    """Test /admin/audit_logs GET request."""
    # Setup mock to return an empty list when stream() is called
    mock_stream = MagicMock()
    mock_stream.stream.return_value = []
    mock_db.collection.return_value = mock_stream
    
    response = client.get('/admin/audit_logs')
    assert response.status_code == 200
    
    data = response.json
    assert 'logs' in data
    assert isinstance(data['logs'], list)

@patch('app.admin.routes.config.db')
def test_admin_stats(mock_config_db, client, mock_firebase):
    """Test /admin/stats GET request."""
    # Setup mock to return an empty list when stream() is called for logs and users
    mock_stream = MagicMock()
    mock_stream.stream.return_value = []
    mock_config_db.collection.return_value = mock_stream
    
    # Setup mock_firebase get_all_users to return empty for total_users calculation
    mock_firebase['get_all_users'].return_value = []
    
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

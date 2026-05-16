import pytest
import io
import time
from unittest.mock import patch, MagicMock

def test_missing_image_error(client, mock_firebase):
    """Test login without an image file."""
    response = client.post('/users/verify_login', data={})
    assert response.status_code == 400
    assert 'error' in response.json

@patch('app.users.routes.face_utils.load_image_from_request')
@patch('app.users.routes.face_utils.extract_face_encoding')
@patch('app.users.routes.face_utils.decrypt_encoding')
@patch('app.users.routes.face_utils.compare_encodings')
def test_successful_login(mock_compare, mock_decrypt, mock_extract, mock_load, client, mock_firebase):
    """Test a successful login scenario."""
    # Setup mocks
    mock_compare.return_value = True
    mock_decrypt.return_value = [0.1, 0.2, 0.3] # Dummy encoding list
    mock_extract.return_value = [0.1, 0.2, 0.3]
    mock_load.return_value = MagicMock()

    # Mock user data
    mock_firebase['get_all_users'].return_value = [
        {
            'id': 'user123',
            'name': 'Test User',
            'email': 'test@example.com',
            'face_encoding': 'dummy_encrypted_string',
            'blocked': False,
            'soft_block': False
        }
    ]

    # Dummy file
    data = {
        'image': (io.BytesIO(b"fake image data"), 'test.jpg')
    }

    response = client.post('/users/verify_login', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    assert 'message' in response.json
    assert 'تم تسجيل الدخول بنجاح' in response.json['message']
    assert 'user' in response.json
    assert response.json['user']['id'] == 'user123'

@patch('app.users.routes.face_utils.load_image_from_request')
@patch('app.users.routes.face_utils.extract_face_encoding')
@patch('app.users.routes.face_utils.decrypt_encoding')
@patch('app.users.routes.face_utils.compare_encodings')
def test_login_failure_mismatch(mock_compare, mock_decrypt, mock_extract, mock_load, client, mock_firebase):
    """Test login failure due to face mismatch."""
    mock_compare.return_value = False
    mock_decrypt.return_value = [0.1, 0.2, 0.3]
    mock_extract.return_value = [0.9, 0.8, 0.7]
    mock_load.return_value = MagicMock()

    mock_firebase['get_all_users'].return_value = [
        {
            'id': 'user123',
            'face_encoding': 'dummy_encrypted_string',
            'blocked': False,
            'soft_block': False
        }
    ]

    data = {
        'image': (io.BytesIO(b"fake image data"), 'test.jpg')
    }

    response = client.post('/users/verify_login', data=data, content_type='multipart/form-data')
    assert response.status_code == 403
    assert 'message' in response.json
    assert 'فشل تسجيل الدخول' in response.json['message']

@patch('app.users.routes.face_utils.load_image_from_request')
@patch('app.users.routes.face_utils.extract_face_encoding')
def test_soft_block_trigger(mock_extract, mock_load, client, mock_firebase):
    """Test anti-brute force mechanism (soft block)."""
    mock_extract.return_value = [0.1, 0.2, 0.3]
    mock_load.return_value = MagicMock()

    # Mock user data with soft_block active
    mock_firebase['get_all_users'].return_value = [
        {
            'id': 'user123',
            'face_encoding': 'dummy_encrypted_string',
            'failed_attempts': 3,
            'soft_block': True,
            'soft_block_time': int(time.time()) # Blocked right now
        }
    ]

    data = {
        'image': (io.BytesIO(b"fake image data"), 'test.jpg')
    }

    response = client.post('/users/verify_login', data=data, content_type='multipart/form-data')
    assert response.status_code == 403
    assert 'message' in response.json
    assert 'تم تجاوز عدد المحاولات الفاشلة' in response.json['message']

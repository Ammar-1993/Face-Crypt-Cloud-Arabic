import pytest
import io
import time
from unittest.mock import patch, MagicMock

def test_missing_image_error(client, mock_firebase):
    """Test login without an image file."""
    response = client.post('/users/verify_login', data={})
    assert response.status_code == 400
    assert 'error' in response.json

@patch('app.users.routes.ENABLE_LIVENESS_CHECK', new=False)
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
    assert 'فشل تسجيل الدخول' in response.json['message']

@patch('app.users.routes.face_utils.load_image_from_request')
@patch('app.users.routes.face_utils.extract_face_encoding')
@patch('app.users.routes.face_utils.decrypt_encoding')
@patch('app.users.routes.face_utils.compare_encodings')
def test_anti_enumeration(mock_compare, mock_decrypt, mock_extract, mock_load, client, mock_firebase):
    """Test that NO-MATCH and MATCH-BLOCKED yield exactly the same public HTTP response."""
    # 1. Test No Match
    mock_compare.return_value = False
    mock_decrypt.return_value = [0.1]
    mock_extract.return_value = [0.9]
    mock_load.return_value = MagicMock()
    mock_firebase['get_all_users'].return_value = [
        {'id': 'user1', 'face_encoding': 'dummy', 'blocked': False, 'soft_block': False}
    ]
    data_no_match = {'image': (io.BytesIO(b"fake image data"), 'test.jpg')}
    res_no_match = client.post('/users/verify_login', data=data_no_match, content_type='multipart/form-data')

    # 2. Test Match but Blocked
    mock_compare.return_value = True
    mock_firebase['get_all_users'].return_value = [
        {'id': 'user1', 'face_encoding': 'dummy', 'blocked': True, 'soft_block': False}
    ]
    data_blocked = {'image': (io.BytesIO(b"fake image data"), 'test.jpg')}
    res_blocked = client.post('/users/verify_login', data=data_blocked, content_type='multipart/form-data')

    # Compare identical outputs
    assert res_no_match.status_code == res_blocked.status_code == 403
    assert res_no_match.json == res_blocked.json
    assert 'فشل تسجيل الدخول' in res_no_match.json['message']

@patch('app.users.routes.firebase_utils.update_user_fields')
@patch('app.users.routes.face_utils.load_image_from_request')
@patch('app.users.routes.face_utils.extract_face_encoding')
@patch('app.users.routes.face_utils.decrypt_encoding')
@patch('app.users.routes.face_utils.compare_encodings')
def test_failed_login_does_not_penalize_all_users(mock_compare, mock_decrypt, mock_extract, mock_load, mock_update, client, mock_firebase):
    """Test that a failed login doesn't penalize all users in the system."""
    mock_compare.return_value = False
    mock_decrypt.return_value = [0.1, 0.2, 0.3]
    mock_extract.return_value = [0.9, 0.8, 0.7]
    mock_load.return_value = MagicMock()

    mock_firebase['get_all_users'].return_value = [
        {
            'id': 'user1',
            'face_encoding': 'dummy1',
            'blocked': False,
            'soft_block': False
        },
        {
            'id': 'user2',
            'face_encoding': 'dummy2',
            'blocked': False,
            'soft_block': False
        }
    ]

    data = {
        'image': (io.BytesIO(b"fake image data"), 'test.jpg')
    }

    response = client.post('/users/verify_login', data=data, content_type='multipart/form-data')
    assert response.status_code == 403
    
    # Assert that no users were updated/penalized
    mock_update.assert_not_called()

@patch('app.users.routes.generate_registration_options')
def test_webauthn_register_begin(mock_generate, client, mock_firebase):
    """Test webauthn registration begins successfully for authenticated user."""
    mock_firebase['get_all_users'].return_value = [{'id': 'user123', 'name': 'Test User', 'email': 'test@example.com'}]
    
    mock_options = MagicMock()
    mock_options.challenge = b'test_challenge'
    mock_options.json.return_value = '{"challenge": "dGVzdF9jaGFsbGVuZ2U"}'
    mock_generate.return_value = mock_options

    with client.session_transaction() as sess:
        sess['user_id'] = 'user123'

    response = client.post('/users/webauthn/register/begin')
    assert response.status_code == 200
    assert 'challenge' in response.json
    mock_generate.assert_called_once()

def test_webauthn_register_begin_unauthorized(client):
    """Test webauthn registration begin rejects unauthenticated requests."""
    response = client.post('/users/webauthn/register/begin')
    assert response.status_code == 401

@patch('app.users.routes.verify_registration_response')
@patch('app.users.routes.firebase_utils.update_user_fields')
def test_webauthn_register_complete_success(mock_update, mock_verify, client):
    """Test successful webauthn registration completion."""
    with client.session_transaction() as sess:
        sess['user_id'] = 'user123'
        sess['webauthn_challenge'] = 'dGVzdF9jaGFsbGVuZ2U'

    mock_verification = MagicMock()
    mock_verification.credential_id = b'cred_id'
    mock_verification.credential_public_key = b'pub_key'
    mock_verify.return_value = mock_verification

    response = client.post('/users/webauthn/register/complete', json={'id': 'test', 'rawId': 'test', 'type': 'public-key'})
    assert response.status_code == 200
    assert response.json['status'] == 'success'
    mock_update.assert_called_once()
    assert 'webauthn_credential_id' in mock_update.call_args[0][1]

@patch('app.users.routes.verify_registration_response')
def test_webauthn_register_complete_invalid(mock_verify, client):
    """Test webauthn registration complete handles verification failure."""
    with client.session_transaction() as sess:
        sess['user_id'] = 'user123'
        sess['webauthn_challenge'] = 'dGVzdF9jaGFsbGVuZ2U'

    mock_verify.side_effect = Exception("Invalid credential")

    response = client.post('/users/webauthn/register/complete', json={'id': 'invalid'})
    assert response.status_code == 400
    assert 'error' in response.json

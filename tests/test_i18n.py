import pytest
from flask import session
import json

def test_language_switch_success(client):
    """Test switching to English works and sets session correctly."""
    response = client.get('/set-language/en', base_url="https://localhost")
    assert response.status_code in [200, 302]
    with client.session_transaction() as sess:
        assert sess.get('locale') == 'en'

def test_language_switch_invalid(client):
    """Test switching to an unsupported language returns 400."""
    response = client.get('/set-language/fr', base_url="https://localhost")
    assert response.status_code == 400

def test_subsequent_request_translation(client):
    """Test that a backend API returns an English string via Accept-Language fallback."""
    # By sending Accept-Language: en, get_locale() will return 'en' if session is empty.
    response = client.post('/users/verify_login', headers={"Accept-Language": "en"})
    data = json.loads(response.data)
    
    assert response.status_code == 400
    assert "No image provided" in data.get('error', '')

import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# --- Mock firebase_admin BEFORE importing the app to prevent real initialization ---
sys.modules['firebase_admin'] = MagicMock()
sys.modules['firebase_admin.credentials'] = MagicMock()
sys.modules['firebase_admin.firestore'] = MagicMock()
sys.modules['firebase_admin.storage'] = MagicMock()

# Set valid dummy environment variables to bypass the fail-fast config check in app/config.py
os.environ.setdefault('FACECRYPT_ADMIN_PASSWORD', 'test_admin_password')
os.environ.setdefault('FACECRYPT_SERVICE_ACCOUNT_PATH', 'test_path.json')
os.environ.setdefault('FACECRYPT_STORAGE_BUCKET', 'test.appspot.com')
os.environ.setdefault('FACECRYPT_SECRET_KEY', 'R7kyQt7z69lzAyu1NQEFYvJYb0preezrytAENnh7src=')
os.environ.setdefault('FACECRYPT_FLASK_SECRET_KEY', 'R7kyQt7z69lzAyu1NQEFYvJYb0preezrytAENnh7src=')

from app import create_app

# --- Custom Firestore Mocks ---
class MockQuery:
    """Simulates a Firestore Query object (e.g. .where(...))"""
    def __init__(self, docs):
        self.docs = docs

    def stream(self):
        # Return a list of MagicMocks simulating Firestore DocumentSnapshots
        return [MagicMock(to_dict=lambda d=doc: d) for doc in self.docs]

    def where(self, field, op, value):
        if op == '==':
            filtered_docs = [doc for doc in self.docs if doc.get(field) == value]
            return MockQuery(filtered_docs)
        return self

class MockCollection:
    """Simulates a Firestore CollectionReference"""
    def __init__(self, docs):
        self.query = MockQuery(docs)
    
    def stream(self):
        return self.query.stream()
        
    def where(self, field, op, value):
        return self.query.where(field, op, value)


@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        # Simulate an active admin session to bypass the @login_required decorator
        with client.session_transaction() as sess:
            sess['admin_logged_in'] = True
        yield client


@patch('app.admin.routes.config.db.collection')
def test_admin_dashboard_stats(mock_db_collection, client):
    """
    Verifies the statistical mathematical logic of the Admin Dashboard.
    """
    # 1. Create a mock dataset simulating various states
    mock_audit_logs = [
        {"status": "success"},
        {"status": "success"},
        {"status": "success"},
        {"status": "failure"},
        {"status": "failure"},
        {"status": "blocked"},    # Permanent ban event
        {"status": "soft_block"}  # Temporary ban event
    ] # Total Expected Attempts: 7

    mock_users = [
        {"blocked": False, "soft_block": False},  # Active
        {"blocked": False, "soft_block": False},  # Active
        {"blocked": True, "soft_block": False},   # Permanently Banned
        {"blocked": False, "soft_block": True},   # Temporarily Banned
        {"blocked": False, "soft_block": True},   # Temporarily Banned
    ] # Total Expected Users: 5

    def side_effect(collection_name):
        if collection_name == 'audit_logs':
            return MockCollection(mock_audit_logs)
        elif collection_name == 'users':
            return MockCollection(mock_users)
        return MockCollection([])

    # Attach our mock router to the db.collection() call
    mock_db_collection.side_effect = side_effect

    # 2. Call the statistics aggregation endpoint
    response = client.get('/admin/stats')
    
    assert response.status_code == 200
    data = response.get_json()

    # 3. Assert mathematical logic is perfectly accurate
    calculated_total = (data['success_attempts'] + 
                        data['failed_attempts'] + 
                        data['blocked_events'] + 
                        data['soft_block_events'])
                        
    assert data['total_attempts'] == calculated_total, \
        f"Logic Error: Expected sum is {calculated_total} but got {data['total_attempts']}"

    # 4. Assert that counting users by status matches the mocked documents
    assert data['total_attempts'] == 7
    assert data['success_attempts'] == 3
    assert data['failed_attempts'] == 2
    assert data['blocked_events'] == 1
    assert data['soft_block_events'] == 1
    
    assert data['total_users'] == 5
    assert data['blocked_users_count'] == 1
    assert data['soft_blocked_users_count'] == 2

    # 5. Generate a simulated summary report in the terminal output
    print("\n\n" + "="*50)
    print(" 📊 Admin Dashboard Statistics - QA Test Report ")
    print("="*50)
    print(f"✅ Mathematical Logic Verified: Total ({data['total_attempts']}) == " 
          f"Success ({data['success_attempts']}) + Fail ({data['failed_attempts']}) + "
          f"Perm Ban ({data['blocked_events']}) + Temp Ban ({data['soft_block_events']})")
    print(f"✅ Total Users Counted: {data['total_users']} (Expected: 5)")
    print(f"✅ Banned Users (Permanent): {data['blocked_users_count']} (Expected: 1)")
    print(f"✅ Banned Users (Temporary): {data['soft_blocked_users_count']} (Expected: 2)")
    print("="*50 + "\n")

from datetime import datetime
from firebase_admin import firestore
import pytz

from app.config import db

def add_user_to_firestore(user_id, user_data):
    """
    Adds a new user document to the Firestore 'users' collection.
    user_id: The unique identifier for the user.
    user_data: A dictionary containing user information.
    """
    doc_ref = db.collection('users').document(user_id)
    doc_ref.set(user_data)
    print(f"✅ User {user_id} added to Firestore.")

def delete_user_from_firestore(user_id):
    """
    Deletes a user document from the Firestore 'users' collection by user_id.
    """
    doc_ref = db.collection('users').document(user_id)
    doc_ref.delete()
    print(f"✅ User {user_id} deleted from Firestore.")

def get_all_users():
    """
    Retrieves all user documents from the Firestore 'users' collection.
    Returns a list of user dictionaries, each including the user's ID.
    """
    users = []
    docs = db.collection('users').stream()
    for doc in docs:
        user = doc.to_dict()
        user['id'] = doc.id
        users.append(user)
    print(f"✅ Retrieved {len(users)} users.")
    return users

def log_audit_event(user_id, event, status=None, ip_address=None):
    """
    Logs an audit event to the Firestore 'audit_logs' collection.
    Records the user_id, event type, timestamp, and optionally status and IP address.
    """
    local_tz = pytz.timezone("Asia/Riyadh")
    local_time = datetime.now(local_tz).isoformat()

    event_data = {
        'user_id': user_id,
        'event': event,
        'timestamp': local_time
    }

    if status:
        event_data['status'] = status

    if ip_address:
        event_data['ip_address'] = ip_address

    db.collection('audit_logs').document().set(event_data)
    print(f"✅ Logged event: {event_data}")

def update_user_fields(user_id, data):
    """
    Updates specific fields for a user document in the Firestore 'users' collection.
    user_id: The unique identifier for the user.
    data: A dictionary of fields to update.
    """
    doc_ref = db.collection('users').document(user_id)
    doc_ref.update(data)
    print(f"✅ Updated user {user_id} with: {data}")
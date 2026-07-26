from datetime import datetime
from firebase_admin import firestore
import pytz
import logging

logger = logging.getLogger(__name__)

from app.config import db

def add_user_to_firestore(user_id, user_data):
    """
    Adds a new user document to the Firestore 'users' collection.
    user_id: The unique identifier for the user.
    user_data: A dictionary containing user information.
    """
    doc_ref = db.collection('users').document(user_id)
    if doc_ref.get().exists:
        raise ValueError(f"المستخدم بالمعرف {user_id} موجود مسبقاً.")
    doc_ref.set(user_data)
    logger.info("✅ User %s added to Firestore.", user_id)

def delete_user_from_firestore(user_id):
    """
    Deletes a user document from the Firestore 'users' collection by user_id.
    """
    doc_ref = db.collection('users').document(user_id)
    doc_ref.delete()
    logger.info("✅ User %s deleted from Firestore.", user_id)

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
    logger.info("✅ Retrieved %d users.", len(users))
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
    logger.info("✅ Logged event '%s' for user '%s'", event, user_id)

def update_user_fields(user_id, data):
    """
    Updates specific fields for a user document in the Firestore 'users' collection.
    user_id: The unique identifier for the user.
    data: A dictionary of fields to update.
    """
    doc_ref = db.collection('users').document(user_id)
    doc_ref.update(data)
    logger.info("✅ Updated user %s with keys: %s", user_id, list(data.keys()))
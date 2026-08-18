from app import create_app
from flask import json
import app.config as config
from utils import firebase_utils

app = create_app()

with app.app_context():
    # Insert a dummy blocked event and user for testing
    firebase_utils.log_audit_event("dummy", "Test_Event", status="blocked", ip_address="127.0.0.1")
    firebase_utils.log_audit_event("dummy", "Test_Event", status="soft_block", ip_address="127.0.0.1")
    
    # Update a user to be blocked
    try:
        firebase_utils.add_user_to_firestore("dummy_user", {"blocked": True, "soft_block": True})
    except Exception:
        pass
    firebase_utils.update_user_fields("dummy_user", {"blocked": True, "soft_block": True})

    # Now run the stats query logic
    logs_ref = config.db.collection('audit_logs')
    def get_count(query):
        return query.count().get()[0][0].value

    try:
        total = get_count(logs_ref)
        success = get_count(logs_ref.where('status', '==', 'success'))
        failure = get_count(logs_ref.where('status', '==', 'failure'))
        blocked_events = get_count(logs_ref.where(filter=firestore.FieldFilter('status', '==', 'blocked'))) # wait, where('status', '==', 'blocked')
        # Let's just run what admin_stats runs
        blocked_events = get_count(logs_ref.where('status', '==', 'blocked'))
        soft_block_events = get_count(logs_ref.where('status', '==', 'soft_block'))
        
        users_ref = config.db.collection('users').stream()
        blocked_users = 0
        soft_blocked_users = 0
        total_users = 0

        for doc in users_ref:
            u = doc.to_dict()
            total_users += 1
            if u.get('blocked', False):
                blocked_users += 1
            if u.get('soft_block', False):
                soft_blocked_users += 1

        print("total:", total)
        print("blocked_events:", blocked_events)
        print("soft_block_events:", soft_block_events)
        print("blocked_users:", blocked_users)
        print("soft_blocked_users:", soft_blocked_users)
    except Exception as e:
        print("ERROR:", e)


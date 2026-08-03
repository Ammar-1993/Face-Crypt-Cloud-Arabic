import firebase_admin
from firebase_admin import credentials, firestore
cred = credentials.Certificate('firebase/serviceAccountKey.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Insert a dummy liveness ban event
db.collection('audit_logs').document().set({
    'user_id': 'unknown_user',
    'event': 'Spoofing_Attempt',
    'status': 'blocked',
    'timestamp': '2026-08-03T07:07:00'
})

logs_ref = db.collection('audit_logs')

def get_count(query):
    return query.count().get()[0][0].value

print("total:", get_count(logs_ref))
print("blocked:", get_count(logs_ref.where('status', '==', 'blocked')))


import firebase_admin
from firebase_admin import credentials, firestore
cred = credentials.Certificate('firebase/serviceAccountKey.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

db.collection('audit_logs').document().set({
    'user_id': 'test',
    'event': 'User_Login',
    'status': 'blocked',
    'timestamp': '2026-08-03T07:07:00'
})

db.collection('users').document('test_user').set({
    'blocked': True,
    'soft_block': False
})

query = db.collection("audit_logs").where("status", "==", "blocked")
count_query = query.count()
res = count_query.get()
print("blocked events count:", res[0][0].value)

users_ref = db.collection('users').stream()
blocked_users = 0
for u in users_ref:
    if u.to_dict().get('blocked', False):
        blocked_users += 1
print("blocked users count:", blocked_users)

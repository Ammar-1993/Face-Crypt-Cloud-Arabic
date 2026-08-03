import firebase_admin
from firebase_admin import credentials, firestore
cred = credentials.Certificate('firebase/serviceAccountKey.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

query = db.collection("audit_logs").where("status", "==", "blocked")
count_query = query.count()
res = count_query.get()
print("res:", res)
print("type(res):", type(res))
if res:
    print("res[0]:", res[0])
    print("res[0][0]:", res[0][0])
    print("res[0][0].value:", res[0][0].value)

users_ref = db.collection('users').stream()
blocked_users = 0
soft_blocked_users = 0

for doc in users_ref:
    u = doc.to_dict()
    if u.get('blocked', False):
        blocked_users += 1
    if u.get('soft_block', False):
        soft_blocked_users += 1
print("Blocked users:", blocked_users)
print("Soft blocked users:", soft_blocked_users)

docs = query.stream()
print("blocked audit_logs:", len(list(docs)))

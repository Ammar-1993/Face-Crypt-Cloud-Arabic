import firebase_admin
from firebase_admin import credentials, firestore
cred = credentials.Certificate('firebase/serviceAccountKey.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

query = db.collection('empty_collection').where('status', '==', 'blocked')
try:
    res = query.count().get()
    print("res:", res)
    print("value:", res[0][0].value)
except Exception as e:
    print("Error:", e)

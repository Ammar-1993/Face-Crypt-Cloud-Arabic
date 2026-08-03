from app.config import db
logs_ref = db.collection('audit_logs')
print(len(list(logs_ref.where('status', '==', 'blocked').stream())))

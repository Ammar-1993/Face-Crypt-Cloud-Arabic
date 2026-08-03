from app import create_app
from app.config import db

app = create_app()
with app.app_context():
    docs = db.collection('audit_logs').stream()
    logs = [d.to_dict() for d in docs]
    print(f"Total logs: {len(logs)}")
    
    blocked = [l for l in logs if l.get('status') == 'blocked']
    print(f"Blocked logs: {len(blocked)}")
    
    soft_blocked = [l for l in logs if l.get('status') == 'soft_block']
    print(f"Soft blocked logs: {len(soft_blocked)}")
    
    users = db.collection('users').stream()
    u_list = [u.to_dict() for u in users]
    print(f"Total users: {len(u_list)}")
    print(f"Blocked users: {len([u for u in u_list if u.get('blocked')])}")
    print(f"Soft blocked users: {len([u for u in u_list if u.get('soft_block')])}")

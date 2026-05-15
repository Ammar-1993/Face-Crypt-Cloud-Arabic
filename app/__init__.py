import os
from flask import Flask
from app import config
from app.routes import bp as routes_bp
from app.users.routes import users_bp
from app.admin.routes import admin_bp



def create_app():
    app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'),
    template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates')
)

    
    # تهيئة Firebase
    config.initialize_firebase()

    # تسجيل الـ Blueprints
    app.register_blueprint(routes_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(admin_bp)


    print("✅ Flask App created and routes registered.")
    return app

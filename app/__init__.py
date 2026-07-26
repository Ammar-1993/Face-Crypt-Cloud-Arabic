import os
import logging
from flask import Flask

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
from app import config
from app.routes import bp as routes_bp
from app.users.routes import users_bp
from app.admin.routes import admin_bp



def create_app():
    from datetime import timedelta
    app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'),
    template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates')
)
    app.config['SECRET_KEY'] = config.FLASK_SECRET_KEY
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SECURE'] = True
    
    # تهيئة Firebase
    config.initialize_firebase()

    # تسجيل الـ Blueprints
    from app.limiter import limiter
    limiter.init_app(app)
    
    app.register_blueprint(routes_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(admin_bp)

    import traceback
    from flask import jsonify

    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.error("Unhandled Exception: %s\n%s", str(e), traceback.format_exc())
        
        if app.debug:
            return jsonify({"error": f"❌ خطأ داخلي: {str(e)}"}), 500
            
        return jsonify({"error": "❌ خطأ داخلي في الخادم. يرجى المحاولة مرة أخرى لاحقاً."}), 500


    logger.info("✅ Flask App created and routes registered.")
    return app

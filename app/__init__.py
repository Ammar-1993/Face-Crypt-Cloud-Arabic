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

from flask import session, request, redirect, jsonify
from flask_babel import Babel

babel = Babel()

def get_locale():
    if 'locale' in session:
        return session['locale']
    return request.accept_languages.best_match(['ar', 'en']) or 'ar'



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
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB limit
    
    # تهيئة Firebase
    config.initialize_firebase()

    # تسجيل الـ Blueprints
    from app.limiter import limiter
    limiter.init_app(app)
    
    app.register_blueprint(routes_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(admin_bp)

    app.config['BABEL_TRANSLATION_DIRECTORIES'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'translations')
    # تهيئة Babel
    babel.init_app(app, locale_selector=get_locale)

    # Inject get_locale for templates
    @app.context_processor
    def inject_locale():
        from flask_babel import get_locale
        return {'get_locale': lambda: str(get_locale())}


    @app.route('/set-language/<lang_code>')
    def set_language(lang_code):
        if lang_code not in ['ar', 'en']:
            return jsonify({"error": "Invalid language code"}), 400
        session['locale'] = lang_code
        return redirect(request.referrer or '/')


    import traceback
    from flask import jsonify, request, render_template
    from werkzeug.exceptions import HTTPException

    def wants_json_response():
        if request.path.startswith('/admin') or request.path.startswith('/users'):
            return True
        return request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html

    @app.errorhandler(404)
    def page_not_found(e):
        if wants_json_response():
            return jsonify({"error": "المورد غير موجود (404)."}), 404
        return render_template('404.html'), 404

    @app.errorhandler(Exception)
    def handle_exception(e):
        # Pass through normal HTTP errors (404, 405, etc.) so they aren't logged as 500s
        if isinstance(e, HTTPException):
            return e
            
        logger.error("Unhandled Exception: %s\n%s", str(e), traceback.format_exc())
        
        error_msg = f"❌ خطأ داخلي: {str(e)}" if app.debug else "❌ خطأ داخلي في الخادم. يرجى المحاولة مرة أخرى لاحقاً."
        
        if wants_json_response():
            return jsonify({"error": error_msg}), 500
            
        return render_template('500.html'), 500
    @app.errorhandler(413)
    def request_entity_too_large(error):
        logger.warning("Request Entity Too Large: %s", str(error))
        return jsonify({"error": "❌ حجم الملف كبير جداً. الحد الأقصى المسموح به هو 5 ميغابايت."}), 413

    @app.errorhandler(429)
    def ratelimit_handler(error):
        logger.warning("Rate limit exceeded: %s", str(error))
        return jsonify({"error": f"❌ عذراً، تم تجاوز الحد المسموح من الطلبات: {error.description}"}), 429



    logger.info("✅ Flask App created and routes registered.")
    return app

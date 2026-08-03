from flask import Blueprint, render_template, request, redirect, url_for

bp = Blueprint('routes', __name__)

from app.limiter import limiter

@bp.route('/')
@limiter.exempt
def index():
    message = request.args.get('message')
    return render_template('index.html', message=message)


@bp.route('/health')
def health():
    return "✅ Server is healthy!", 200

@bp.route('/verify')
@limiter.exempt
def verify():
    return render_template('verification.html')




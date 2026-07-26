from flask import Blueprint, render_template, request, redirect, url_for

bp = Blueprint('routes', __name__)

@bp.route('/')
def index():
    message = request.args.get('message')
    return render_template('index.html', message=message)


@bp.route('/health')
def health():
    return "✅ Server is healthy!", 200




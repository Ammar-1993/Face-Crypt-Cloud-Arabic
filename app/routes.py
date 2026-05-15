from flask import Blueprint, render_template, request, redirect, url_for
from app.config import db, bucket

from app.services.storage_service import upload_file
from app.services.firestore_service import log_upload


bp = Blueprint('routes', __name__)

@bp.route('/')
def index():
    message = request.args.get('message')
    return render_template('index.html', message=message)


@bp.route('/health')
def health():
    return "✅ Server is healthy!", 200

@bp.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return redirect(url_for('routes.index', message="❌ No file part."))

    file = request.files['image']
    if file.filename == '':
        return redirect(url_for('routes.index', message="❌ No selected file."))

    # رفع إلى Firebase Storage
    public_url = upload_file(file)

    # تسجيل في Firestore
    log_upload(file.filename, public_url)

    return redirect(url_for('routes.index', message=f"✅ Uploaded {file.filename} successfully!"))




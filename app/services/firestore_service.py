from app.config import db


def log_upload(filename, url):
    """
    Saves upload details to Firestore.
    """
    doc_ref = db.collection('uploads').document()
    doc_ref.set({
        'filename': filename,
        'url': url
    })
    print(f"✅ Firestore: Saved {filename}")

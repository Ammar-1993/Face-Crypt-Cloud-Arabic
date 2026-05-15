from app.config import bucket

def upload_file(file):
    """
    Uploads a file to Firebase Storage and returns its public URL.
    """
    blob = bucket.blob(file.filename)
    blob.upload_from_file(file)
    print(f"✅ Storage: Uploaded {file.filename}")
    return blob.public_url

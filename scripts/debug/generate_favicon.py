import sys
from PIL import Image

try:
    img = Image.open('static/images/face_crypt_cloud_logo.png')
    img.resize((32, 32), Image.Resampling.LANCZOS).save('static/images/favicon-32x32.png')
    img.resize((16, 16), Image.Resampling.LANCZOS).save('static/images/favicon-16x16.png')
    print("Success")
except Exception as e:
    print(f"Error: {e}")

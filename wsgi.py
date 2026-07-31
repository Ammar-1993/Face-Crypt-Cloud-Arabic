import os
from app import create_app
from waitress import serve

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    # Face recognition is CPU-bound. Threads should ideally match CPU cores.
    default_threads = os.cpu_count() or 4
    threads = int(os.environ.get('FACECRYPT_WSGI_THREADS', default_threads))
    print(f"Starting Waitress WSGI server on port {port} with {threads} threads...")
    serve(app, host='0.0.0.0', port=port, threads=threads)

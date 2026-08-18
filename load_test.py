import time
import requests
import concurrent.futures
import random
import uuid

URL = "https://face-crypt-cloud-184918603595.us-central1.run.app/users/verify_login"
IMAGE_PATH = "static/images/face_crypt_cloud_logo.png"

def send_request(req_id):
    try:
        start_time = time.time()
        # Create a unique boundary or dummy IP if needed, but we can't reliably spoof without ProxyFix maybe.
        # But we only send 10 requests anyway.
        with open(IMAGE_PATH, 'rb') as f:
            files = {'image': ('image.png', f, 'image/png')}
            response = requests.post(URL, files=files, headers={'X-Forwarded-For': f'10.0.{random.randint(0,255)}.{random.randint(0,255)}'})
        elapsed = time.time() - start_time
        return req_id, response.status_code, elapsed
    except Exception as e:
        return req_id, str(e), 0

def main():
    concurrency = 8
    total_requests = 10
    print(f"Starting load test: {total_requests} requests with concurrency {concurrency}...")
    
    start_total = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(send_request, i) for i in range(total_requests)]
        
        for future in concurrent.futures.as_completed(futures):
            req_id, status_code, elapsed = future.result()
            print(f"Request {req_id} completed with status {status_code} in {elapsed:.2f}s")
            
    total_elapsed = time.time() - start_total
    print(f"\nTotal time: {total_elapsed:.2f}s")

if __name__ == '__main__':
    main()

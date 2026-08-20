# 🐳 WSL2 + Docker Setup Guide — Face Crypt Cloud

A precise, step-by-step guide for running Face Crypt Cloud in a Docker container on Windows Subsystem for Linux 2 (WSL2). Covers environment preparation, container build, test verification, and the HTTPS quirk required for admin panel testing.

---

## ✅ Prerequisites Already in Place

The following concerns are **fully handled** in the current codebase — no manual intervention needed:

| Item | Status | Details |
|---|---|---|
| `opencv-python-headless` | ✅ Confirmed | `requirements.txt` uses `opencv-python-headless==5.0.0.93` — the headless variant required for server environments without a display. Do not change this. |
| `.env.example` variable names | ✅ Confirmed | All variable names in `.env.example` are **identical** to what `app/config.py` reads. The `FACECRYPT_` prefix is consistent across the entire codebase. |
| `pytest.ini` testpath isolation | ✅ Confirmed | `pytest.ini` restricts test discovery exclusively to the `tests/` directory, preventing any accidental execution of one-off debug scripts in the project root. |
| Secrets excluded from Docker image | ✅ Confirmed | `.dockerignore` explicitly excludes `.env`, `.env.*`, and `firebase/serviceAccountKey.json` — they are injected at runtime only. |

---

## 1. WSL2 Environment Preparation

### 1.1 Enable Docker Integration

**Option A — Docker Desktop (recommended for most users):**
Open Docker Desktop → **Settings → Resources → WSL Integration** → enable your Ubuntu distribution (e.g., `Ubuntu-22.04`).

**Option B — Docker Engine directly inside WSL2 (no Docker Desktop):**
Follow the [official Docker Engine install guide for Ubuntu](https://docs.docker.com/engine/install/ubuntu/), then either:
- Start Docker manually each session: `sudo service docker start`
- Or enable systemd permanently by adding the following to `/etc/wsl.conf`:
  ```ini
  [boot]
  systemd=true
  ```

### 1.2 Allocate Sufficient Resources for dlib Compilation

The first `docker compose build` compiles `dlib` from source — a CPU and memory-intensive operation. Configure WSL2 resource limits before building:

Create or edit `%UserProfile%\.wslconfig` on the **Windows side**:

```ini
[wsl2]
memory=8GB
processors=4
swap=4GB
```

Apply the changes from a **Windows PowerShell** prompt:
```powershell
wsl --shutdown
```

Then reopen your WSL2 terminal. The new limits will be in effect.

### 1.3 Fix Line Endings (Critical for Shell Scripts)

Prevent CRLF-related script failures inside Linux containers by configuring Git globally:

```bash
git config --global core.autocrlf input
```

### 1.4 Work From the WSL2 Filesystem

> **Important:** Always work from a path within the WSL2 filesystem (e.g., `/home/ammar/code/Face-Crypt-Cloud`), **not** from a Windows-mounted path like `/mnt/c/...`.

Working from `/mnt/c/` routes all file I/O through the 9P protocol bridge between Windows and Linux, which is significantly slower and can cause file permission issues with Docker bind mounts. Use VS Code with the **"Remote - WSL"** extension pointed at your WSL2 path for the best development experience.

---

## 2. Key Configuration Files

These files are already present in the repository root. Review them before building:

| File | Purpose |
|---|---|
| [`Dockerfile`](./Dockerfile) | Multi-stage build: Stage 1 compiles `dlib` + all dependencies into wheel files; Stage 2 is the lean runtime image that installs from those pre-built wheels. |
| [`docker-compose.yml`](./docker-compose.yml) | Development config: bind-mounts the source directory into the container (`.:/app`) for live code changes, runs `python app.py` (Flask dev server with auto-reload). |
| [`.dockerignore`](./.dockerignore) | Excludes secrets, virtual environments, cache files, and documentation from the Docker build context. |
| [`pytest.ini`](./pytest.ini) | Restricts `pytest` to the `tests/` directory. Prevents any debug scripts in the project root from touching real Firestore data. |
| [`Caddyfile`](./Caddyfile) | Optional local HTTPS reverse proxy config (see [Section 4](#4-admin-panel--the-https-requirement)). |

---

## 3. Step-by-Step: First-Time Setup & Run

```bash
# Step 1 — Clone the repository (skip if already cloned)
git clone https://github.com/Ammar-1993/Face-Crypt-Cloud-Arabic.git
cd Face-Crypt-Cloud-Arabic

# Step 2 — Create your environment file from the template
cp .env.example .env
nano .env
# Fill in all required values:
#   FACECRYPT_SECRET_KEY        — generate with: python -c "import secrets; print(secrets.token_hex(32))"
#   FACECRYPT_FLASK_SECRET_KEY  — generate with the same command (use a different value)
#   FACECRYPT_ADMIN_PASSWORD    — your chosen admin password
#   FACECRYPT_SERVICE_ACCOUNT_PATH — path to your Firebase key (default: firebase/serviceAccountKey.json)
#   FACECRYPT_STORAGE_BUCKET    — your Firebase project's storage bucket

# Step 3 — Place your Firebase service account key at the configured path
ls -la firebase/serviceAccountKey.json   # Confirm it exists before building

# Step 4 — Build the Docker image
# The first build compiles dlib from source — expect 5–15 minutes.
# Subsequent builds use Docker's layer cache and are much faster.
docker compose build

# Step 5 — Start the container in the background
docker compose up -d

# Step 6 — Confirm the server is responding
curl http://localhost:8081/health
# Expected: HTTP 200 OK

# Step 7 — Run the full test suite inside the container
docker compose exec app pytest -v
# Expected: 26 passed
```

Open **`http://localhost:8081`** in your browser for the user-facing verification portal.

---

## 4. Admin Panel — The HTTPS Requirement

> **Why does the admin panel login fail on plain HTTP?**

The application sets `SESSION_COOKIE_SECURE = True` in `app/__init__.py`. This is a browser security standard: the session cookie that authenticates the admin is **only transmitted over HTTPS**. On a plain `http://` connection, the browser silently drops the cookie, and every admin request appears unauthenticated — even after a "successful" login.

**Impact:** The public face-verification flow (`/verify`) works fine over HTTP. Only the admin panel (`/admin/`) requires HTTPS.

### Enabling Local HTTPS With Caddy

A `caddy` service is included in `docker-compose.yml` (commented out by default). Caddy auto-generates and locally trusts a TLS certificate — no manual certificate setup required.

**To activate it:**

1. Open `docker-compose.yml` and uncomment the `caddy` service block.
2. Restart the stack:
   ```bash
   docker compose down
   docker compose up -d
   ```
3. Access the admin panel at **`https://localhost:8443`**.

> On first visit, your browser may show a certificate warning. Accept it once (or run `caddy trust` inside the Caddy container). Caddy uses `tls internal` to issue a locally-trusted certificate via its built-in CA, as configured in [`Caddyfile`](./Caddyfile):
> ```
> localhost:8443 {
>     tls internal
>     reverse_proxy app:8080
> }
> ```

---

## 5. Development Workflow

### Live Code Reloading

`docker-compose.yml` bind-mounts the project root into the container (`.:/app`) and runs `python app.py` (Flask's built-in dev server). Any file you edit on the host is immediately reflected inside the container — **no image rebuild required**.

```bash
# After editing a Python file, Flask auto-reloads. Watch the logs:
docker compose logs -f app
```

### Running Tests During Development

```bash
# Run the full test suite
docker compose exec app pytest -v

# Run a specific test file
docker compose exec app pytest tests/test_user_routes.py -v

# Run a single test by name
docker compose exec app pytest -v -k "test_login_success"
```

### Rebuilding the Image

Only needed when `requirements.txt` changes or `Dockerfile` is modified:

```bash
docker compose build --no-cache   # Full clean rebuild
docker compose up -d
```

### Viewing Logs

```bash
docker compose logs -f            # Follow all service logs
docker compose logs -f app        # Follow only the Flask app
```

### Stopping the Stack

```bash
docker compose down               # Stop and remove containers
docker compose down -v            # Also remove anonymous volumes (clears __pycache__)
```

---

## 6. Production vs. Development Mode

The `docker-compose.yml` overrides the `Dockerfile`'s default command (`python wsgi.py` / Waitress) with `python app.py` (Flask dev server) for local development convenience. The differences are:

| Aspect | Development (`app.py`) | Production (`wsgi.py`) |
|---|---|---|
| Server | Flask built-in dev server | Waitress WSGI |
| Auto-reload | ✅ Yes (when `FLASK_DEBUG=True`) | ❌ No |
| Thread count | Single-threaded by default | `FACECRYPT_WSGI_THREADS` (defaults to CPU core count) |
| Performance | Not suitable for real load | Production-grade |
| Use case | Local development | Cloud Run / VPS |

**To test the production Waitress path locally**, comment out (or remove) the `command:` line in `docker-compose.yml`:

```yaml
# command: ["python", "app.py"]   # ← comment this out
```

The container will then use the `Dockerfile`'s default `CMD ["python", "wsgi.py"]`.

---

## 7. Final Verification Checklist

Work through this checklist after your first successful build:

- [ ] `.env` created from `.env.example` with all five required secrets filled in
- [ ] `firebase/serviceAccountKey.json` exists at the path set in `FACECRYPT_SERVICE_ACCOUNT_PATH`
- [ ] `docker compose build` completed without errors
- [ ] `curl http://localhost:8081/health` returns HTTP 200
- [ ] `docker compose exec app pytest -v` reports **26 passed, 0 failed**
- [ ] Face login works via `http://localhost:8081`
- [ ] *(If Caddy enabled)* Admin panel login works via `https://localhost:8443`
- [ ] Editing a source file is reflected in the running container without a rebuild

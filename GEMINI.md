# Face-Crypt-Cloud: Gemini Development Session Notes

This document summarizes the actions, changes, and notes recorded during this development session, primarily focused on hardening the security and resilience of the application.

## 1. Information Disclosure & Enumeration Prevention
- **Normalized Login Responses:** Modified `app/users/routes.py` so that attempts yielding "not matched", "matched but blocked", and "matched but soft-blocked" all return an identical, generic HTTP 403 response (`"Login failed. Please try again or contact an administrator if the problem persists."`).
- **Internal Auditing Maintained:** Ensured that while the public API response is generic, the internal `firebase_utils.log_audit_event` continues to log exact reasons (e.g., `blocked`, `soft_block`, `failure`) for the admin dashboard.
- **Regression Testing:** Added a test case in `tests/test_user_routes.py` to confirm that the public API responses are indistinguishable between these failure states.

## 2. Timing Attack Mitigation
- **Constant-Time Comparison:** Replaced standard equality operators (`==`) with `hmac.compare_digest(password, ADMIN_PASSWORD)` in `app/admin/routes.py` for admin authentication. This prevents attackers from executing timing attacks to guess the secret admin password character by character.

## 3. Global Error Handling & Preventing Traceback Leaks
- **Centralized Error Handler:** Introduced a global `@app.errorhandler(Exception)` in `app/__init__.py`. 
- **Non-Revealing Responses:** Replaced localized, overly permissive `except Exception as e: return str(e)` blocks across the app with the centralized handler. It now returns a generic HTTP 500 error (`"Internal server error. Please try again later."`) in production.
- **Debug Mode Guard:** The centralized handler conditionally returns detailed tracebacks only if the `FLASK_DEBUG` environment variable is explicitly set to `True`.

## 4. Dependency Security Audit & CI/CD
- **Dependency Upgrades:** Audited `requirements.txt` and upgraded several outdated packages with known CVEs to secure versions, including `Pillow`, `numpy`, `opencv-python`, `Flask`, `cryptography`, and `werkzeug`.
- **Automated Pipeline:** Added a GitHub Actions workflow (`.github/workflows/security_audit.yml`) that automatically runs `pip-audit` on every code push to prevent vulnerable dependencies from being introduced in the future.

## 5. Denial-of-Service (DoS) Mitigation
- **Max Content Length:** Configured `app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024` (5MB) in `app/__init__.py`. This caps the size of image uploads, preventing attackers from overloading the server's CPU with massive images during the intensive face-encoding extraction process.
- **Graceful Handling:** Added a specific 413 (Payload Too Large) error handler to return a friendly JSON response when an upload exceeds the limit.
- **Documentation:** Documented the 5MB upload limit restriction in `README.md`.

## 6. Firestore Defense-in-Depth
- **Security Rules:** Added a `firestore.rules` file to the root of the repository that explicitly denies all direct client-side read/write access to the `users` and `audit_logs` collections (`allow read, write: if false;`).
- **Safety Net:** Since the Flask backend uses the Firebase Admin SDK (which bypasses these rules), the application remains functional. However, if a client-side Firebase SDK is ever accidentally introduced into the frontend in the future, these rules will block direct access to the database.

## 7. Cross-Site Request Forgery (CSRF) Protection
- **Custom CSRF Implementation:** Implemented a lightweight, custom CSRF protection mechanism without bloating the app with `Flask-WTF`.
- **Token Generation:** Configured `/admin/login` to generate a secure 32-byte token (`secrets.token_hex(32)`) and store it in `session['csrf_token']`.
- **Frontend Injection:** Updated `static/js/admin_portal.js` to securely hold the token in memory and automatically attach it as an `X-CSRFToken` header for all state-changing requests via `adminFetch()`.
- **Backend Validation:** Added an `@admin_bp.before_request` hook that intercepts all `POST`, `PUT`, `PATCH`, and `DELETE` requests in the admin panel to validate the token using `hmac.compare_digest`.
- **Testing:** Updated `tests/test_admin_routes.py` to seamlessly inject the CSRF headers, maintaining 100% test pass rates.

## 8. Secure Configuration & Production Readiness
- **Insecure Default Session Secret:** Removed the hardcoded fallback for `FLASK_SECRET_KEY` in `app/config.py` that would silently allow attackers to forge valid admin sessions and bypass CSRF protections if the environment variable was omitted. The application now fails fast on startup with a strict `RuntimeError` explicitly listing all missing variables.
- **Environment Variable Standardization:** Enforced a consistent `FACECRYPT_` prefix for all application-specific secrets across both the codebase (`app/config.py`) and documentation (`README.md`), removing ambiguity and potential Firebase initialization crashes.
- **Production Deployment Guidance:** Added a comprehensive "Production Deployment" section in `README.md` containing TLS reverse proxy (Nginx) configuration examples and Waitress setup instructions.
- **HTTPS Enforcement:** Documented that because `SESSION_COOKIE_SECURE = True` is set, the application strictly requires HTTPS in production, otherwise the admin login will silently fail as browsers drop the non-secure session cookies.

## 9. Robust Global Error Handling
- **HTTPException Passthrough:** Corrected an overreach in the global `@app.errorhandler(Exception)` located in `app/__init__.py`. It previously intercepted all `werkzeug.exceptions.HTTPException` events (like 404 Not Found), triggering false positive 500 Internal Server Error logs and overriding standard HTTP responses. Standard HTTP errors are now gracefully passed through to Werkzeug's native handlers.

## 10. Fixing Broken Test Pipeline & Environment Safety
- **Test Environment Injection:** Fixed a critical bug in `tests/conftest.py` where a strict environment variable check in `app/config.py` caused `pytest` to immediately crash on import for fresh environments. Added `os.environ.setdefault()` calls for all five required secrets prior to importing the Flask application factory.
- **Valid Cryptographic Keys:** Instead of using arbitrary text, the mocked `FACECRYPT_SECRET_KEY` and `FACECRYPT_FLASK_SECRET_KEY` were initialized with valid 32-byte URL-safe base64 strings generated via `cryptography.fernet.Fernet.generate_key()`. This prevents immediate `ValueError` crashes in `face_utils` during initialization, restoring the 100% test pass rate locally and in CI.

## 11. CORS Safety & Relative Paths
- **API Base Fix:** Addressed a severe security/deployment risk in `static/js/admin_portal.js` by changing the hardcoded `const API_BASE = "http://127.0.0.1:8081";` to a relative path `const API_BASE = "";`. This implicitly eliminates CORS issues and ensures cross-domain session cookies (and CSRF tokens) securely travel over the same origin in production.

## 12. Repository Hygiene & Dead Artifact Cleanup
- **Pruned Stale Files:** Removed legacy utility scripts in the project root (e.g. `check_structure.py`, `update_tests.py`, `script_firebase_utils.py`), unneeded templates like `index2.html`, and a large unused compiled artifact (`dlib-*.whl` - 2.9MB).
- **Cleaned Static Assets:** Identified and safely deleted 29 unused legacy images from `static/images/`, keeping only the verified active asset (`face_crypt_cloud_logo.png`).


## 13. Dynamic Face Recognition Tolerance (Admin Dashboard)
- **Backend Refactoring:** Located the hardcoded `tolerance` parameter in `utils/face_utils.py` and updated the comparison functions to dynamically fetch this setting from a new `settings/security_config` Firestore document, with a fallback to `0.6`. Added helper functions in `utils/firebase_utils.py` to handle these database reads/writes.
- **Admin API Endpoints:** Created secure `GET` and `POST` endpoints at `/admin/api/settings/tolerance` in `app/admin/routes.py`. These endpoints are guarded by `@login_required` and the existing custom CSRF validation. Added server-side validation to enforce that the tolerance remains strictly between `0.1` and `1.0`. All changes are logged to the `audit_logs` collection.
- **Global Error Handling Fix:** Updated the `POST /admin/api/settings/tolerance` endpoint to utilize `request.get_json(silent=True)` combined with a broad `try...except Exception as e` block. This ensures that even if a request lacks the `Content-Type: application/json` header, Werkzeug does not throw a 400 Bad Request HTTP exception (which would historically bypass JSON formatting and return an HTML error page). Instead, the backend consistently returns a predictable JSON response (`{"success": False, "error": ...}`) for seamless frontend handling.
- **Frontend UI & Flexbox Layout:** Integrated a new "Advanced Security Settings" (إعدادات الأمان المتقدمة) section into `templates/index_admin.html`. Used Bootstrap Flexbox (`d-flex align-items-center`) to construct a perfect Right-to-Left (RTL) layout where the Save button aligns left, the interactive range slider expands in the center, and the numeric Value Badge sits on the right.
- **Neon Aesthetic CSS:** Added specialized styling (`.neon-control-box`, `.custom-range-glow`, `.neon-btn`) inside `static/css/admin_portal.css` to match the "Dark Glassmorphism" aesthetic. Fixed a CSS diagnostic warning by specifying standard `appearance: none;` alongside the `-webkit-appearance: none;` vendor prefixes.
- **Asynchronous Data Handling:** Programmed `static/js/admin_portal.js` to initialize the slider value via `GET` on page load, dynamically update the numeric UI as the slider moves, and submit updates using the `adminFetch()` wrapper (which automatically injects the `X-CSRFToken`). Implemented a loading spinner and SweetAlert2 integration for robust UX feedback.

## 14. ML-based Anti-Spoofing (Liveness Check)
- **Model Integration:** Downloaded the open-source `MiniFASNetV2.onnx` model (Apache 2.0 license) and integrated it using `onnxruntime` as a third layer of defense in `utils/face_utils.py`'s `check_liveness()`.
- **Global Initialization:** Modified `utils/face_utils.py` to load the `onnxruntime.InferenceSession` exactly once globally on app startup, successfully eliminating per-request loading latency.
- **Latency Benchmarking:** Benchmarked the inference time locally, confirming the MiniFASNet model is exceptionally lightweight, averaging **~2.7 ms** per request on CPU.
- **Fallback Security:** The checks are strictly aggregated. The face must now pass the Laplacian blur check, the active challenge, AND receive a >60% genuine probability from MiniFASNet to be accepted.

## 15. CI Pipeline Stabilization (conftest.py Import Order)
- **Root Cause Identified:** A GitHub Actions CI failure on `pytest` was traced to a premature import in `tests/conftest.py` (`from utils.firebase_utils import get_security_config`). This triggered the strict environment validation checks in `app/config.py` *before* the mocked `os.environ.setdefault()` credentials could be injected.
- **Fix:** Removed the premature import. All environment variables are now correctly mocked before the Flask app factory initializes, restoring a 100% pass rate in CI.

## 16. Active Random Challenge (Pre-recorded Replay Defense)
- **Frontend Interaction:** Updated `static/js/user_portal.js` to randomly select and display a challenge (e.g., "ابتسم", "أدر رأسك يمينًا", "ارفع حاجبيك") using SweetAlert2 during the two-frame capture flow. The challenge code is appended to the submitted `formData`.
- **Backend Verification:** Enhanced `check_liveness()` in `utils/face_utils.py` to accept the `challenge` parameter. Using `dlib`'s facial landmarks (via `face_recognition`), the system calculates geometric changes between the two frames (e.g., mouth width expansion for a smile, horizontal nose movement for turning, eyebrow distance from eyes for raising eyebrows).
- **Threat Model Clarity:** Documented explicitly in both code comments and `README.md` that this defense mitigates pre-recorded replay attacks (where a static video cannot react to a just-in-time random prompt) but is not designed to defeat real-time deepfake puppeteering.
- **Testing:** Added `test_check_liveness_active_challenge_mismatch` in `tests/test_face_utils.py` which mocks a face that moves slightly (passing the generic static photo check) but fails to perform the requested specific challenge, successfully resulting in a rejection.

## 17. WebAuthn (Passkey) Integration
- **Dependency Added:** Integrated the `webauthn` (Duo Labs' `py_webauthn`) package to handle the server-side FIDO2/WebAuthn logic, alongside base64url data conversion utilities. 
- **Database Schema Update:** Allowed two new fields (`webauthn_credential_id`, `webauthn_public_key`) inside each user's Firestore document.
- **Secure Registration Routes:** Added `POST /users/webauthn/register/begin` and `POST /users/webauthn/register/complete`. Both routes mandate an active, verified face-based session (`session['user_id']`), preventing arbitrary key assignment to unauthenticated users.
- **Frontend Ceremony:** Augmented `static/js/user_portal.js` so that a successful login conditionally presents a "🔑 تسجيل مفتاح مرور لهذا الجهاز" button inside the SweetAlert2 success modal. This button coordinates the `navigator.credentials.create()` browser API with the backend endpoints to securely generate and store the public key. 
- **Unit Testing:** Wrote tests (`test_webauthn_register_begin`, `test_webauthn_register_complete_success`, `test_webauthn_register_complete_invalid`, and unauthorized blocks) leveraging `unittest.mock.patch` to bypass real `py_webauthn` processing in CI, verifying the logic behaves securely under various payload conditions.

## 18. Frontend Client-Side Liveness & Face Tracking (MediaPipe JS)
- **Architectural Shift:** Completely removed the experimental Python `mediapipe` dependency to prevent massive Docker bloat (~300MB) and unresolvable `protobuf` conflicts with Firebase `grpcio` packages.
- **Frontend Integration:** Injected `@mediapipe/tasks-vision` via CDN into `templates/verification.html`.
- **Real-time Face Mesh:** Added an `<canvas>` overlay to the webcam feed in `static/js/user_portal.js` to draw real-time face tracking landmarks at 60 FPS, greatly improving the UX.
- **Client-side Active Challenge:** The active challenge (Smile, Turn Head, Raise Eyebrows) is now performed instantly in the browser using MediaPipe Blendshapes (`mouthSmileLeft`, `headTurnRight`, `browInnerUp`) rather than sending two separate frames to the backend.
- **Bandwidth Optimization:** The frontend automatically triggers capture upon challenge completion and only sends a single frame to the backend.
- **Backend Integrity:** The Flask backend `check_liveness` gracefully handles the absence of the second frame and continues to enforce the server-side `MiniFASNet` ONNX AI anti-spoofing model to prevent client-side bypass attacks. The `dlib` shape predictor remains strictly used for the 128-D cryptographic extraction to maintain parity with the database.

## 19. Bug Fixes, Resilience & Testing Enhancements (Session 2)
- **Warning Suppression:** Addressed test suite noise by explicitly configuring the `Flask-Limiter` storage backend to `"memory://"` in `app/limiter.py` and ignoring a third-party `pkg_resources` deprecation warning from `face_recognition_models` via `pytest.ini`. This results in a perfectly clean, warning-free test output.
- **Manual Testing Documentation:** Created a comprehensive `manual_testing_plan.md` in the project root containing step-by-step instructions for testing admin operations, user flows, passkeys, DoS/Rate limiting defenses, and edge cases like Soft-Block brute force triggering, admin unblocking, and CSRF protection verification.
- **Admin Portal Asynchronous Data Fix:** Resolved a `401 Unauthorized` API error that triggered on the `/admin` page load. The tolerance slider was prematurely fetching data before the admin session was established. Restructured `static/js/admin_portal.js` to defer the `/admin/api/settings/tolerance` fetch until *after* successful password authentication.
- **CSS CDN Resilience:** Fixed a `net::ERR_NAME_NOT_RESOLVED` error caused by an external outage at `cdnjs.cloudflare.com`. Downloaded `animate.min.css` from an alternative CDN and hosted it locally at `static/css/animate.min.css`, updating `templates/index_admin.html` to eliminate external stylesheet dependencies and improve resilience.
- **MediaPipe AI Framework Upgrade:** Addressed a critical `404 Not Found` and MIME type error for the MediaPipe `vision_bundle.js`. The previously pinned version `@0.10.3` experienced structural CDN changes. Upgraded the integration in both `templates/verification.html` and `static/js/user_portal.js` to the newer, stable `@1.0.1` release.
- **Restored Liveness Challenge Prompts:** Fixed a silent failure where the active challenge (e.g., "Smile") was being skipped. The upgrade to MediaPipe `1.0.1` nested the exported classes under a `window.Vision` object. Updated the Javascript destructuring in `static/js/user_portal.js` (`const { FaceLandmarker, FilesetResolver } = window.Vision || window;`) to correctly hook into the model, fully restoring the client-side active challenge flow.


## 20. Bilingual Support & Internationalization (Session 3)
- **Flask-Babel Integration:** Added dynamic session-based locale switching via `/set-language/<lang>` utilizing `Flask-Babel`. Fixed a critical context inheritance issue where the application factory pattern caused `app.root_path` to resolve incorrectly, breaking backend translations. Explicitly bound `BABEL_TRANSLATION_DIRECTORIES` to restore API translation functionality.
- **Template & API Localization:** Wrapped all user-facing strings across `index.html`, `verification.html`, `index_admin.html`, and backend JSON APIs with Jinja/Babel `_()` functions. Extracted and compiled complete `.po` and `.mo` message catalogs for the `en` locale.
- **Client-Side Translation Engine (Vanilla JS):** Abstracted all JavaScript-driven text (e.g., SweetAlerts, dynamic DOM injection) into a central `translations.js` mapping dictionary. Deployed a native `t(key)` helper function to enable immediate client-side switching without full page reloads.
- **CSS Logical Properties Refactor (Native RTL/LTR):** Systematically audited and refactored physical directional CSS rules (`margin-left`, `right`, `padding-left`) into modern CSS logical properties (`margin-inline-start`, `inset-inline-end`). The UI now natively adapts and mirrors layouts perfectly between Arabic (RTL) and English (LTR) utilizing the `dir` HTML attribute, eliminating duplicate code.
- **Language Toggle UI:** Integrated a sleek, mobile-responsive `AR | EN` language toggle switch seamlessly into the main navigation bars across all templates.
- **I18n Test Suite Robustness:** Rewrote `pytest` assertions to evaluate structural JSON payloads and HTTP status codes instead of hardcoded localized text, preventing CI pipeline failures across different locales. Added `tests/test_i18n.py` to assert route redirection and translation fallback behavior (34/34 tests passing).

## 21. AI Anti-Spoofing Preprocessing Fix (Session 3)
- **MiniFASNet Image Cropping:** Investigated user reports of repeated "Login Failed" and spoofing blockades. Discovered a bug where the backend was shrinking the entire 640x480 webcam frame to an 80x80 tensor, blinding the `MiniFASNetV2` model and causing false-positive spoof detections (`real_prob < 0.01`). Refactored `utils/face_utils.py` to mathematically crop the bounding box with a 20% spatial margin before scaling, restoring valid `> 0.60` genuine probabilities for real webcam captures.
- **Account Recovery:** Intervened in the Firestore database to unblock testing accounts that were permanently locked out due to the false-positive AI spoofing triggers.

## Conclusion
The application has successfully evolved into a highly secure, performant, and user-friendly system. 
It features robust defense-in-depth mechanisms (anti-enumeration, CSRF tokens, strict rate limits, and custom error handling). 
Furthermore, the recent architectural shift offloads active geometric liveness tracking (MediaPipe Face Mesh) to the user's browser, enabling zero-latency UI interaction and eliminating Python backend dependency conflicts, while the server retains complete authority over the 128-D cryptographic extraction (dlib), hardware-backed authentication (WebAuthn/Passkeys), and deep-learning anti-spoofing (MiniFASNet).

# ☁️ Face Crypt Cloud

> **نظام مصادقة سحابي متطور يعتمد على القياسات الحيوية للوجه (Biometrics) والتشفير المتقدم، لتقديم بديل آمن وسلس لكلمات المرور التقليدية — بدون كلمة مرور واحدة.**

[![Live Demo](https://img.shields.io/badge/🌐_Live_Demo-Cloud_Run-4285F4.svg)](https://face-crypt-cloud-184918603595.us-central1.run.app/)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.x-green.svg)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/tests-18%20passing-brightgreen.svg)]()
[![Firebase](https://img.shields.io/badge/Firebase-Firestore%20%7C%20Storage-orange.svg)](https://firebase.google.com/)
[![Academic](https://img.shields.io/badge/University_of_Bisha-Cybersecurity-1a4659.svg)]()

**🔗 جرّب النظام مباشرة:** [face-crypt-cloud-184918603595.us-central1.run.app](https://face-crypt-cloud-184918603595.us-central1.run.app/)

---

## 📖 عن المشروع

**Face Crypt Cloud** مشروع تخرج هندسي يهدف إلى القضاء على الثغرات الأمنية المرتبطة بكلمات المرور التقليدية (التصيّد الاحتيالي، هجمات القوة الغاشمة، وإعادة استخدام الكلمات السرية بين المواقع).

يعمل النظام عبر التقاط صورة حية للمستخدم عبر الكاميرا، واستخراج المعالم الحيوية للوجه (Face Encodings) بدقة، ثم **تشفير هذه المعالم** قبل تخزينها في السحابة (Google Firebase). عند تسجيل الدخول، تتم المطابقة برمجيًا في ذاكرة الخادم المؤقتة فقط — بدون أي كلمة مرور، وبدون حفظ صور الوجه نفسها، فقط تمثيلها الرقمي المشفّر.

---

## ✨ الميزات الرئيسية

* **🔐 مصادقة حيوية بدون كلمات مرور:** دخول آمن وسريع بمجرد التعرف على ملامح الوجه، باستخدام `dlib`/`face_recognition`.
* **🕵️ فحص حيوية أساسي (Liveness Detection):** ميزة اختيارية (`FACECRYPT_ENABLE_LIVENESS_CHECK`) تكشف الصور المطبوعة الثابتة عبر قياس وضوح الصورة، وتتحقق من حركة طبيعية بين إطارين عند تفعيل التحدي التفاعلي.
* **🛡️ تشفير البيانات الحيوية:** لا تُحفظ ملامح الوجه كنص واضح أبدًا — تُشفَّر بخوارزمية `Fernet` (AES-128 + HMAC-SHA256) قبل التخزين.
* **🚦 حماية من التخمين والحظر الجماعي:**
  * حظر مؤقت آلي (5 دقائق) بعد 3 محاولات فاشلة، وحظر دائم يتطلب تدخلًا إداريًا بعد 5 محاولات — **لكل مستخدم على حدة**، وليس حظرًا جماعيًا يطال كل الحسابات من محاولة واحدة.
  * حد معدّل صريح على بوابة تسجيل الدخول (10 طلبات/دقيقة، 30 طلبات/ساعة لكل IP) عبر `Flask-Limiter`.
  * رسائل خطأ موحدة (Generic Responses) تمنع مهاجمًا من استنتاج وجود الحساب أو حالته.
* **🔒 تحصين إضافي:** مقارنة كلمات المرور ورموز CSRF بوقت ثابت (`hmac.compare_digest`)، جلسات أدمن محمية بـ CSRF، وقواعد Firestore تمنع أي وصول مباشر من العميل (كل الوصول عبر Admin SDK بالخادم فقط).
* **🎨 واجهة مستخدم حديثة:** تصميم "Dark Glassmorphism" مخصص بالكامل، متجاوب عبر كل أحجام الشاشات، ويحترم `prefers-reduced-motion` لذوي الحساسية للحركة.
* **📊 لوحة تحكم إدارية:** إدارة المستخدمين، إحصائيات لحظية (عبر Firestore Aggregation Queries، لا تحميل كامل للسجلات)، وسجلات تدقيق مُقسّمة على صفحات (Pagination).
* **📝 سجلات تدقيق شاملة:** توثيق كل عملية (نجاح/فشل/حظر) مع الوقت ومعرف المستخدم وعنوان IP.

---

## 🛠️ التقنيات المستخدمة

| الفئة | التقنيات |
|---|---|
| **الخلفية (Backend)** | Python 3.10+, Flask 3.1, Waitress (WSGI للإنتاج) |
| **الذكاء الاصطناعي ومعالجة الصور** | `face_recognition`, `dlib`, `opencv-python-headless`, `Pillow`, `NumPy` |
| **قاعدة البيانات والسحابة** | Google Firebase (Cloud Firestore & Cloud Storage) |
| **الأمان** | `cryptography` (Fernet), `Flask-Limiter`, HMAC (مقارنة بوقت ثابت) |
| **الحاويات والنشر** | Docker, Docker Compose, Google Cloud Run |
| **الواجهة الأمامية** | HTML5, Vanilla CSS3 (نظام تصميم مخصص), Vanilla JS, SweetAlert2 |
| **الاختبارات** | pytest (18 اختبار: مصادقة، صلاحيات، منع تعداد الحسابات، حماية XSS) |

---

## 🚀 البدء والتشغيل

### الطريقة الموصى بها: Docker (الأسرع والأضمن)

لا حاجة لتثبيت `cmake` أو أي أدوات بناء يدويًا — كل شيء داخل الحاوية.

```bash
git clone https://github.com/Ammar-1993/Face-Crypt-Cloud-Arabic.git
cd Face-Crypt-Cloud-Arabic

cp .env.example .env
# عدّل .env بقيمك الفعلية (راجع قسم المتغيرات البيئية أدناه)
# ضع ملف اعتماد Firebase بالمسار: firebase/serviceAccountKey.json

docker compose build
docker compose up -d
docker compose exec app pytest -v   # تأكيد: 18 passed
```
افتح `http://localhost:8080`. لدليل تفصيلي عن الإعداد على WSL2 تحديدًا (بما فيه إعداد HTTPS محلي لاختبار لوحة الأدمن)، راجع [`WSL2_DOCKER_SETUP.md`](./WSL2_DOCKER_SETUP.md).

### الطريقة التقليدية: بيئة افتراضية محلية

يتطلب تثبيت `cmake` ومترجم ++C على جهازك مسبقًا (لازمة لتجميع `dlib`).

```bash
git clone https://github.com/Ammar-1993/Face-Crypt-Cloud-Arabic.git
cd Face-Crypt-Cloud-Arabic

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env      # عدّل القيم، وضع serviceAccountKey.json بمساره
```

**تشغيل التطوير** (بإعادة تحميل تلقائي إن فُعّل `FLASK_DEBUG=True`):
```bash
python app.py
```

**تشغيل يحاكي الإنتاج محليًا:**
```bash
waitress-serve --host=0.0.0.0 --port=8080 wsgi:app
```

* بوابة المستخدمين: `http://127.0.0.1:8080/verify`
* بوابة المسؤول: `http://127.0.0.1:8080/admin/`

---

## ⚙️ إعداد المتغيرات البيئية

انسخ `.env.example` إلى `.env` (هذا الملف جاهز بالمستودع وأسماء متغيراته مطابقة تمامًا لما يقرأه الكود):

```env
FACECRYPT_SECRET_KEY=your_generated_fernet_key_here
FACECRYPT_FLASK_SECRET_KEY=your_generated_flask_secret_key_here
FACECRYPT_ADMIN_PASSWORD=YourStrongAdminPassword
FACECRYPT_SERVICE_ACCOUNT_PATH=firebase/serviceAccountKey.json
FACECRYPT_STORAGE_BUCKET=your-firebase-project-id.appspot.com
FACECRYPT_ENABLE_LIVENESS_CHECK=False

FLASK_DEBUG=False
PORT=8080
FACECRYPT_WSGI_THREADS=4
```

لتوليد مفتاح عشوائي قوي لأي من المتغيرين السريين:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

> **النظام مزوّد بآلية Fail-Fast:** لن يبدأ التشغيل إطلاقًا إذا كان أي متغير سري مفقودًا — يطبع رسالة خطأ واضحة تحدد بالضبط أي متغير ناقص، بدل فشل غامض لاحقًا.

---

## 🧪 الاختبارات

```bash
pytest -v          # محليًا (بعد تفعيل البيئة الافتراضية)
docker compose exec app pytest -v   # داخل الحاوية
```
18 اختبارًا تغطي: نجاح/فشل تسجيل الدخول، منع تعداد الحسابات (Anti-Enumeration)، عدم معاقبة كل المستخدمين من محاولة فاشلة واحدة، حماية XSS بلوحة الأدمن، صلاحيات الجلسات، وترقيم صفحات سجلات التدقيق. `pytest.ini` يقيّد التنفيذ على مجلد `tests/` حصرًا.

---

## 🛡️ هندسة الأمان

1. **مكافحة التخمين والتوقيت:** `hmac.compare_digest` لكل مقارنة كلمة مرور/رمز CSRF، واستجابات API موحدة عند فشل تسجيل الدخول بغض النظر عن السبب الفعلي.
2. **الحد من حجم الحمولات:** الصور المرفوعة محدودة بـ 5 ميجابايت (`MAX_CONTENT_LENGTH`) لمنع استنزاف المعالج عبر رفع ملفات ضخمة.
3. **الدفاع متعدد الطبقات:** `firestore.rules` يمنع أي قراءة/كتابة مباشرة من العميل — كل الوصول حصريًا عبر `Firebase Admin SDK` بالخادم. معالجة أخطاء مركزية تمنع تسريب أي تفاصيل داخلية (Traceback) للمستخدم النهائي.
4. **تدقيق آلي للاعتماديات:** GitHub Actions يشغّل `pip-audit` أسبوعيًا لاكتشاف ثغرات (CVEs) بمكتبات الطرف الثالث.

---

## 🌍 النشر في الإنتاج

النسخة الحية من هذا المشروع تعمل فعليًا على **Google Cloud Run** (رابط أعلى الصفحة)، مبنية مباشرة من `Dockerfile` الموجود بالمستودع عبر:
```bash
gcloud run deploy face-crypt-cloud --source . --region us-central1 --allow-unauthenticated \
  --memory 1Gi --cpu 2 --min-instances 0 \
  --set-secrets FACECRYPT_ADMIN_PASSWORD=...,FACECRYPT_SECRET_KEY=...,FACECRYPT_FLASK_SECRET_KEY=...,/secrets/serviceAccountKey.json=...
```
Cloud Run يوفّر HTTPS تلقائيًا بشهادة مُدارة، وهذا شرط ضروري لعمل التطبيق: `SESSION_COOKIE_SECURE=True` بالكود يعني جلسة تسجيل دخول الأدمن **لن تُحفظ** على اتصال HTTP غير مشفّر.

### بديل: خادم ذاتي خلف Nginx

لو تفضّل استضافة ذاتية (VPS) بدل منصة PaaS، شغّل `waitress` مقيّدًا بـ `127.0.0.1` خلف وكيل عكسي يتولى التشفير:

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 5M;
    }
}
```

---

*© 2024–2026 Face-Crypt-Cloud — جميع الحقوق محفوظة.*
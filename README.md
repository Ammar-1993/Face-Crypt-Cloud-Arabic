# ☁️ Face Crypt Cloud (سحابة الملامح المشفرة)

> **نظام مصادقة ذكي لتأمين المنصات الإلكترونية باستخدام تقنية التعرف على الوجوه والتشفير السحابي كبديل آمن لكلمات المرور التقليدية والمعتاد عليها.**

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.1-green.svg)](https://flask.palletsprojects.com/)
[![Firebase](https://img.shields.io/badge/Firebase-Firestore%20%7C%20Storage-orange.svg)](https://firebase.google.com/)
[![Security](https://img.shields.io/badge/Security-Zero--Knowledge%20Proof-red.svg)]()
[![Academic](https://img.shields.io/badge/University_of_Bisha-Cybersecurity-1a4659.svg)]()

## 📖 عن المشروع (About The Project)
**Face Crypt Cloud** هو مشروع تخرج هندسي يهدف إلى معالجة ثغرات المصادقة التقليدية (مثل التصيد الاحتيالي وهجمات القوة الغاشمة). يقوم النظام بالتقاط صورة وجه المستخدم حياً، واستخراج المعالم الحيوية (Face Encodings)، ثم **تشفيرها** قبل تخزينها في السحابة (Google Firebase). عند محاولة تسجيل الدخول، يتم التحقق من الوجه ومطابقته برمجياً في الذاكرة المؤقتة دون الحاجة لكتابة أي كلمة مرور، مما يوفر بيئة وصول آمنة، موثوقة، وسهلة الاستخدام.

## ✨ الميزات الرئيسية (Key Features)
* **🔐 مصادقة حيوية بدون كلمات مرور (Passwordless Auth):** الدخول للنظام بمجرد التحقق الآمن والسريع من ملامح الوجه باستخدام الذكاء الاصطناعي.
* **🛡️ تشفير البيانات الحيوية (Biometric Encryption):** لا يتم حفظ بصمات الوجوه كنصوص واضحة في قاعدة البيانات، بل يتم تشفيرها بخوارزمية `Fernet` لضمان الخصوصية القصوى.
* **🚦 نظام حظر ذكي (Smart Rate Limiting):** حظر مؤقت آلي للمستخدم بعد 3 محاولات فاشلة، وحظر دائم بعد 5 محاولات لمنع هجمات التخمين والاختراق.
* **📊 لوحة تحكم مركزية (Admin Dashboard):** واجهة مخصصة للإدارة لإضافة/حذف المستخدمين، فك الحظر، ومراقبة إحصائيات النظام في الوقت الفعلي.
* **📝 سجلات تدقيق دقيقة (Audit Logs):** توثيق شامل لكل عملية دخول (ناجحة/فاشلة/حظر) مع تسجيل الوقت ومعرف المستخدم، مما يضمن الشفافية والمساءلة الإدارية.

## 🛠️ التقنيات المستخدمة (Tech Stack)
* **الواجهة الخلفية (Backend):** Python, Flask Framework.
* **الذكاء الاصطناعي ومعالجة الصور:** `face_recognition`, `dlib`, `OpenCV`, `Pillow`, `NumPy`.
* **قاعدة البيانات والسحابة:** Google Firebase (Cloud Firestore for NoSQL Data, Cloud Storage for Images).
* **الواجهة الأمامية (Frontend):** HTML5, CSS3, Vanilla JavaScript, Bootstrap, SweetAlert2.
* **الأمان والتشفير:** `cryptography` (Fernet Symmetric Encryption).

## 📂 هيكل المشروع المعماري (Project Structure)
```text
Face-Crypt-Cloud/
│
├── app/                    # مجلد التطبيق الرئيسي (App Factory Pattern)
│   ├── admin/              # مسارات وخدمات لوحة تحكم الإدارة
│   ├── users/              # مسارات وخدمات المستخدم العادي
│   ├── services/           # دوال الاتصال بقواعد البيانات السحابية
│   └── config.py           # إعدادات النظام وربط المتغيرات البيئية
│
├── utils/                  # الأدوات البرمجية المساعدة (Utilities)
│   ├── face_utils.py       # دوال معالجة، تشفير، ومقارنة الوجوه
│   └── firebase_utils.py   # دوال الاتصال المباشر مع Firestore و Storage
│
├── static/                 # الملفات الثابتة (CSS, JavaScript, Images)
├── templates/              # قوالب واجهات المستخدم ولوحة التحكم (HTML)
├── firebase/               # مجلد الاعتمادات السحابية (serviceAccountKey.json)
├── test_images/            # صور تجريبية لعمليات الفحص والاختبار
├── .env                    # المتغيرات البيئية السرية (يجب عدم رفعه للعامة)
├── app.py                  # نقطة انطلاق تشغيل الخادم (للتطوير)
├── wsgi.py                 # نقطة انطلاق تشغيل الخادم (للإنتاج)
└── requirements.txt        # الاعتمادات ومكتبات بايثون المطلوبة

```

## 🚀 البدء والتشغيل (Getting Started)

### 1. المتطلبات الأساسية (Prerequisites)

* تثبيت `Python 3.10`
* إنشاء مشروع على منصة **Google Firebase** وتفعيل خدمتي (Firestore Database) و (Storage).
* تنزيل مفتاح الخدمة `serviceAccountKey.json` من إعدادات Firebase ووضعه داخل مجلد `firebase/`.

### 2. التثبيت (Installation)

1. قم باستنساخ المستودع:
```bash
git clone [https://github.com/YourUsername/Face-Crypt-Cloud.git](https://github.com/YourUsername/Face-Crypt-Cloud.git)
cd Face-Crypt-Cloud

```

2. إنشاء بيئة افتراضية وتفعيلها:
```bash
python -m venv venv
source venv/bin/activate  # في الويندوز: venv\Scripts\activate
```

### 3. تثبيت الاعتمادات وفحص الأمان (Install & Audit Dependencies)

```bash
pip install -r requirements.txt
```

**فحص الأمان المستمر (Security Auditing):**
يُنصح بشدة بإجراء فحص دوري لاعتمادات بايثون للتأكد من خلوها من الثغرات الأمنية المكتشفة حديثاً (CVEs).
```bash
pip install pip-audit
pip-audit -r requirements.txt
```
*(اقتراح للإطلاق في الإنتاج: إضافة سير عمل GitHub Actions لتشغيل `pip-audit` تلقائياً مع كل عملية Push).*

### 4. إعداد المتغيرات البيئية (Environment Setup)

قم بإنشاء ملف باسم `.env` في المسار الرئيسي للمشروع، وأضف بداخله القيم السرية التالية (تأكد من مطابقة أسماء المتغيرات تماماً):

```env
# مفتاح تشفير البيانات الحيوية (يتم توليده عبر مكتبة cryptography - Fernet)
FACECRYPT_SECRET_KEY=your_generated_fernet_key_here

# مفتاح تشفير الجلسات وحماية CSRF (يجب أن يكون قيمة عشوائية طويلة، ومختلفاً عن مفتاح Fernet)
# يمكنك توليده عبر الأمر: python -c "import secrets; print(secrets.token_hex(32))"
FACECRYPT_FLASK_SECRET_KEY=your_generated_flask_secret_key_here

# كلمة مرور الدخول للوحة تحكم المسؤول (يتم التحقق منها من الذاكرة مباشرة)
FACECRYPT_ADMIN_PASSWORD=YourStrongAdminPassword

# مسار مفتاح فايربيس ورابط التخزين الخاص بمشروعك السحابي
FACECRYPT_SERVICE_ACCOUNT_PATH=firebase/serviceAccountKey.json
FACECRYPT_STORAGE_BUCKET=your-firebase-project-id.appspot.com

# إعدادات التشغيل (اختياري)
FLASK_DEBUG=False
PORT=8080

```

### 4. تشغيل النظام (Run the Application)

**لبيئة التطوير (Development):**
```bash
python app.py
```

**لبيئة الإنتاج (Production):**
نوصي بشدة بتشغيل النظام باستخدام خادم `Waitress` WSGI المتوفر ضمن المشروع بدلاً من خادم Flask المدمج.
```bash
python wsgi.py
```
أو عبر الأمر:
```bash
waitress-serve --port=8080 wsgi:app
```

* **بوابة وصول المستخدمين:** `http://127.0.0.1:8080/`
* **بوابة وصول الإدارة (لوحة التحكم):** `http://127.0.0.1:8080/admin/`

## 🛡️ ملاحظات أمنية (Security Notes)

* **فحص الحيوية الأساسي (Liveness Detection):** تم تنفيذ فحص أساسي لمكافحة الانتحال (Anti-spoofing) لردع محاولات استخدام صور مطبوعة أو شاشات ثابتة. يستخدم الفحص تحليل تباين الصور (Laplacian Variance) بالإضافة إلى اكتشاف الحركة الدقيقة بين إطارين (Micro-movement باستخدام Facial Landmarks). **ملاحظة:** هذا الفحص مصمم لأغراض مشروع التخرج كطبقة أمان إضافية، ولكنه ليس بديلاً معتمداً تجارياً لتقنيات Liveness 3D المتقدمة. يمكن تفعيله عبر المتغير `FACECRYPT_ENABLE_LIVENESS_CHECK=True`.
* **⚠️ خطر وضع التطوير (FLASK_DEBUG):** يجب **ألا تقوم أبداً** بتعيين المتغير البيئي `FLASK_DEBUG=True` في أي بيئة إنتاج أو على خادم متصل بالإنترنت. تشغيل Flask في وضع التطوير يكشف واجهة مصحح الأخطاء (Werkzeug Debugger)، مما يعرض النظام لخطر تسريب البيانات الحساسة أو حتى تنفيذ الأوامر البرمجية عن بُعد (Remote Code Execution).
* **حماية مفاتيح التشفير:** ملف `.env` يحتوي على مفتاح `Fernet` الذي يشفر بصمات الوجوه. إذا ضاع هذا المفتاح، فلن تتمكن من فك تشفير البيانات الموجودة في Firestore أبداً. تأكد من عدم رفع هذا الملف للعامة (تم إدراجه في `.gitignore`).
* **حدود حجم الملفات (Upload Limits):** لتقليل هجمات حرمان الخدمة (DoS) الناتجة عن الإرهاق الحسابي لمعالجة الصور، تم تقييد حجم الطلبات المرفوعة إلى 5 ميغابايت كحد أقصى.
* **استرداد حساب الإدارة (Recovery):** وصول المسؤول (Admin) معزول تماماً عن قاعدة البيانات. في حال نسيان كلمة المرور الإدارية، يمكن لمهندس النظام استعادتها فوراً بتحديث المتغير `FACECRYPT_ADMIN_PASSWORD` في بيئة الخادم.
* **قواعد أمان قاعدة البيانات (Firestore Security Rules):** تم إضافة ملف `firestore.rules` لرفض كافة اتصالات العميل المباشرة (Client-Side). النظام يعتمد كلياً على بيئة (Admin SDK) داخل الواجهة الخلفية (Flask)، مما يضمن عدم إمكانية الوصول إلى البيانات الحيوية من المتصفح مباشرة كطبقة حماية إضافية (Defense-in-Depth).

## 🌍 النشر في بيئة الإنتاج (Production Deployment)

لضمان أمان البيانات الحيوية (مثل صور الوجوه وكلمات المرور) عند النشر على خوادم حقيقية، يجب **تأمين الاتصال باستخدام HTTPS/TLS**. إرسال البيانات الحساسة عبر HTTP غير المشفر يعرضها لخطر الاعتراض (Man-in-the-Middle Attacks).

**ملاحظة هامة جداً:** التطبيق مهيأ لإنشاء ملفات تعريف ارتباط (Cookies) آمنة فقط (`SESSION_COOKIE_SECURE = True`). إذا قمت بتشغيل التطبيق عبر اتصال `HTTP` غير مشفر في بيئة الإنتاج، فلن يقوم المتصفح بحفظ جلسة الإدارة، مما سيؤدي إلى فشل تسجيل الدخول بصمت (لن تتمكن من الدخول للوحة التحكم إطلاقاً). لذلك فإن HTTPS هو **متطلب تشغيلي إلزامي** وليس مجرد توصية.

### 1. الخادم الوكيل العكسي وتشفير الاتصال (Reverse Proxy & TLS)
يجب وضع التطبيق خلف خادم وكيل عكسي (Reverse Proxy) مثل Nginx أو Caddy ليتولى مهمة تشفير الاتصال (TLS Termination).

**مثال لإعداد Nginx (Nginx Configuration Example):**
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8080; # توجيه الطلبات إلى خادم Waitress
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. تشغيل التطبيق (Application Server)
* ⚠️ **تحذير:** لا تستخدم خادم Flask المدمج (`python app.py`) في بيئة الإنتاج.
* استخدم دائماً خادم إنتاج مخصص مثل `Waitress` (المتضمن بالفعل في الاعتمادات).
* تأكد من أن التطبيق يعمل ومقيد بالشبكة المحلية (`localhost` أو `127.0.0.1`) وأنه غير متاح للوصول الخارجي المباشر، بل فقط من خلال الخادم الوكيل (Reverse Proxy).

```bash
# التشغيل الصحيح في الإنتاج
waitress-serve --listen=127.0.0.1:8080 wsgi:app
```

### 3. قائمة التحقق قبل النشر (Pre-Deployment Checklist)
قبل إطلاق النظام، تأكد من الآتي:
- [ ] **تعطيل وضع التطوير:** التأكد تماماً من تعيين `FLASK_DEBUG=False`.
- [ ] **إدارة الأسرار السرية:** عدم رفع ملف `.env` لمستودعات الكود. يجب إعداد جميع المتغيرات السرية (مثل `FACECRYPT_SECRET_KEY`, `FACECRYPT_FLASK_SECRET_KEY`, `FACECRYPT_ADMIN_PASSWORD`) عبر "مدير الأسرار" الخاص بمنصة الاستضافة (Secret Manager) أو كمتغيرات بيئية على الخادم بشكل آمن، مع التأكد من تعيين قيمة فريدة وقوية لـ `FACECRYPT_FLASK_SECRET_KEY`.
- [ ] **شهادات SSL/TLS صالحة ومفعلة:** لضمان تشفير البيانات المرسلة بين المستخدم والخادم.
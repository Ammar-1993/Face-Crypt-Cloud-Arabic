# ☁️ Face Crypt Cloud (سحابة الملامح المشفرة)

> **نظام مصادقة سحابي متطور يعتمد على القياسات الحيوية للوجه (Biometrics) والتشفير المتقدم (Zero-Knowledge Architecture)، لتقديم بديل آمن وسلس لكلمات المرور التقليدية.**

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.x-green.svg)](https://flask.palletsprojects.com/)
[![Firebase](https://img.shields.io/badge/Firebase-Firestore%20%7C%20Storage-orange.svg)](https://firebase.google.com/)
[![Security](https://img.shields.io/badge/Security-Advanced-red.svg)]()
[![Design](https://img.shields.io/badge/UI%2FUX-Glassmorphism-00D4FF.svg)]()
[![Academic](https://img.shields.io/badge/University_of_Bisha-Cybersecurity-1a4659.svg)]()

---

## 📖 عن المشروع (About The Project)
**Face Crypt Cloud** هو مشروع تخرج هندسي متقدم يهدف إلى القضاء على الث الثغرات الأمنية المرتبطة بكلمات المرور (مثل التصيد الاحتيالي، هجمات القوة الغاشمة، وإعادة استخدام الكلمات السريّة). 

يعمل النظام عبر التقاط صورة حية للمستخدم، واستخراج المعالم الحيوية للوجه (Face Encodings) بدقة، ثم **تشفير هذه المعالم** قبل إرسالها وتخزينها في السحابة (Google Firebase). عند محاولة تسجيل الدخول، يتم فك التشفير والمطابقة برمجياً في الذاكرة المؤقتة للخادم فقط، مما يضمن بيئة وصول سلسة (Passwordless) ومحصنة بالكامل.

---

## ✨ الميزات الرئيسية (Key Features)

* **🔐 مصادقة حيوية بدون كلمات مرور (Passwordless Auth):** دخول آمن وسريع بمجرد التعرف على ملامح الوجه باستخدام خوارزميات الذكاء الاصطناعي.
* **🛡️ تشفير البيانات الحيوية (Biometric Encryption):** لا يتم حفظ بصمات الوجوه كنصوص واضحة أبداً. يتم تشفيرها بخوارزمية التشفير المتماثل `Fernet` (AES-128) لضمان الخصوصية التامة.
* **🚦 نظام حماية ومكافحة التخمين (Anti-Enumeration & Rate Limiting):**
  * حظر مؤقت آلي (5 دقائق) بعد 3 محاولات فاشلة.
  * حظر دائم يتطلب تدخلاً إدارياً بعد 5 محاولات.
  * رسائل خطأ موحدة (Generic Responses) لمنع المهاجمين من استنتاج حالة الحساب.
* **🛡️ حماية متقدمة ضد الهجمات (Advanced Hardening):** 
  * مقارنة كلمات المرور بوقت ثابت (Constant-Time Comparison) لمنع هجمات التوقيت.
  * حماية مدمجة ضد هجمات تزوير الطلبات عبر المواقع (CSRF) للوحة الإدارة.
  * منع الوصول المباشر لقاعدة البيانات عبر قواعد Firestore الصارمة (Defense-in-Depth).
* **🎨 واجهة مستخدم حديثة (Modern UI/UX):** تصميم مبتكر يعتمد على "Glassmorphism" والألوان الداكنة (Dark Cyberpunk Theme) مع تجربة مستخدم سلسة ومتجاوبة عبر جميع الأجهزة.
* **📊 لوحة تحكم مركزية (Admin Dashboard):** واجهة مخصصة وآمنة لإدارة المستخدمين، ومراقبة إحصائيات النظام في الوقت الفعلي.
* **📝 سجلات تدقيق غير قابلة للتلاعب (Audit Logs):** توثيق شامل لكل العمليات (ناجحة/فاشلة/حظر) مع تسجيل دقيق للوقت ومعرف المستخدم لضمان المساءلة.

---

## 🛠️ التقنيات المستخدمة (Tech Stack)

* **الواجهة الخلفية (Backend):** Python 3.10+, Flask Framework.
* **الذكاء الاصطناعي ومعالجة الصور:** `face_recognition`, `dlib`, `OpenCV`, `Pillow`, `NumPy`.
* **قاعدة البيانات والسحابة:** Google Firebase (Cloud Firestore & Cloud Storage).
* **الواجهة الأمامية (Frontend):** HTML5, Vanilla CSS3 (Custom Design System), Vanilla JS, Bootstrap Grid, SweetAlert2.
* **الأمان والتشفير:** `cryptography` (Fernet), HMAC (Constant-time comparison).

---

## 🚀 البدء والتشغيل (Getting Started)

### 1. المتطلبات الأساسية (Prerequisites)
* تثبيت `Python 3.10` أو أحدث.
* إنشاء مشروع على منصة **Google Firebase** وتفعيل خدمتي (Firestore Database) و (Storage).
* تنزيل مفتاح الخدمة `serviceAccountKey.json` من إعدادات Firebase ووضعه داخل مجلد `firebase/`.

### 2. التثبيت (Installation)
```bash
# 1. استنساخ المستودع
git clone https://github.com/YourUsername/Face-Crypt-Cloud.git
cd Face-Crypt-Cloud

# 2. إنشاء بيئة افتراضية وتفعيلها
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. تثبيت الاعتمادات
pip install -r requirements.txt
```

### 3. إعداد المتغيرات البيئية (Environment Setup)
قم بإنشاء ملف باسم `.env` في المسار الرئيسي للمشروع. **يجب ألا يتم رفع هذا الملف إطلاقاً لأي مستودع عام**.

```env
# مفتاح تشفير البيانات الحيوية (مطلوب - يولد عبر مكتبة cryptography - Fernet)
FACECRYPT_SECRET_KEY=your_generated_fernet_key_here

# مفتاح تشفير جلسات Flask (مطلوب - استخدم قيمة عشوائية طويلة مثل 32-byte hex)
FACECRYPT_FLASK_SECRET_KEY=your_generated_flask_secret_key_here

# كلمة مرور الدخول للوحة تحكم المسؤول (مطلوب)
FACECRYPT_ADMIN_PASSWORD=YourStrongAdminPassword

# مسار مفتاح فايربيس (مطلوب)
FACECRYPT_SERVICE_ACCOUNT_PATH=firebase/serviceAccountKey.json

# رابط التخزين الخاص بمشروعك السحابي (مطلوب)
FACECRYPT_STORAGE_BUCKET=your-firebase-project-id.appspot.com

# إعدادات التشغيل (اختياري)
FLASK_DEBUG=False
PORT=8080
FACECRYPT_WSGI_THREADS=4
```
*(ملاحظة: النظام مزود بآلية "Fail-Fast"، ولن يعمل إذا كانت أي من المتغيرات السرية مفقودة).*

### 4. التشغيل (Run the Application)

**لبيئة التطوير (Development):**
```bash
python app.py
```

**لبيئة الإنتاج (Production):**
يُمنع استخدام خادم التطوير. استخدم `Waitress`:
```bash
waitress-serve --port=8080 wsgi:app
```
* بوابة المستخدمين: `http://127.0.0.1:8080/`
* بوابة المسؤول: `http://127.0.0.1:8080/admin/`

---

## 🛡️ هندسة الأمان والملاحظات (Security Architecture)

تم بناء **Face Crypt Cloud** مع مراعاة أعلى معايير الأمان:

1. **مكافحة الهجمات الجانبية والتخمين:** 
   * يتم استخدام `hmac.compare_digest` لمقارنة كلمات المرور ورموز CSRF لمنع استنتاج البيانات عبر هجمات التوقيت (Timing Attacks).
   * استجابات الواجهة البرمجية API موحدة تماماً عند فشل تسجيل الدخول، مما يمنع المهاجم من معرفة ما إذا كان الحساب غير موجود، أو محظوراً، أو غير مطابق (User Enumeration Prevention).
2. **الحد من حجم الحمولات (DoS Prevention):** تم تقييد حجم الصور المرفوعة بـ 5 ميجابايت (`MAX_CONTENT_LENGTH`) لمنع هجمات حرمان الخدمة (DoS) التي تستهدف إرهاق المعالج أثناء استخراج ملامح الوجه.
3. **الدفاع المتعدد الطبقات (Defense in Depth):** 
   * ملف `firestore.rules` يغلق تماماً إمكانية القراءة/الكتابة من جانب العميل. التطبيق يتواصل حصرياً وموثوقاً عبر `Firebase Admin SDK` في الواجهة الخلفية.
   * إدارة أخطاء شاملة تمنع تسريب تفاصيل الأكواد أو البنية التحتية (Traceback Leaks) للمستخدم النهائي، مع الاكتفاء بتسجيلها في النظام.
4. **تدقيق الاعتمادات (CI/CD Auditing):** المشروع مزود بمسار عمل GitHub Actions لتشغيل `pip-audit` آلياً لاكتشاف أي ثغرات (CVEs) في مكتبات الطرف الثالث.

---

## 🌍 النشر في الإنتاج (Production Deployment)

لضمان أمان البيانات والجلسات، **يُعتبر استخدام بروتوكول HTTPS شرطاً إلزامياً** في الإنتاج. 

التطبيق مُعد لإنشاء جلسات مؤمنة (`SESSION_COOKIE_SECURE = True`). عبر اتصال HTTP غير مشفر، لن تحتفظ المتصفحات بجلسة المشرف، وسيفشل تسجيل الدخول.

### إعداد الخادم الوكيل العكسي (Nginx Reverse Proxy)

يجب وضع خادم `Waitress` خلف خادم وكيل يعالج التشفير (TLS Termination). مثال التكوين:

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
        
        # السماح برفع صور تصل إلى 5MB (مطابق لإعدادات التطبيق)
        client_max_body_size 5M;
    }
}
```

---
*© 2024–2026 Face-Crypt-Cloud — جميع الحقوق محفوظة.*
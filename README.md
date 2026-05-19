# ☁️ Face Crypt Cloud (سحابة الملامح المشفرة)

> **نظام مصادقة ذكي لتأمين المنصات الإلكترونية باستخدام تقنية التعرف على الوجوه والتشفير السحابي كبديل آمن لكلمات المرور التقليدية.**

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
├── app.py                  # نقطة انطلاق تشغيل الخادم
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
# لنظام الويندوز:
venv\Scripts\activate
# لنظام ماك/لينكس:
source venv/bin/activate

```


3. تثبيت المكتبات المطلوبة:
*(ملاحظة: لتثبيت مكتبة `dlib` على بيئة ويندوز بسهولة، يمكنك استخدام ملف `.whl` المرفق في المجلد المحلى)*
```bash
pip install -r requirements.txt

```



### 3. إعداد المتغيرات البيئية (Environment Setup)

قم بإنشاء ملف باسم `.env` في المسار الرئيسي للمشروع، وأضف بداخله القيم السرية التالية:

```env
# مفتاح تشفير الجلسات والبيانات الحيوية (يتم توليده عبر مكتبة cryptography)
SECRET_KEY=your_generated_fernet_key_here

# كلمة مرور الدخول للوحة تحكم المسؤول (يتم التحقق منها من الذاكرة مباشرة)
FACECRYPT_ADMIN_PASSWORD=YourStrongAdminPassword

# مسار مفتاح فايربيس ورابط التخزين الخاص بمشروعك السحابي
SERVICE_ACCOUNT_PATH=firebase/serviceAccountKey.json
STORAGE_BUCKET=your-firebase-project-id.appspot.com

```

### 4. تشغيل النظام (Run the Application)

لتشغيل خادم التطوير محلياً:

```bash
python app.py

```

* **بوابة وصول المستخدمين:** `http://127.0.0.1:8080/`
* **بوابة وصول الإدارة (لوحة التحكم):** `http://127.0.0.1:8080/admin/`

## 🛡️ ملاحظات أمنية (Security Notes)

* **حماية مفاتيح التشفير:** ملف `.env` يحتوي على مفتاح `Fernet` الذي يشفر بصمات الوجوه. إذا ضاع هذا المفتاح، فلن تتمكن من فك تشفير البيانات الموجودة في Firestore أبداً. تأكد من عدم رفع هذا الملف للعامة (تم إدراجه في `.gitignore`).
* **استرداد حساب الإدارة (Recovery):** وصول المسؤول (Admin) معزول تماماً عن قاعدة البيانات. في حال نسيان كلمة المرور الإدارية، يمكن لمهندس النظام استعادتها فوراً بتحديث المتغير `FACECRYPT_ADMIN_PASSWORD` في بيئة الخادم.


```
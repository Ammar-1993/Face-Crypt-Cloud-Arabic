# ☁️ Face Crypt Cloud (سحابة الملامح المشفرة)

> **نظام مصادقة سحابي ذكي يعتمد على التشفير الحيوي (Biometric Encryption) كبديل آمن لكلمات المرور التقليدية.**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.1-green.svg)](https://flask.palletsprojects.com/)
[![Firebase](https://img.shields.io/badge/Firebase-Firestore%20%7C%20Storage-orange.svg)](https://firebase.google.com/)
[![Security](https://img.shields.io/badge/Encryption-Fernet-red.svg)]()

## 📖 عن المشروع (About The Project)
**Face Crypt Cloud** هو مشروع تخرج يهدف إلى معالجة ثغرات المصادقة التقليدية (مثل التصيد الاحتيالي وهجمات القوة الغاشمة). يقوم النظام بالتقاط صورة وجه المستخدم حياً، واستخراج المعالم الحيوية (Face Encodings)، ثم **تشفيرها** قبل تخزينها في السحابة (Firebase). عند تسجيل الدخول، يتم التحقق من الوجه ومطابقته برمجياً دون الحاجة لكتابة أي كلمة مرور.

## ✨ الميزات الرئيسية (Key Features)
* **🔐 مصادقة حيوية بدون كلمات مرور (Passwordless Auth):** الدخول للنظام بمجرد النظر للكاميرا.
* **🛡️ تشفير البيانات الحيوية (Zero-Knowledge Proof):** لا يتم حفظ بصمات الوجوه كنصوص واضحة في قاعدة البيانات، بل يتم تشفيرها بخوارزمية `Fernet` لضمان الخصوصية.
* **🚦 نظام حظر ذكي (Smart Rate Limiting):** حظر مؤقت للمستخدم بعد 3 محاولات فاشلة، وحظر دائم بعد 5 محاولات لمنع هجمات التخمين.
* **📊 لوحة تحكم مركزية (Admin Dashboard):** واجهة مخصصة للإدارة لإضافة/حذف المستخدمين، فك الحظر، وعرض إحصائيات النظام.
* **📝 سجلات تدقيق دقيقة (Audit Logs):** توثيق شامل لكل عملية دخول (ناجحة/فاشلة/حظر) مع تسجيل الوقت ومعرف المستخدم لضمان المساءلة.

## 🛠️ التقنيات المستخدمة (Tech Stack)
* **الواجهة الخلفية (Backend):** Python, Flask Framework.
* **الذكاء الاصطناعي ومعالجة الصور:** `face_recognition`, `dlib`, `OpenCV`, `Pillow`, `NumPy`.
* **قاعدة البيانات والسحابة:** Google Firebase (Firestore for Data, Cloud Storage for Images).
* **الواجهة الأمامية (Frontend):** HTML5, CSS3, Vanilla JavaScript, Bootstrap, SweetAlert2.
* **الأمان:** `cryptography` (Fernet).

## 📂 هيكل المشروع (Project Structure)
```text
Face-Crypt-Cloud/
│
├── app/                    # مجلد التطبيق الرئيسي (App Factory)
│   ├── admin/              # مسارات وخدمات لوحة تحكم الإدارة
│   ├── users/              # مسارات وخدمات المستخدم العادي
│   ├── services/           # دوال الاتصال بقواعد البيانات (Firestore/Storage)
│   └── config.py           # إعدادات النظام وربط المتغيرات البيئية
│
├── utils/                  # الأدوات المساعدة
│   ├── face_utils.py       # دوال معالجة، تشفير، ومقارنة الوجوه
│   └── firebase_utils.py   # دوال الاتصال المباشر مع فايربيس
│
├── static/                 # الملفات الثابتة (CSS, JS, Images)
├── templates/              # قوالب واجهات المستخدم (HTML)
├── firebase/               # مجلد يحتوي على مفتاح الوصول الخاص بـ Firebase (JSON)
├── .env                    # المتغيرات البيئية السرية (مستثنى من التتبع)
├── app.py                  # نقطة انطلاق تشغيل الخادم
└── requirements.txt        # مكتبات بايثون المطلوبة
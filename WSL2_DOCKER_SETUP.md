# خطة تهيئة Face-Crypt-Cloud على WSL2 + Docker (نسخة محدّثة)

سحبت نسخة حديثة من المستودع وحلّلتها بعمق قبل كتابة هذي النسخة. الخبر الجيد: أغلب اللي كنت رح أطلبه منك بالنسخة السابقة **صار موجود فعلًا** بالكود الحالي. فيه اكتشاف جديد واحد يستاهل الانتباه قبل ما تدخل Docker. وضّحت أدناه شنو تغيّر بالضبط.

---

## ✅ ما تأكدت إنه صار مطبّقًا فعليًا (لا حاجة تعيده)

- **`opencv-python` صارت `opencv-python-headless==5.0.0.93`** بـ `requirements.txt` — بالضبط التعديل اللي كنت سأطلبه. لا تلمسه.
- **ملف `.env.example` موجود الآن بجذر المشروع**، وتحققت إن كل أسماء المتغيرات فيه مطابقة **حرفيًا** لما يقرأه `app/config.py` (بادئة `FACECRYPT_` موحّدة على الكل) — يعني تقدر تعتمد عليه مباشرة بدل نسخ الأسماء يدويًا من README.

---

## ⚠️ اكتشاف جديد: سكربتات تجريبية بجذر المشروع، وواحد منها يلمس Firestore الحقيقي

لاحظت رجوع نمط كنا نظّفناه بجولة سابقة: 11 ملف سكربت تجريبي عاد لجذر المشروع (`check_logs.py`, `generate_favicon.py`, `mock_face_recognition.py`, `test_empty_count.py`, `test_firestore.py`, `test_firestore_insert.py`, `test_get_count.py`, `test_stats.py`, `test_stats_direct.py`, `test_stats_route.py`, `test_stream_count.py`).

فحصت `test_firestore.py` تحديدًا وشغّلته فعليًا: يتصل بـ Firestore **الحقيقي** مباشرة (`credentials.Certificate('firebase/serviceAccountKey.json')`) بلا أي محاكاة (mocking)، وما فيه ولا دالة `def test_...` بالداخل — هو سكربت تشخيصي عادي بس اسمه يبدأ بـ `test_` فيتشابه مع ملفات pytest. تحققت عمليًا: استدعاؤه المباشر (`pytest test_firestore.py` أو تشغيله كـ Python عادي) يحاول الاتصال الفوري بقاعدة بياناتك الحقيقية. **المستودع لا يحتوي حاليًا على `pytest.ini` أو أي إعداد يحدد نطاق البحث عن الاختبارات (`testpaths`)** — وهذا يعني الاعتماد على السلوك الافتراضي لإصدار pytest نفسه لتحديد أي ملفات يتم جمعها، وهذا سلوك قد يختلف بين الإصدارات وما ينبغي الاعتماد عليه ضمنيًا.

**الحل المرفق:** ملف `pytest.ini` جديد يقيّد pytest صراحة على مجلد `tests/` فقط — يزيل الغموض نهائيًا بغض النظر عن إصدار pytest. أضفته كملف خامس بهذي الجولة.

**توصية إضافية (خارج نطاق Docker مباشرة، لكن تستاهل خطوة قبل ما تكمل):** انقل هذي السكربتات لمجلد منفصل زي `scripts/debug/` بدل جذر المشروع، أو احذف اللي ما تحتاجه — نفس النمط اللي عملناه بجولة تنظيف سابقة.

---

## 1. تجهيز بيئة WSL2 (مرة وحدة فقط)

### 1.1 Docker على توزيعتك بالذات
Docker Desktop: Settings → Resources → WSL Integration، فعّل `Ubuntu-22.04` تحديدًا.
بديل بدون Docker Desktop: ثبّت Docker Engine مباشرة داخل WSL2 (تعليمات Docker الرسمية لـ Ubuntu)، وشغّل `sudo service docker start` بكل جلسة (أو فعّل systemd بـ `/etc/wsl.conf`).

### 1.2 موارد كافية لتجميع dlib
```ini
# %UserProfile%\.wslconfig
[wsl2]
memory=8GB
processors=4
swap=4GB
```
بعدها: `wsl --shutdown` من PowerShell، ثم افتح طرفية WSL2 من جديد.

### 1.3 نهايات الأسطر
```bash
git config --global core.autocrlf input
```

**تذكير مهم:** مسارك الحالي (`/home/ammar/code/Face-Crypt-Cloud` من داخل WSL2، مو `/mnt/c/...`) صحيح تمامًا — استمر بالعمل من طرفية WSL2 أو VS Code عبر "Remote - WSL" مؤشرة على نفس المسار، لتفادي بطء بروتوكول 9P بين ويندوز ولينكس.

---

## 2. الملفات الخمسة المرفقة

انسخها لجذر المشروع:
- `Dockerfile` — بناء متعدد المراحل، يجمّع `dlib` بمرحلة منفصلة.
- `docker-compose.yml` — معدّ للتطوير: `volumes: .:/app` لانعكاس تعديلاتك فورًا، ويشغّل `python app.py` (إعادة تحميل تلقائي).
- `.dockerignore` — يستثني `.env` و`firebase/serviceAccountKey.json` و`test_images/` وكل السكربتات التجريبية المذكورة أعلاه.
- `pytest.ini` — **جديد بهذي الجولة** — يقيّد pytest على `tests/` فقط.
- `Caddyfile` (اختياري) — بروكسي HTTPS محلي لاختبار لوحة الأدمن (راجع قسم 4).

---

## 3. التشغيل الفعلي — أمرًا بعد أمر

```bash
# 1) أنشئ .env من القالب الجاهز (بدل نسخ يدوي من README)
cp .env.example .env
nano .env   # عبّي القيم الفعلية: كلمة مرور الأدمن، مسار serviceAccountKey.json...

# 2) تأكد إن ملف اعتماد Firebase موجود فعليًا بالمسار اللي حددته بـ .env
ls -la firebase/serviceAccountKey.json

# 3) ابنِ الصورة (البناء الأول يستغرق وقتًا لتجميع dlib، طبيعي)
docker compose build

# 4) شغّل الحاوية
docker compose up

# 5) بنافذة ثانية: تأكد إن السيرفر يستجيب
curl http://localhost:8081/health

# 6) شغّل مجموعة الاختبارات — الآن pytest.ini يضمن تشغيل tests/ فقط،
#    بلا خطر لمس أي سكربت تجريبي بالجذر
docker compose exec app pytest -v
# المتوقع: 18 passed
```

---

## 4. فخ لوحة الأدمن (HTTPS)

`SESSION_COOKIE_SECURE = True` يعني جلسة تسجيل دخول الأدمن **لن تثبّت** على `http://localhost:8081` العادي. بوابة الوجه العامة تشتغل طبيعي بدون هذا القيد. لاختبار لوحة الأدمن كاملة محليًا: فعّل خدمة `caddy` المعلّقة بـ `docker-compose.yml`، وزُر `https://localhost:8443` بدلًا من المنفذ العادي.

---

## 5. قائمة تحقق نهائية

- [ ] `pytest.ini` منسوخ لجذر المشروع (يمنع أي خطر لمس بيانات حقيقية عبر تشغيل pytest بالخطأ)
- [ ] `docker compose build` نجح
- [ ] `curl http://localhost:8081/health` يرجع 200
- [ ] `docker compose exec app pytest -v` يعطي 18/18 ناجح
- [ ] تسجيل دخول حقيقي بوجه فعلي يشتغل عبر `http://localhost:8081`
- [ ] (لو فعّلت Caddy) تسجيل دخول أدمن كامل يشتغل عبر `https://localhost:8443`
- [ ] تعديل بسيط بأي ملف ينعكس تلقائيًا بالحاوية بدون إعادة بناء
- [ ] نقلت أو حذفت السكربتات التجريبية الـ11 من جذر المشروع (خطوة نظافة، مو حرجة لـ Docker نفسه)

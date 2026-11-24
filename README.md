# سامانه پرسش از اسناد (RAG)

این پروژه یک نمونه‌ی ساده، مرتب و قابل ارائه از «پرسش از اسناد» است. سند را ثبت می‌کنید، برنامه متن آن را به بخش‌های کوچک تبدیل می‌کند، بخش‌های مرتبط را پیدا می‌کند و با کمک مدل زبانی پاسخ می‌دهد.

## نقشه‌ی خیلی ساده‌ی پروژه

```text
DOCX یا متن → استخراج متن → تکه‌بندی → BM25 / LangChain → بخش‌های مرتبط
                                                        ↓
پرسش کاربر → LLM: عبارت‌های هم‌معنا → BM25 → LLM: پاسخ + منابع → تاریخچه
```

**چرا این طراحی؟** برای پروژه‌ی کوچک SQLite و BM25 سریع‌اند. پیش از جست‌وجو، LLM چند عبارت هم‌معنا برای پرسش می‌سازد تا وابستگی BM25 به کلمه‌های دقیق کمتر شود؛ این راهکار بدون دانلود مدل جدید یا افزودن vector database است. در پروژه‌ی بزرگ می‌توان مرحله‌ی بازیابی را با embedding و یک vector database جایگزین کرد، بدون تغییر API یا مدل‌ها.

## قابلیت‌ها

- CRUD کامل سندها از API و Django Admin
- آپلود و استخراج متن پاراگراف‌ها و جدول‌های DOCX
- ذخیره‌ی متن کامل و بخش‌های (chunks) هر سند
- بازیابی BM25 در جریان پردازش `LangChain`، با گسترش ساده‌ی معنایی پرسش توسط LLM
- پاسخ‌دهی از OpenRouter با مدل رایگان، همراه با منابع استفاده‌شده
- حالت بدون API Key: پاسخ مستند از قطعه‌های بازیابی‌شده، مناسب توسعه و تست
- ذخیره‌ی پرسش، پاسخ، منابع و زمان در تاریخچه
- Docker، داده نمونه، تست و مستندات API

## اجرای سریع با Docker

1. فایل `.env.example` را با نام `.env` کپی کنید.
2. برای پاسخ LLM واقعی، `OPENROUTER_API_KEY` را در `.env` وارد کنید. دریافت کلید رایگان: <https://openrouter.ai/keys>.
3. اجرا کنید:

```bash
docker compose up --build
```

4. در یک ترمینال دیگر داده‌ی نمونه و مدیر بسازید:

```bash
docker compose exec web python manage.py seed_demo
docker compose exec web python manage.py createsuperuser
```

پنل مدیریت در <http://localhost:8000/admin/> و API قابل مرور در <http://localhost:8000/api/> است.

### پرسش مستقیم از پنل Admin

پس از ورود به Admin، وارد «تاریخچه پرسش‌ها و پاسخ‌ها» شوید و روی دکمهٔ **«پرسش از اسناد»** بزنید. سؤال، پاسخ، منابع و `expanded_terms` همان‌جا نمایش داده می‌شوند و پاسخ در تاریخچه نیز ذخیره می‌شود؛ بنابراین برای دمو نیازی به Postman نیست.

## اجرای محلی بدون Docker

```bash
python -m venv .venv
.venv\Scripts\activate        # ویندوز PowerShell
pip install -r requirements.txt
Copy-Item .env.example .env     # سپس در صورت نیاز کلید را وارد کنید
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver
```

## استفاده از API

مستندات کامل در [API.md](API.md) است. سه endpoint اصلی:

| کار | آدرس |
| --- | --- |
| لیست، ایجاد، ویرایش و حذف سند | `/api/documents/` |
| پرسش تازه | `POST /api/history/ask/` |
| تاریخچه پاسخ‌ها | `/api/history/` |

نمونه پرسش:

```bash
curl -X POST http://localhost:8000/api/history/ask/ -H "Content-Type: application/json" -d "{\"question\": \"RAG چیست؟\"}"
```

در پاسخ، فیلد `expanded_terms` را هم می‌بینید؛ عبارت‌های هم‌معنایی برای بهتر شدن BM25 هستند. `expansion_method` نیز روشن می‌کند عبارت‌ها با LLM ساخته شده‌اند، از fallback محلی آمده‌اند، یا وجود ندارند.

## بارگذاری DOCX

از Admin روی «اسناد» و سپس «افزودن سند» بزنید، یا درخواست `multipart/form-data` به `/api/documents/` بفرستید. فقط فرمت `.docx` پذیرفته می‌شود. پس از ذخیره، متن کامل و chunks خودکار بازسازی می‌شوند.

## داده نمونه و آزمون

برای داده نمونه‌ی آماده: `python manage.py seed_demo`.

فایل JSON نمونه نیز در `fixtures/sample_documents.json` وجود دارد و با این دستور بارگذاری می‌شود:

```bash
python manage.py loaddata sample_documents
python manage.py seed_demo  # برای ساخت chunks لازم است
```

تست‌ها:

```bash
python manage.py test
```

## نکات

1. یک سند DOCX را از Admin اضافه کنید و متن استخراج‌شده را نشان دهید.
2. هر سند به chunks تبدیل می‌شود تا متن بی‌ربط به مدل داده نشود.
3. با `POST /api/history/ask/` یک سوال بپرسید و `sources` پاسخ را نمایش دهید.
4. LangChain ابتدا با `ChatOpenAI` چند عبارت مرتبط با پرسش می‌سازد، سپس `RunnableLambda` و BM25 روی پرسشِ گسترش‌یافته جست‌وجو می‌کنند.
5. محدودیت فعلی: این گسترش معنایی از vector search دقیق‌تر نیست. راه توسعه: embeddings + Chroma/pgvector، احراز هویت API و PostgreSQL.
6. برای دمو سریع، از صفحهٔ «پرسش از اسناد» در Django Admin استفاده کنید؛ پاسخ و منابع در همان پنل دیده می‌شوند.

## ساختار پوشه‌ها

```text
config/       تنظیمات Django و URLها
knowledge/    مدل‌ها، API، منطق RAG، Admin و تست‌ها
docs/         مستندات API
fixtures/     داده‌ی نمونه
```

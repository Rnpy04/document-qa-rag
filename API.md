# مستندات API

آدرس پایه: `http://localhost:8000/api/`. پاسخ‌ها JSON هستند. در حالت توسعه، رابط قابل مرور Django REST Framework نیز در همین آدرس‌ها دیده می‌شود.

## ۱. مدیریت اسناد

| Method | URL | کاربرد |
| --- | --- | --- |
| GET | `/documents/` | فهرست سندها |
| POST | `/documents/` | ایجاد سند متنی یا آپلود DOCX |
| GET | `/documents/{id}/` | مشاهده یک سند |
| PATCH | `/documents/{id}/` | ویرایش عنوان/متن/فایل |
| DELETE | `/documents/{id}/` | حذف سند و chunks آن |

### ایجاد سند متنی

```http
POST /api/documents/
Content-Type: application/json

{"title": "راهنمای پروژه", "content": "Django برای ساخت API استفاده شده است."}
```

### آپلود DOCX

```bash
curl -X POST http://localhost:8000/api/documents/ \
  -F "title=جلسه اول" -F "source_file=@my-document.docx"
```

پاسخ شامل `content` (متن استخراج‌شده) و `chunks_count` است.

## ۲. پرسیدن سؤال

```http
POST /api/history/ask/
Content-Type: application/json

{"question": "سامانه چگونه پاسخ می‌دهد؟"}
```

نمونه پاسخ:

```json
{
  "id": 3,
  "question": "سامانه چگونه پاسخ می‌دهد؟",
  "expanded_terms": ["روش پاسخ‌گویی سامانه", "مراحل تولید جواب"],
  "expansion_method": "llm",
  "answer": "...",
  "used_llm": true,
  "sources": [
    {"id": 1, "document": 1, "document_title": "راهنمای سامانه", "position": 1, "content": "..."}
  ],
  "created_at": "2026-11-18T10:00:00+03:30"
}
```

`used_llm=false` یعنی کلید OpenRouter تنظیم نشده یا سرویس خارجی موقتاً پاسخ نداده است؛ در این حالت پاسخ همچنان قطعه‌های واقعی بازیابی‌شده را نمایش می‌دهد و API خطای 503 نمی‌دهد.

`expanded_terms` عبارت‌های مرتبطی هستند که پیش از جست‌وجوی BM25 ساخته شده‌اند. `expansion_method` مشخص می‌کند منبع آن‌ها چیست: `llm`، `local_fallback` یا `none`. این فیلد نشان می‌دهد چرا جست‌وجو ممکن است فراتر از واژه‌های دقیقِ پرسش نتیجه پیدا کند.

## ۳. تاریخچه

| Method | URL | کاربرد |
| --- | --- | --- |
| GET | `/history/` | فهرست همه پرسش‌ها و پاسخ‌ها |
| GET | `/history/{id}/` | یک رکورد تاریخچه |

## وضعیت‌های خطا

- `400`: پرسش خالی یا فایلی غیر از DOCX فرستاده شده است.
- `404`: شناسه سند/تاریخچه وجود ندارد.
- `201`: سند یا پرسش با موفقیت ساخته شده است.
- `204`: حذف با موفقیت انجام شده است.

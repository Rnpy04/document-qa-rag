from django.core.management.base import BaseCommand
from knowledge.models import Document
from knowledge.services import ingest_document


DEMO_DOCUMENTS = [
    ("راهنمای سامانه", "این سامانه برای پرسش از اسناد طراحی شده است. هر سند به بخش‌های کوچک تقسیم می‌شود. سپس بخش‌های مرتبط با پرسش کاربر پیدا می‌شوند و مدل زبانی فقط با تکیه بر همان بخش‌ها پاسخ می‌دهد."),
    ("راهنمای بازیابی", "بازیابی در این پروژه با BM25 انجام می‌شود. BM25 واژه‌های پرسش را با واژه‌های متن مقایسه می‌کند و بخش‌های نزدیک‌تر را برمی‌گرداند. محدود کردن تعداد بخش‌ها باعث می‌شود پاسخ مدل دقیق‌تر و کم‌هزینه‌تر باشد."),
]


class Command(BaseCommand):
    help = "دو سند نمونه برای آزمودن سامانه می‌سازد."

    def handle(self, *args, **options):
        for title, content in DEMO_DOCUMENTS:
            document, _ = Document.objects.update_or_create(title=title, defaults={"content": content})
            ingest_document(document)
        # پیام ASCII است تا در ترمینال‌های ویندوز با encoding قدیمی هم خطا ندهد.
        self.stdout.write(self.style.SUCCESS("Demo data created."))

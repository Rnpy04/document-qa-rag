# Generated manually for a small, portable classroom project.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Document",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255, verbose_name="عنوان")),
                ("source_file", models.FileField(blank=True, null=True, upload_to="documents/", verbose_name="فایل DOCX")),
                ("content", models.TextField(blank=True, verbose_name="متن کامل سند")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="آخرین تغییر")),
            ],
            options={"verbose_name": "سند", "verbose_name_plural": "اسناد", "ordering": ["-updated_at"]},
        ),
        migrations.CreateModel(
            name="DocumentChunk",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("content", models.TextField()), ("position", models.PositiveIntegerField()),
                ("document", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="chunks", to="knowledge.document")),
            ],
            options={"ordering": ["document_id", "position"]},
        ),
        migrations.CreateModel(
            name="QuestionAnswer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("question", models.TextField(verbose_name="پرسش")), ("answer", models.TextField(verbose_name="پاسخ")),
                ("used_llm", models.BooleanField(default=False, verbose_name="پاسخ مدل زبانی")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="تاریخ")),
                ("sources", models.ManyToManyField(blank=True, related_name="answers", to="knowledge.documentchunk")),
            ],
            options={"verbose_name": "پرسش و پاسخ", "verbose_name_plural": "تاریخچه پرسش‌ها و پاسخ‌ها", "ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(model_name="documentchunk", constraint=models.UniqueConstraint(fields=("document", "position"), name="unique_chunk_position")),
    ]

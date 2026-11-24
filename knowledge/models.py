from django.db import models


class Document(models.Model):
    """یک سند اصلی؛ متن کامل جدا از فایل نگه‌داری می‌شود تا جست‌وجو سریع باشد."""
    title = models.CharField("عنوان", max_length=255)
    source_file = models.FileField("فایل DOCX", upload_to="documents/", blank=True, null=True)
    content = models.TextField("متن کامل سند", blank=True)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین تغییر", auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "سند"
        verbose_name_plural = "اسناد"

    def __str__(self):
        return self.title


class DocumentChunk(models.Model):
    """تکه‌های کوچک سند؛ واحد واقعی بازیابی در RAG هستند."""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chunks")
    content = models.TextField()
    position = models.PositiveIntegerField()

    class Meta:
        ordering = ["document_id", "position"]
        constraints = [models.UniqueConstraint(fields=["document", "position"], name="unique_chunk_position")]

    def __str__(self):
        return f"{self.document.title} - بخش {self.position}"


class QuestionAnswer(models.Model):
    question = models.TextField("پرسش")
    expanded_terms = models.JSONField("عبارت‌های مرتبط برای جست‌وجو", default=list, blank=True)
    expansion_method = models.CharField("روش گسترش پرسش", max_length=20, default="none")
    answer = models.TextField("پاسخ")
    used_llm = models.BooleanField("پاسخ مدل زبانی", default=False)
    created_at = models.DateTimeField("تاریخ", auto_now_add=True)
    sources = models.ManyToManyField(DocumentChunk, related_name="answers", blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "پرسش و پاسخ"
        verbose_name_plural = "تاریخچه پرسش‌ها و پاسخ‌ها"

    def __str__(self):
        return self.question[:70]

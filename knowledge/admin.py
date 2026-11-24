from django import forms
from django.contrib import admin, messages
from django.shortcuts import render
from django.urls import path
from .models import Document, DocumentChunk, QuestionAnswer
from .services import answer_question, ingest_document, rebuild_chunks


class AskDocumentForm(forms.Form):
    question = forms.CharField(label="پرسش", widget=forms.Textarea(attrs={"rows": 3, "placeholder": "مثال: حداکثر مرخصی سالانه چند روز کاری است؟"}))


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "source_file", "updated_at")
    search_fields = ("title", "content")
    readonly_fields = ("created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # اگر فایل جدید انتخاب شده باشد، متن و بخش‌ها را به‌روز می‌کنیم.
        if "source_file" in form.changed_data:
            ingest_document(obj)
        elif "content" in form.changed_data:
            rebuild_chunks(obj)


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ("document", "position")
    search_fields = ("content", "document__title")


@admin.register(QuestionAnswer)
class QuestionAnswerAdmin(admin.ModelAdmin):
    list_display = ("question", "used_llm", "created_at")
    search_fields = ("question", "answer")
    filter_horizontal = ("sources",)
    change_list_template = "admin/knowledge/questionanswer/change_list.html"

    def get_urls(self):
        custom_urls = [
            path("ask/", self.admin_site.admin_view(self.ask_view), name="knowledge_questionanswer_ask"),
        ]
        return custom_urls + super().get_urls()

    def ask_view(self, request):
        form = AskDocumentForm(request.POST or None)
        result = None
        if request.method == "POST" and form.is_valid():
            result = answer_question(form.cleaned_data["question"])
            messages.success(request, "پاسخ ثبت شد و به تاریخچه اضافه شد.")
        context = {
            **self.admin_site.each_context(request),
            "title": "پرسش از اسناد",
            "form": form,
            "result": result,
        }
        return render(request, "admin/knowledge/questionanswer/ask.html", context)

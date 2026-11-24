from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from docx import Document as DocxDocument

from knowledge.models import Document
from knowledge.serializers import DocumentSerializer
from knowledge.services import ingest_document


class DocumentEditingTests(TestCase):
    def test_manual_content_edit_does_not_get_replaced_by_old_docx(self):
        buffer = BytesIO()
        word_document = DocxDocument()
        word_document.add_paragraph("متن قدیمی داخل فایل")
        word_document.save(buffer)
        document = Document.objects.create(
            title="سند قابل ویرایش",
            source_file=SimpleUploadedFile("editable.docx", buffer.getvalue()),
        )
        ingest_document(document)
        serializer = DocumentSerializer(document, data={"content": "متن جدیدِ دستی"}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        document.refresh_from_db()
        self.assertEqual(document.content, "متن جدیدِ دستی")
        self.assertEqual(document.chunks.first().content, "متن جدیدِ دستی")

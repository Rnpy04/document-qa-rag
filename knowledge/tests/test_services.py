import os
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from docx import Document as DocxDocument
from knowledge.models import Document
from unittest.mock import patch

from knowledge.services import answer_question, expand_question, expand_question_details, ingest_document, retrieve, split_text


class RAGServiceTests(TestCase):
    def setUp(self):
        self.api_key = os.environ.pop("OPENROUTER_API_KEY", None)
        self.document = Document.objects.create(title="آزمون", content="Django یک چارچوب وب پایتون است. سامانه با Docker اجرا می‌شود.")
        ingest_document(self.document)

    def tearDown(self):
        if self.api_key is not None:
            os.environ["OPENROUTER_API_KEY"] = self.api_key

    def test_text_is_chunked(self):
        self.assertEqual(split_text(""), [])
        self.assertGreaterEqual(self.document.chunks.count(), 1)

    def test_question_is_saved_with_sources(self):
        result = answer_question("سامانه با چه چیزی اجرا می‌شود؟")
        self.assertIn("Docker", result.answer)
        self.assertFalse(result.used_llm)
        self.assertGreater(result.sources.count(), 0)

    def test_docx_is_extracted(self):
        buffer = BytesIO()
        word_document = DocxDocument()
        word_document.add_paragraph("این متن از فایل DOCX خوانده می‌شود.")
        word_document.save(buffer)
        document = Document.objects.create(
            title="فایل آزمایشی",
            source_file=SimpleUploadedFile("test.docx", buffer.getvalue()),
        )
        ingest_document(document)
        document.refresh_from_db()
        self.assertIn("DOCX", document.content)
        self.assertEqual(document.chunks.count(), 1)

    @patch("knowledge.services.expand_question")
    def test_query_expansion_helps_bm25_find_synonyms(self, mock_expand):
        document = Document.objects.create(title="مرخصی", content="هر کارمند سهمیه تعطیلات با حقوق دارد.")
        ingest_document(document)
        unrelated = Document.objects.create(title="تجهیزات", content="لپ‌تاپ و شارژر هنگام پایان همکاری تحویل داده می‌شوند.")
        ingest_document(unrelated)
        mock_expand.return_value = ["سهمیه تعطیلات", "مرخصی با حقوق"]
        results = retrieve("مرخصی")
        self.assertEqual(results[0].document.title, "مرخصی")
        mock_expand.assert_called_once_with("مرخصی")

    def test_query_expansion_does_not_need_llm_key(self):
        self.assertEqual(expand_question("مدل زبانی چیست؟"), [])

    def test_local_expansion_is_returned_when_llm_is_unavailable(self):
        terms, method = expand_question_details("سهمیه مرخصی سالانه چقدر است؟")
        self.assertEqual(method, "local_fallback")
        self.assertIn("تعطیلات با حقوق", terms)

    @patch("knowledge.services._openrouter_llm")
    @patch("knowledge.services.expand_question_details", return_value=([], "none"))
    def test_provider_error_returns_document_based_answer_not_503(self, _, mock_llm):
        mock_llm.return_value.invoke.side_effect = RuntimeError("temporary provider limit")
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            result = answer_question("سامانه با چه چیزی اجرا می‌شود؟")
        self.assertFalse(result.used_llm)
        self.assertIn("Docker", result.answer)
        self.assertIn("مدل زبانی موقتاً در دسترس نبود", result.answer)

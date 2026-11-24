import os
from rest_framework.test import APITestCase
from knowledge.models import Document
from knowledge.services import ingest_document


class ApiTests(APITestCase):
    def setUp(self):
        self.api_key = os.environ.pop("OPENROUTER_API_KEY", None)
        document = Document.objects.create(title="سند", content="OpenRouter مدل زبانی را فراهم می‌کند.")
        ingest_document(document)

    def tearDown(self):
        if self.api_key is not None:
            os.environ["OPENROUTER_API_KEY"] = self.api_key

    def test_create_document_and_ask(self):
        response = self.client.post("/api/documents/", {"title": "جدید", "content": "LangChain ابزار ساخت زنجیره است."}, format="json")
        self.assertEqual(response.status_code, 201)
        response = self.client.post("/api/history/ask/", {"question": "مدل زبانی چیست؟"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIn("sources", response.data)
        self.assertEqual(response.data["expanded_terms"], [])

    def test_answer_returns_related_terms_and_method(self):
        response = self.client.post("/api/history/ask/", {"question": "مرخصی چیست؟"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIn("تعطیلات با حقوق", response.data["expanded_terms"])
        self.assertEqual(response.data["expansion_method"], "local_fallback")

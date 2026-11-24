import os

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from knowledge.models import Document
from knowledge.services import ingest_document


class AdminAskViewTests(TestCase):
    def setUp(self):
        self.api_key = os.environ.pop("OPENROUTER_API_KEY", None)
        self.user = get_user_model().objects.create_superuser("admin", "admin@example.com", "password")
        document = Document.objects.create(title="مرخصی", content="سهمیه مرخصی سالانه ۲۴ روز کاری است.")
        ingest_document(document)
        self.client.force_login(self.user)

    def tearDown(self):
        if self.api_key is not None:
            os.environ["OPENROUTER_API_KEY"] = self.api_key

    def test_admin_can_ask_question_and_view_result(self):
        url = reverse("admin:knowledge_questionanswer_ask")
        response = self.client.post(url, {"question": "مرخصی چیست؟"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "تعطیلات با حقوق")
        self.assertContains(response, "پاسخ موقت")

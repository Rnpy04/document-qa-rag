from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Document, QuestionAnswer
from .serializers import DocumentSerializer, QuestionAnswerSerializer
from .services import answer_question


class DocumentViewSet(viewsets.ModelViewSet):
    """CRUD سندها. برای آپلود، درخواست را با multipart/form-data بفرستید."""
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer


class QuestionAnswerViewSet(viewsets.ReadOnlyModelViewSet):
    """تاریخچه را نمایش می‌دهد و action `ask` یک پرسش جدید ثبت می‌کند."""
    queryset = QuestionAnswer.objects.prefetch_related("sources__document")
    serializer_class = QuestionAnswerSerializer

    @action(detail=False, methods=["post"])
    def ask(self, request):
        question = str(request.data.get("question", "")).strip()
        if not question:
            return Response({"question": ["متن پرسش الزامی است."]}, status=status.HTTP_400_BAD_REQUEST)
        result = answer_question(question)
        return Response(self.get_serializer(result).data, status=status.HTTP_201_CREATED)

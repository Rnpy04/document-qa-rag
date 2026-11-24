from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet, QuestionAnswerViewSet

router = DefaultRouter()
router.register("documents", DocumentViewSet, basename="document")
router.register("history", QuestionAnswerViewSet, basename="history")

urlpatterns = router.urls

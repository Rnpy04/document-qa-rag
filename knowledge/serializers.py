from rest_framework import serializers
from .models import Document, DocumentChunk, QuestionAnswer
from .services import ingest_document, rebuild_chunks


class DocumentSerializer(serializers.ModelSerializer):
    chunks_count = serializers.IntegerField(source="chunks.count", read_only=True)

    class Meta:
        model = Document
        fields = ("id", "title", "source_file", "content", "chunks_count", "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at", "chunks_count")

    def validate_source_file(self, value):
        if value and not value.name.lower().endswith(".docx"):
            raise serializers.ValidationError("فقط فایل DOCX قابل بارگذاری است.")
        return value

    def create(self, validated_data):
        document = super().create(validated_data)
        ingest_document(document)
        return document

    def update(self, instance, validated_data):
        file_changed = "source_file" in validated_data
        document = super().update(instance, validated_data)
        # تغییر متن دستی هم باید ایندکس را تازه کند.
        if file_changed:
            ingest_document(document)
        elif "content" in validated_data:
            rebuild_chunks(document)
        return document


class SourceSerializer(serializers.ModelSerializer):
    document_title = serializers.CharField(source="document.title", read_only=True)

    class Meta:
        model = DocumentChunk
        fields = ("id", "document", "document_title", "position", "content")


class QuestionAnswerSerializer(serializers.ModelSerializer):
    sources = SourceSerializer(many=True, read_only=True)

    class Meta:
        model = QuestionAnswer
        fields = ("id", "question", "expanded_terms", "expansion_method", "answer", "used_llm", "sources", "created_at")
        read_only_fields = ("expanded_terms", "expansion_method", "answer", "used_llm", "sources", "created_at")

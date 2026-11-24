"""هسته‌ی کوچک RAG: استخراج -> تکه‌بندی -> بازیابی -> تولید پاسخ."""
import os
import re
from pathlib import Path

from docx import Document as DocxDocument
from langchain_core.runnables import RunnableLambda
from rank_bm25 import BM25Okapi

from .models import Document, DocumentChunk, QuestionAnswer


CHUNK_SIZE = 700
CHUNK_OVERLAP = 120

# fallback کوچک و شفاف: فقط وقتی سرویس LLM در دسترس نیست استفاده می‌شود.
LOCAL_RELATED_TERMS = {
    "مرخصی": ["تعطیلات با حقوق", "سهمیه مرخصی", "روزهای استحقاقی"],
    "دورکاری": ["کار از راه دور", "کار ریموت"],
    "حضور": ["غیاب", "ثبت ورود و خروج"],
    "امنیت": ["حفاظت اطلاعات", "رمز عبور و دسترسی"],
    "تجهیزات": ["لپ‌تاپ و وسایل تحویلی", "تحویل دارایی"],
}


def _openrouter_llm():
    """تنظیم اتصال LLM در یک جا، برای گسترش پرسش و تولید پاسخ."""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=os.getenv("OPENROUTER_MODEL", "openrouter/free"),
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
        temperature=0,
    )


def extract_docx(uploaded_file) -> str:
    """پاراگراف‌ها و جدول‌های DOCX را به یک متن قابل جست‌وجو تبدیل می‌کند."""
    doc = DocxDocument(uploaded_file)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            values = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if values:
                paragraphs.append(" | ".join(values))
    return "\n".join(paragraphs)


def split_text(text: str) -> list[str]:
    """تکه‌بندی با هم‌پوشانی؛ ساده، قابل تنظیم و مناسب متن فارسی."""
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    chunks, start = [], 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        if end < len(text):
            # تا جای ممکن جمله را کامل نگه می‌داریم.
            boundary = max(text.rfind(". ", start, end), text.rfind("؟", start, end), text.rfind("!", start, end))
            if boundary > start + CHUNK_SIZE // 2:
                end = boundary + 1
        chunks.append(text[start:end].strip())
        if end == len(text):
            break
        start = max(end - CHUNK_OVERLAP, start + 1)
    return chunks


def rebuild_chunks(document: Document) -> Document:
    """ایندکس یک متنِ از پیش آماده را دوباره می‌سازد."""
    DocumentChunk.objects.filter(document=document).delete()
    DocumentChunk.objects.bulk_create([
        DocumentChunk(document=document, content=part, position=index)
        for index, part in enumerate(split_text(document.content), start=1)
    ])
    return document


def ingest_document(document: Document) -> Document:
    """فایل DOCX را می‌خواند، متن کامل را نگه می‌دارد و ایندکس را می‌سازد."""
    if document.source_file:
        if Path(document.source_file.name).suffix.lower() != ".docx":
            raise ValueError("فقط فایل‌های DOCX پشتیبانی می‌شوند.")
        document.source_file.open("rb")
        try:
            document.content = extract_docx(document.source_file)
        finally:
            document.source_file.close()
        document.save(update_fields=["content", "updated_at"])
    return rebuild_chunks(document)


def _local_related_terms(question: str) -> list[str]:
    terms = []
    for keyword, related_terms in LOCAL_RELATED_TERMS.items():
        if keyword in question:
            terms.extend(related_terms)
    return list(dict.fromkeys(terms))[:3]


def expand_question_details(question: str) -> tuple[list[str], str]:
    """چند واژه هم‌معنا می‌گیرد تا BM25 فقط به کلمات دقیق وابسته نباشد.

    این روش عمداً ساده است: نه مدل embedding دانلود می‌کند و نه دیتابیس جدید می‌خواهد.
    اگر این مرحله خطا بخورد، جست‌وجو با همان پرسش اصلی ادامه می‌یابد.
    """
    if not os.getenv("OPENROUTER_API_KEY"):
        terms = _local_related_terms(question)
        return terms, "local_fallback" if terms else "none"
    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        response = _openrouter_llm().invoke([
            SystemMessage(content="پرسش فارسی را پاسخ نده. فقط حداکثر سه عبارت کوتاه هم‌معنا یا مرتبط برای بهتر شدن جست‌وجوی سند برگردان. عبارت‌ها را فقط با | جدا کن."),
            HumanMessage(content=question),
        ])
        additions = response.content if isinstance(response.content, str) else str(response.content)
        terms = []
        for term in additions.replace("\n", "|").split("|"):
            term = term.strip(" -•،.\t")
            if term and term != question and term not in terms:
                terms.append(term[:80])
        return terms[:3], "llm"
    except Exception:
        terms = _local_related_terms(question)
        return terms, "local_fallback" if terms else "none"


def expand_question(question: str) -> list[str]:
    """فقط عبارت‌ها را برمی‌گرداند؛ برای سازگاری با بازیابی BM25."""
    return expand_question_details(question)[0]


def retrieve(question: str, limit: int = 4, expanded_terms: list[str] | None = None) -> list[DocumentChunk]:
    """بازیابی BM25 با کمک گسترش معنایی ساده‌ی پرسش توسط LLM."""
    chunks = list(DocumentChunk.objects.select_related("document").all())
    if not chunks:
        return []
    tokenized_chunks = [re.findall(r"\w+", chunk.content.lower()) for chunk in chunks]

    def bm25_search(query: str) -> list[DocumentChunk]:
        scores = BM25Okapi(tokenized_chunks).get_scores(re.findall(r"\w+", query.lower()))
        indices = sorted(range(len(chunks)), key=lambda index: scores[index], reverse=True)
        return [chunks[index] for index in indices[: min(len(chunks), limit * 3)]]

    # RunnableLambda یعنی بازیابی هم بخشی از زنجیره‌ی قابل توسعه LangChain است.
    expanded_terms = expand_question(question) if expanded_terms is None else expanded_terms
    search_query = " ".join([question, *expanded_terms])
    ranked = RunnableLambda(bm25_search).invoke(search_query)
    results, per_document = [], {}
    for item in ranked:
        count = per_document.get(item.document_id, 0)
        if count < 2:  # یک سند بزرگ همه‌ی نتایج را اشغال نکند.
            results.append(item)
            per_document[item.document_id] = count + 1
        if len(results) == limit:
            break
    return results


def _fallback_answer(sources: list[DocumentChunk]) -> str:
    if not sources:
        return "در اسناد ثبت‌شده، محتوای مرتبطی پیدا نشد. ابتدا یک سند اضافه کنید یا پرسش را دقیق‌تر بنویسید."
    excerpts = "\n\n".join(f"- {c.content}" for c in sources)
    return "پاسخ موقت از بخش‌های مرتبط اسناد (برای پاسخ روان‌تر، کلید OpenRouter را تنظیم کنید):\n\n" + excerpts


def answer_question(question: str) -> QuestionAnswer:
    """بازیابی محتوا و سپس تولید پاسخ با OpenRouter؛ بدون کلید، fallback آموزشی."""
    expanded_terms, expansion_method = expand_question_details(question)
    sources = retrieve(question, expanded_terms=expanded_terms)
    context = "\n\n".join(f"[منبع: {c.document.title}]\n{c.content}" for c in sources)
    api_key = os.getenv("OPENROUTER_API_KEY")
    used_llm = False
    answer = _fallback_answer(sources)
    if api_key and sources:
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            response = _openrouter_llm().invoke([
                SystemMessage(content="فقط بر اساس متن منابع پاسخ فارسی، دقیق و کوتاه بده. اگر پاسخ در منابع نیست، صادقانه بگو پیدا نشد."),
                HumanMessage(content=f"منابع:\n{context}\n\nپرسش: {question}"),
            ])
            answer = response.content if isinstance(response.content, str) else str(response.content)
            used_llm = True
        except Exception as exc:
            # محدودیت موقت provider نباید کل سامانه را با 503 از کار بیندازد.
            # `used_llm=false` و متن پاسخ، عدم استفاده از LLM را کاملاً شفاف می‌کنند.
            answer = _fallback_answer(sources)
            answer += f"\n\n(مدل زبانی موقتاً در دسترس نبود: {exc.__class__.__name__})"
    record = QuestionAnswer.objects.create(
        question=question,
        expanded_terms=expanded_terms,
        expansion_method=expansion_method,
        answer=answer,
        used_llm=used_llm,
    )
    record.sources.set(sources)
    return record

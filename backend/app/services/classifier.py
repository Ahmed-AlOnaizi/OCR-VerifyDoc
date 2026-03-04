from app.models.document import DocType
from app.services.normalization import normalize_unicode

KEYWORDS: dict[DocType, list[str]] = {
    DocType.CIVIL_ID: [
        "civil id card",
        "civil id no",
        "الرقم المدنى",
        "الرقم المدني",
        "البطاقة المدنية",
    ],
    DocType.SALARY_TRANSFER: [
        "to whom it may concern",
        "خطاب تحويل",
        "شهادة راتب",
    ],
    DocType.BANK_STATEMENT: [
        "account statement",
        "statement from date",
        "beginning balance",
        "كشف حساب",
    ],
}


def classify_document(text: str) -> DocType | None:
    """Score OCR text against keyword lists. Highest score wins."""
    lower = normalize_unicode(text).lower()
    scores: dict[DocType, int] = {}

    for doc_type, keywords in KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in lower)
        if score > 0:
            scores[doc_type] = score

    if not scores:
        return None

    return max(scores, key=scores.get)

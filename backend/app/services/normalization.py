import re
import unicodedata

# Arabic-Indic digits → Western digits
_ARABIC_DIGIT_MAP = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

# Extended Arabic-Indic digits (used in some OCR)
_EXTENDED_DIGIT_MAP = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")


def normalize_unicode(text: str) -> str:
    """Normalize Unicode presentation forms (e.g. Arabic Presentation Forms-B) to standard characters."""
    return unicodedata.normalize("NFKC", text)


def normalize_digits(text: str) -> str:
    """Convert Arabic-Indic and Extended Arabic-Indic digits to Western."""
    return text.translate(_ARABIC_DIGIT_MAP).translate(_EXTENDED_DIGIT_MAP)


def normalize_whitespace(text: str) -> str:
    """Collapse multiple whitespace characters into single spaces and strip."""
    return re.sub(r"\s+", " ", text).strip()


def normalize_arabic(text: str) -> str:
    """Normalize Arabic text: remove diacritics, normalize alef/taa forms."""
    # Remove Arabic diacritics (tashkeel)
    text = re.sub(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E4\u06E7-\u06E8\u06EA-\u06ED]", "", text)
    # Normalize alef variants to plain alef
    text = re.sub(r"[إأآا]", "ا", text)
    # Normalize taa marbouta to haa
    text = text.replace("ة", "ه")
    # Normalize alef maqsura to yaa
    text = text.replace("ى", "ي")
    return text


def casefold_text(text: str) -> str:
    """Unicode-aware case folding for comparison."""
    return unicodedata.normalize("NFKC", text).casefold()


def full_normalize(text: str) -> str:
    """Apply all normalizations."""
    text = normalize_digits(text)
    text = normalize_arabic(text)
    text = normalize_whitespace(text)
    text = casefold_text(text)
    return text

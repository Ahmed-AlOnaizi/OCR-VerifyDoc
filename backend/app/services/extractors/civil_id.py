import re
from dataclasses import dataclass, field

from app.services.normalization import normalize_digits, normalize_whitespace


@dataclass
class CivilIDData:
    civil_id: str = ""
    name_en: str = ""
    name_ar: str = ""
    date_of_birth: str = ""
    nationality: str = ""
    errors: list[str] = field(default_factory=list)


def extract_civil_id(text: str) -> CivilIDData:
    """Extract fields from civil ID card OCR text."""
    result = CivilIDData()
    text = normalize_digits(text)
    lines = [normalize_whitespace(l) for l in text.split("\n") if l.strip()]

    # Extract 12-digit civil ID number
    id_match = re.search(r"\b(\d{12})\b", text)
    if id_match:
        result.civil_id = id_match.group(1)
    else:
        result.errors.append("Could not find 12-digit civil ID number")

    # Extract English name — look for "Name" label and grab the name from it
    # PaddleOCR often puts "Name AHMED F A ALONAIZI" on one line
    name_label_pattern = re.compile(r"\bName\b\s+(.+)", re.IGNORECASE)
    for line in lines:
        m = name_label_pattern.search(line.strip())
        if m:
            candidate = m.group(1).strip()
            # Remove trailing non-name labels (e.g. "Nationality", "Sex")
            candidate = re.split(r"\b(?:Nationality|Sex|Gender|Birth|Expiry)\b", candidate, flags=re.IGNORECASE)[0].strip()
            if len(candidate) >= 3:
                result.name_en = candidate
                break

    # Fallback: all-caps line with at least two words that isn't a header
    if not result.name_en:
        skip_en = {"STATE", "OF", "KUWAIT", "CIVIL", "ID", "CARD", "KUWAITI", "MALE",
                   "FEMALE", "NAME", "NATIONALITY", "GENDER", "DATE", "BIRTH", "EXPIRY"}
        for line in lines:
            stripped = line.strip()
            if len(stripped) < 5:
                continue
            if re.match(r"^[A-Z][A-Z\s\-\.]{4,}$", stripped):
                words = set(stripped.replace("-", " ").split())
                if not words.issubset(skip_en):
                    result.name_en = stripped
                    break

    # Extract Arabic name — look for it near the "اسم" (Name) label or
    # on the line just before the English "Name" line.
    arabic_name_pattern = re.compile(r"[\u0600-\u06FF][\u0600-\u06FF\s\-]{4,}")

    # Strategy 1: line containing "اسم" (Name) label — name may be on the same
    # line, or on the next line (common in clean/fixture text)
    for i, line in enumerate(lines):
        stripped = line.strip()
        if "اسم" in stripped or "الاسم" in stripped:
            # Try same line (remove label words)
            cleaned = re.sub(r"(الاسم|اسم)", "", stripped).strip()
            m = arabic_name_pattern.search(cleaned)
            if m and len(m.group().split()) >= 2:
                result.name_ar = m.group().strip()
                break
            # Try next line
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                m = arabic_name_pattern.search(next_line)
                if m and len(m.group().split()) >= 2:
                    result.name_ar = m.group().strip()
                    break

    # Strategy 2: look up to 3 lines before the English "Name" line.
    # On Kuwait civil IDs the Arabic name sits above the "Name" label,
    # but OCR may insert garbled fragments (e.g. "الس") in between.
    if not result.name_ar:
        for i, line in enumerate(lines):
            if re.search(r"\bName\b", line, re.IGNORECASE) and i > 0:
                for offset in range(1, min(i + 1, 4)):
                    prev = lines[i - offset].strip()
                    m = arabic_name_pattern.search(prev)
                    if m and len(m.group().split()) >= 2:
                        result.name_ar = m.group().strip()
                        break
                if result.name_ar:
                    break

    # Strategy 3: fallback — first Arabic multi-word line that isn't a header
    if not result.name_ar:
        skip_ar = {"دولة", "الكويت", "البطاقة", "المدنية", "الرقم", "المدني", "المدنى",
                   "الاسم", "اسم", "تاريخ", "الميلاد", "الجنسية", "الجنس", "الانتهاء",
                   "الاتنهاء", "كويتي", "ذكر", "أنثى", "بطاقة"}
        for line in lines:
            stripped = line.strip()
            m = arabic_name_pattern.search(stripped)
            if m:
                candidate = m.group().strip()
                words = set(candidate.split())
                if len(words) >= 2 and not words.issubset(skip_ar):
                    result.name_ar = candidate
                    break

    # Extract date of birth
    dob_match = re.search(r"(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})", text)
    if dob_match:
        result.date_of_birth = dob_match.group(1)

    if not result.name_en:
        result.errors.append("Could not extract English name")

    return result

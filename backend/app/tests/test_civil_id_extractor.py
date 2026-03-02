import pytest

from app.services.extractors.civil_id import extract_civil_id


SAMPLE_TEXT = """دولة الكويت
STATE OF KUWAIT
البطاقة المدنية
CIVIL ID CARD

الرقم المدني / Civil ID
281234567890

الاسم / Name
أحمد محمد الصباح
AHMAD MOHAMMAD AL-SABAH

تاريخ الميلاد / Date of Birth
15/03/1988

الجنسية / Nationality
كويتي / KUWAITI

الجنس / Gender
ذكر / MALE
"""


class TestCivilIDExtractor:
    def test_extracts_civil_id(self):
        result = extract_civil_id(SAMPLE_TEXT)
        assert result.civil_id == "281234567890"

    def test_extracts_english_name(self):
        result = extract_civil_id(SAMPLE_TEXT)
        assert result.name_en == "AHMAD MOHAMMAD AL-SABAH"

    def test_extracts_arabic_name(self):
        result = extract_civil_id(SAMPLE_TEXT)
        assert "أحمد" in result.name_ar
        assert "الصباح" in result.name_ar

    def test_extracts_dob(self):
        result = extract_civil_id(SAMPLE_TEXT)
        assert result.date_of_birth == "15/03/1988"

    def test_no_errors(self):
        result = extract_civil_id(SAMPLE_TEXT)
        assert len(result.errors) == 0

    def test_missing_id_reports_error(self):
        result = extract_civil_id("Some random text without any IDs")
        assert len(result.errors) > 0
        assert "civil ID" in result.errors[0].lower() or "12-digit" in result.errors[0].lower()

    def test_arabic_digits_in_id(self):
        text = SAMPLE_TEXT.replace("281234567890", "٢٨١٢٣٤٥٦٧٨٩٠")
        result = extract_civil_id(text)
        assert result.civil_id == "281234567890"

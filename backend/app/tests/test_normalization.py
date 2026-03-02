import pytest

from app.services.normalization import (
    normalize_digits,
    normalize_whitespace,
    normalize_arabic,
    casefold_text,
    full_normalize,
)


class TestNormalizeDigits:
    def test_arabic_indic_digits(self):
        assert normalize_digits("٠١٢٣٤٥٦٧٨٩") == "0123456789"

    def test_extended_arabic_digits(self):
        assert normalize_digits("۰۱۲۳۴۵۶۷۸۹") == "0123456789"

    def test_mixed_digits(self):
        assert normalize_digits("ID: ٢٨١٢٣٤") == "ID: 281234"

    def test_no_change_for_western(self):
        assert normalize_digits("12345") == "12345"


class TestNormalizeWhitespace:
    def test_collapses_spaces(self):
        assert normalize_whitespace("hello   world") == "hello world"

    def test_strips(self):
        assert normalize_whitespace("  hello  ") == "hello"

    def test_tabs_and_newlines(self):
        assert normalize_whitespace("a\t\nb") == "a b"


class TestNormalizeArabic:
    def test_alef_variants(self):
        result = normalize_arabic("إبراهيم أحمد آل")
        assert "إ" not in result
        assert "أ" not in result
        assert "آ" not in result

    def test_taa_marbouta(self):
        assert "ة" not in normalize_arabic("فاطمة")

    def test_removes_diacritics(self):
        result = normalize_arabic("مُحَمَّد")
        assert "ُ" not in result
        assert "َ" not in result


class TestCasefold:
    def test_lowercase(self):
        assert casefold_text("AHMAD") == "ahmad"

    def test_unicode_normalize(self):
        # NFKC normalization
        result = casefold_text("ﬁ")  # fi ligature
        assert result == "fi"


class TestFullNormalize:
    def test_combined(self):
        result = full_normalize("  ٢٨١٢٣٤   AHMAD  ")
        assert result == "281234 ahmad"

import pytest

from app.services.extractors.civil_id import CivilIDData
from app.services.verifiers.civil_id import verify_civil_id


class TestCivilIDVerifier:
    def test_pass_name_match(self):
        data = CivilIDData(
            civil_id="281234567890",
            name_en="AHMAD MOHAMMAD AL-SABAH",
            name_ar="أحمد محمد الصباح",
        )
        result = verify_civil_id(data, "Ahmad Mohammad Al-Sabah", "أحمد محمد الصباح")
        assert result.passed is True
        assert result.name_en_match is True

    def test_fail_completely_different_name(self):
        data = CivilIDData(
            civil_id="281234567890",
            name_en="JOHN SMITH",
        )
        result = verify_civil_id(data, "Ahmad Al-Sabah")
        assert result.name_en_match is False
        assert result.passed is False

    def test_fuzzy_name_match(self):
        data = CivilIDData(
            civil_id="281234567890",
            name_en="AHMAD M AL-SABAH",
        )
        result = verify_civil_id(data, "Ahmad Mohammad Al-Sabah")
        assert result.name_en_score > 0
        # Partial match should still score reasonably
        assert result.name_en_score >= 60

    def test_arabic_name_match(self):
        data = CivilIDData(
            civil_id="281234567890",
            name_en="AHMAD AL-SABAH",
            name_ar="أحمد الصباح",
        )
        result = verify_civil_id(data, "Ahmad Al-Sabah", "أحمد الصباح")
        assert result.name_ar_match is True

    def test_pass_with_only_arabic_name(self):
        """Should pass if Arabic name matches, even if English name is empty."""
        data = CivilIDData(
            civil_id="281234567890",
            name_en="",
            name_ar="أحمد محمد الصباح",
        )
        result = verify_civil_id(data, "Ahmad Al-Sabah", "أحمد محمد الصباح")
        assert result.name_ar_match is True
        assert result.passed is True

    def test_fail_no_name_match(self):
        """Should fail if neither English nor Arabic name matches."""
        data = CivilIDData(
            civil_id="281234567890",
            name_en="JOHN SMITH",
            name_ar="جون سميث",
        )
        result = verify_civil_id(data, "Ahmad Al-Sabah", "أحمد الصباح")
        assert result.name_en_match is False
        assert result.name_ar_match is False
        assert result.passed is False
        assert len(result.errors) >= 1

    def test_civil_id_not_used_for_verification(self):
        """Civil ID number mismatch should NOT cause failure — only names matter."""
        data = CivilIDData(
            civil_id="999999999999",
            name_en="AHMAD MOHAMMAD AL-SABAH",
        )
        result = verify_civil_id(data, "Ahmad Mohammad Al-Sabah")
        assert result.passed is True

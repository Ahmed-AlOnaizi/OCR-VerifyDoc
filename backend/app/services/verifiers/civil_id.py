from dataclasses import dataclass, field

from thefuzz import fuzz

from app.config import settings
from app.services.extractors.civil_id import CivilIDData
from app.services.normalization import casefold_text, normalize_arabic


@dataclass
class CivilIDVerification:
    passed: bool = False
    name_en_score: int = 0
    name_ar_score: int = 0
    name_en_match: bool = False
    name_ar_match: bool = False
    checks: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def verify_civil_id(
    extracted: CivilIDData,
    expected_name_en: str,
    expected_name_ar: str = "",
) -> CivilIDVerification:
    """Verify civil ID data against expected user data. Name-only matching."""
    result = CivilIDVerification()
    threshold = settings.NAME_MATCH_THRESHOLD

    # Check 1: English name fuzzy match
    if extracted.name_en and expected_name_en:
        norm_extracted = casefold_text(extracted.name_en)
        norm_expected = casefold_text(expected_name_en)
        result.name_en_score = fuzz.token_sort_ratio(norm_extracted, norm_expected)
        result.name_en_match = result.name_en_score >= threshold
        result.checks.append({
            "field": "name_en",
            "expected": expected_name_en,
            "extracted": extracted.name_en,
            "score": result.name_en_score,
            "threshold": threshold,
            "match": result.name_en_match,
            "method": "fuzzy_token_sort",
        })

        if not result.name_en_match:
            result.errors.append(
                f"English name mismatch (score {result.name_en_score} < {threshold}): "
                f"expected '{expected_name_en}', got '{extracted.name_en}'"
            )

    # Check 2: Arabic name fuzzy match (if both available)
    if extracted.name_ar and expected_name_ar:
        norm_extracted_ar = normalize_arabic(extracted.name_ar)
        norm_expected_ar = normalize_arabic(expected_name_ar)
        result.name_ar_score = fuzz.token_sort_ratio(norm_extracted_ar, norm_expected_ar)
        result.name_ar_match = result.name_ar_score >= threshold
        result.checks.append({
            "field": "name_ar",
            "expected": expected_name_ar,
            "extracted": extracted.name_ar,
            "score": result.name_ar_score,
            "threshold": threshold,
            "match": result.name_ar_match,
            "method": "fuzzy_token_sort",
        })

        if not result.name_ar_match:
            result.errors.append(
                f"Arabic name mismatch (score {result.name_ar_score} < {threshold}): "
                f"expected '{expected_name_ar}', got '{extracted.name_ar}'"
            )

    # Overall pass: at least one name must match
    result.passed = result.name_en_match or result.name_ar_match

    return result

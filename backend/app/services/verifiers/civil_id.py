from dataclasses import dataclass, field

from thefuzz import fuzz

from app.config import settings
from app.services.extractors.civil_id import CivilIDData
from app.services.normalization import casefold_text, normalize_arabic


@dataclass
class CivilIDVerification:
    passed: bool = False
    best_name_score: int = 0
    best_name_match: bool = False
    checks: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def verify_civil_id(
    extracted: CivilIDData,
    expected_name: str,
) -> CivilIDVerification:
    """Verify civil ID data against expected user data. Name-only matching.

    The single expected_name is compared against both the English and Arabic
    names extracted from the civil ID. The best score wins.
    """
    result = CivilIDVerification()
    threshold = settings.NAME_MATCH_THRESHOLD

    en_score = 0
    ar_score = 0

    # Try English comparison
    if extracted.name_en and expected_name:
        norm_extracted = casefold_text(extracted.name_en)
        norm_expected = casefold_text(expected_name)
        en_score = fuzz.token_sort_ratio(norm_extracted, norm_expected)
        result.checks.append({
            "field": "name_en",
            "expected": expected_name,
            "extracted": extracted.name_en,
            "score": en_score,
            "threshold": threshold,
            "match": en_score >= threshold,
            "method": "fuzzy_token_sort",
        })

    # Try Arabic comparison
    if extracted.name_ar and expected_name:
        norm_extracted_ar = normalize_arabic(extracted.name_ar)
        norm_expected_ar = normalize_arabic(expected_name)
        ar_score = fuzz.token_sort_ratio(norm_extracted_ar, norm_expected_ar)
        result.checks.append({
            "field": "name_ar",
            "expected": expected_name,
            "extracted": extracted.name_ar,
            "score": ar_score,
            "threshold": threshold,
            "match": ar_score >= threshold,
            "method": "fuzzy_token_sort",
        })

    # Best score wins
    result.best_name_score = max(en_score, ar_score)
    result.best_name_match = result.best_name_score >= threshold
    result.passed = result.best_name_match

    if not result.best_name_match:
        result.errors.append(
            f"Name mismatch (best score {result.best_name_score} < {threshold}): "
            f"expected '{expected_name}'"
        )

    return result

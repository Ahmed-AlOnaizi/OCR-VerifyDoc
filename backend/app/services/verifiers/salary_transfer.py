from dataclasses import dataclass, field

from thefuzz import fuzz

from app.config import settings
from app.services.extractors.salary_transfer import SalaryTransferData
from app.services.normalization import casefold_text, normalize_arabic


@dataclass
class SalaryTransferVerification:
    passed: bool = False
    is_salary_letter: bool = False
    name_match: bool = False
    name_score: int = 0
    checks: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def verify_salary_transfer(
    extracted: SalaryTransferData,
    expected_name: str = "",
) -> SalaryTransferVerification:
    """Verify salary transfer letter against expected user data."""
    result = SalaryTransferVerification()
    threshold = settings.NAME_MATCH_THRESHOLD

    # Check 1: Is it a salary transfer letter?
    result.is_salary_letter = extracted.is_salary_transfer_letter
    result.checks.append({
        "field": "document_type",
        "is_salary_letter": result.is_salary_letter,
        "match": result.is_salary_letter,
    })
    if not result.is_salary_letter:
        result.errors.append("Document does not appear to be a salary transfer letter")

    # Check 2: Name match (try both casefold and Arabic normalization, take best)
    if expected_name and extracted.employee_name:
        # English-style comparison
        en_score = fuzz.token_sort_ratio(
            casefold_text(extracted.employee_name),
            casefold_text(expected_name),
        )
        # Arabic-style comparison
        ar_score = fuzz.token_sort_ratio(
            normalize_arabic(extracted.employee_name),
            normalize_arabic(expected_name),
        )
        result.name_score = max(en_score, ar_score)
        result.name_match = result.name_score >= threshold
        result.checks.append({
            "field": "employee_name",
            "expected": expected_name,
            "extracted": extracted.employee_name,
            "score": result.name_score,
            "threshold": threshold,
            "match": result.name_match,
            "method": "fuzzy_token_sort",
        })
        if not result.name_match:
            result.errors.append(f"Employee name mismatch (score {result.name_score})")

    # Overall: must be salary letter AND name match (if name provided)
    required_checks = [result.is_salary_letter]
    if expected_name:
        required_checks.append(result.name_match)

    result.passed = all(required_checks)

    return result

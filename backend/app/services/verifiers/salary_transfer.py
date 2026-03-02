from dataclasses import dataclass, field

from thefuzz import fuzz

from app.config import settings
from app.services.extractors.salary_transfer import SalaryTransferData
from app.services.normalization import casefold_text


@dataclass
class SalaryTransferVerification:
    passed: bool = False
    is_salary_letter: bool = False
    civil_id_match: bool = False
    name_match: bool = False
    name_score: int = 0
    salary_match: bool = False
    checks: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def verify_salary_transfer(
    extracted: SalaryTransferData,
    expected_civil_id: str = "",
    expected_name_en: str = "",
    expected_salary: float = 0.0,
) -> SalaryTransferVerification:
    """Verify salary transfer letter against expected user data."""
    result = SalaryTransferVerification()
    threshold = settings.NAME_MATCH_THRESHOLD
    tolerance = settings.SALARY_STABILITY_TOLERANCE

    # Check 1: Is it a salary transfer letter?
    result.is_salary_letter = extracted.is_salary_transfer_letter
    result.checks.append({
        "field": "document_type",
        "is_salary_letter": result.is_salary_letter,
        "match": result.is_salary_letter,
    })
    if not result.is_salary_letter:
        result.errors.append("Document does not appear to be a salary transfer letter")

    # Check 2: Civil ID match
    if expected_civil_id and extracted.civil_id:
        result.civil_id_match = extracted.civil_id == expected_civil_id
        result.checks.append({
            "field": "civil_id",
            "expected": expected_civil_id,
            "extracted": extracted.civil_id,
            "match": result.civil_id_match,
            "method": "exact",
        })
        if not result.civil_id_match:
            result.errors.append(f"Civil ID mismatch in salary letter")

    # Check 3: Name match
    if expected_name_en and extracted.employee_name:
        norm_extracted = casefold_text(extracted.employee_name)
        norm_expected = casefold_text(expected_name_en)
        result.name_score = fuzz.token_sort_ratio(norm_extracted, norm_expected)
        result.name_match = result.name_score >= threshold
        result.checks.append({
            "field": "employee_name",
            "expected": expected_name_en,
            "extracted": extracted.employee_name,
            "score": result.name_score,
            "threshold": threshold,
            "match": result.name_match,
            "method": "fuzzy_token_sort",
        })
        if not result.name_match:
            result.errors.append(f"Employee name mismatch (score {result.name_score})")

    # Check 4: Salary match
    if expected_salary > 0 and extracted.total_salary > 0:
        result.salary_match = abs(extracted.total_salary - expected_salary) <= expected_salary * tolerance
        result.checks.append({
            "field": "salary",
            "expected": expected_salary,
            "extracted": extracted.total_salary,
            "tolerance": tolerance,
            "match": result.salary_match,
        })
        if not result.salary_match:
            result.errors.append(
                f"Salary mismatch: expected {expected_salary}, got {extracted.total_salary}"
            )

    # Overall: must be salary letter + civil ID match (if available)
    required_checks = [result.is_salary_letter]
    if expected_civil_id:
        required_checks.append(result.civil_id_match)
    if expected_name_en:
        required_checks.append(result.name_match)

    result.passed = all(required_checks)

    return result

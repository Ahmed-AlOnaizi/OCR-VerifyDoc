from dataclasses import dataclass, field

from app.config import settings
from app.services.extractors.bank_statement import BankStatementData


@dataclass
class BankStatementVerification:
    passed: bool = False
    salary_months_found: int = 0
    salary_recurrence_ok: bool = False
    salary_amounts: list[float] = field(default_factory=list)
    salary_stability_ok: bool = False
    average_salary: float = 0.0
    has_loans: bool = False
    loan_count: int = 0
    checks: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def verify_bank_statement(
    extracted: BankStatementData,
) -> BankStatementVerification:
    """Verify bank statement data: salary recurrence, stability, and debt."""
    result = BankStatementVerification()
    min_months = settings.SALARY_RECURRENCE_MIN_MONTHS
    tolerance = settings.SALARY_STABILITY_TOLERANCE

    # Check 1: Salary recurrence
    result.salary_amounts = [
        txn.credit for txn in extracted.salary_credits if txn.credit is not None
    ]
    result.salary_months_found = len(result.salary_amounts)
    result.salary_recurrence_ok = result.salary_months_found >= min_months

    result.checks.append({
        "field": "salary_recurrence",
        "months_found": result.salary_months_found,
        "min_required": min_months,
        "match": result.salary_recurrence_ok,
    })

    if not result.salary_recurrence_ok:
        result.errors.append(
            f"Salary found in {result.salary_months_found} months, "
            f"minimum {min_months} required"
        )

    # Check 2: Salary stability (amounts should be consistent)
    if result.salary_amounts:
        result.average_salary = sum(result.salary_amounts) / len(result.salary_amounts)
        max_deviation = result.average_salary * tolerance
        stable = all(
            abs(amt - result.average_salary) <= max_deviation
            for amt in result.salary_amounts
        )
        result.salary_stability_ok = stable

        result.checks.append({
            "field": "salary_stability",
            "average": result.average_salary,
            "tolerance": tolerance,
            "amounts": result.salary_amounts,
            "match": result.salary_stability_ok,
        })

        if not result.salary_stability_ok:
            result.errors.append("Salary amounts are not stable across months")

    # Check 3: Debt detection
    result.has_loans = len(extracted.loan_debits) > 0
    result.loan_count = len(extracted.loan_debits)

    result.checks.append({
        "field": "debt_detection",
        "loans_found": result.loan_count,
        "has_loans": result.has_loans,
    })

    # Overall: salary must recur and be stable
    result.passed = result.salary_recurrence_ok and result.salary_stability_ok

    return result

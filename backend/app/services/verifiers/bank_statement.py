from dataclasses import dataclass, field

from app.config import settings
from app.services.extractors.bank_statement import BankStatementData


@dataclass
class BankStatementVerification:
    passed: bool = False
    eligible: bool = False
    salary_months_found: int = 0
    salary_recurrence_ok: bool = False
    salary_amounts: list[float] = field(default_factory=list)
    salary_stability_ok: bool = False
    average_salary: float = 0.0
    has_loans: bool = False
    loan_count: int = 0
    total_monthly_debt: float = 0.0
    debt_to_salary_ratio: float = 0.0
    debt_ratio_ok: bool = True
    checks: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def verify_bank_statement(
    extracted: BankStatementData,
    expected_salary: float = 0.0,
) -> BankStatementVerification:
    """Verify bank statement data: salary recurrence, stability, and debt."""
    result = BankStatementVerification()
    min_months = settings.SALARY_RECURRENCE_MIN_MONTHS
    tolerance = settings.SALARY_STABILITY_TOLERANCE
    max_ratio = settings.DEBT_TO_SALARY_MAX_RATIO

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

        # Optional: check against expected salary
        if expected_salary > 0:
            salary_match = abs(result.average_salary - expected_salary) <= expected_salary * tolerance
            result.checks.append({
                "field": "salary_amount",
                "expected": expected_salary,
                "average_found": result.average_salary,
                "tolerance": tolerance,
                "match": salary_match,
            })
            if not salary_match:
                result.errors.append(
                    f"Average salary {result.average_salary:.3f} doesn't match "
                    f"expected {expected_salary:.3f}"
                )

    # Check 3: Debt detection
    result.has_loans = len(extracted.loan_debits) > 0
    result.loan_count = len(extracted.loan_debits)

    result.checks.append({
        "field": "debt_detection",
        "loans_found": result.loan_count,
        "has_loans": result.has_loans,
    })

    # Check 4: Debt-to-salary ratio (eligibility)
    if result.has_loans and result.average_salary > 0:
        loan_amounts = [
            txn.debit for txn in extracted.loan_debits if txn.debit is not None
        ]
        total_debt = sum(loan_amounts)

        # Average across distinct months
        loan_months = set()
        for txn in extracted.loan_debits:
            parts = txn.date.split("/")
            if len(parts) >= 2:
                loan_months.add(parts[1])

        num_months = max(len(loan_months), 1)
        result.total_monthly_debt = total_debt / num_months

        result.debt_to_salary_ratio = result.total_monthly_debt / result.average_salary
        result.debt_ratio_ok = result.debt_to_salary_ratio <= max_ratio

        result.checks.append({
            "field": "debt_to_salary_ratio",
            "ratio": round(result.debt_to_salary_ratio, 4),
            "max_allowed": max_ratio,
            "total_monthly_debt": round(result.total_monthly_debt, 3),
            "match": result.debt_ratio_ok,
        })

        if not result.debt_ratio_ok:
            result.errors.append(
                f"Debt-to-salary ratio {result.debt_to_salary_ratio:.1%} "
                f"exceeds maximum {max_ratio:.0%}"
            )

    # Overall: salary must recur and be stable
    result.passed = result.salary_recurrence_ok and result.salary_stability_ok

    # Eligible: passed AND debt ratio OK
    result.eligible = result.passed and result.debt_ratio_ok

    return result

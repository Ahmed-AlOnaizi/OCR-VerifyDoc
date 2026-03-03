import pytest

from app.services.extractors.bank_statement import BankStatementData, Transaction
from app.services.verifiers.bank_statement import verify_bank_statement


def _make_salary_txns(amounts):
    return [
        Transaction(date=f"05/{i+1:02d}/2025", description="SALARY TRANSFER",
                     credit=amt, category="salary")
        for i, amt in enumerate(amounts)
    ]


def _make_loan_txns(count):
    return [
        Transaction(date=f"20/{i+1:02d}/2025", description="LOAN REPAYMENT",
                     debit=250.0, category="loan")
        for i in range(count)
    ]


class TestBankStatementVerifier:
    def test_pass_sufficient_recurrence_and_stability(self):
        data = BankStatementData(
            salary_credits=_make_salary_txns([1500, 1500, 1500, 1500]),
            transactions=_make_salary_txns([1500, 1500, 1500, 1500]),
        )
        result = verify_bank_statement(data)
        assert result.passed is True
        assert result.salary_recurrence_ok is True
        assert result.salary_stability_ok is True

    def test_fail_insufficient_months(self):
        data = BankStatementData(
            salary_credits=_make_salary_txns([1500, 1500]),
            transactions=_make_salary_txns([1500, 1500]),
        )
        result = verify_bank_statement(data)
        assert result.salary_recurrence_ok is False
        assert result.passed is False

    def test_fail_unstable_salary(self):
        data = BankStatementData(
            salary_credits=_make_salary_txns([1500, 1500, 1500, 800]),
            transactions=_make_salary_txns([1500, 1500, 1500, 800]),
        )
        result = verify_bank_statement(data)
        assert result.salary_stability_ok is False
        assert result.passed is False

    def test_detects_loans(self):
        data = BankStatementData(
            salary_credits=_make_salary_txns([1500, 1500, 1500]),
            loan_debits=_make_loan_txns(3),
            transactions=_make_salary_txns([1500, 1500, 1500]) + _make_loan_txns(3),
        )
        result = verify_bank_statement(data)
        assert result.has_loans is True
        assert result.loan_count == 3

    def test_no_loans(self):
        data = BankStatementData(
            salary_credits=_make_salary_txns([1500, 1500, 1500]),
            transactions=_make_salary_txns([1500, 1500, 1500]),
        )
        result = verify_bank_statement(data)
        assert result.has_loans is False

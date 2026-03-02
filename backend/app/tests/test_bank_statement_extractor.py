import pytest

from app.services.extractors.bank_statement import extract_bank_statement


SAMPLE_TEXT = """Kuwait International Bank
Account Statement

Account Holder: AHMAD MOHAMMAD AL-SABAH
Account Number: 0012345678

Date        | Description                    | Debit   | Credit  | Balance
05/07/2025  | SALARY TRANSFER - KPC          |         | 1,500.000 | 3,950.500
10/07/2025  | ATM WITHDRAWAL                 | 200.000 |         | 3,750.500
22/08/2025  | LOAN REPAYMENT - CAR LOAN      | 250.000 |         | 3,715.250
05/08/2025  | SALARY TRANSFER - KPC          |         | 1,500.000 | 4,715.250
05/09/2025  | SALARY TRANSFER - KPC          |         | 1,500.000 | 5,215.250
20/09/2025  | LOAN REPAYMENT - CAR LOAN      | 250.000 |         | 4,365.250
05/10/2025  | SALARY TRANSFER - KPC          |         | 1,500.000 | 5,865.250
05/11/2025  | SALARY TRANSFER - KPC          |         | 1,500.000 | 6,345.250
05/12/2025  | SALARY TRANSFER - KPC          |         | 1,500.000 | 6,945.250
"""


class TestBankStatementExtractor:
    def test_extracts_account_holder(self):
        result = extract_bank_statement(SAMPLE_TEXT)
        assert result.account_holder == "AHMAD MOHAMMAD AL-SABAH"

    def test_extracts_account_number(self):
        result = extract_bank_statement(SAMPLE_TEXT)
        assert result.account_number == "0012345678"

    def test_finds_transactions(self):
        result = extract_bank_statement(SAMPLE_TEXT)
        assert len(result.transactions) >= 6

    def test_classifies_salary(self):
        result = extract_bank_statement(SAMPLE_TEXT)
        assert len(result.salary_credits) >= 4

    def test_classifies_loans(self):
        result = extract_bank_statement(SAMPLE_TEXT)
        assert len(result.loan_debits) >= 1

    def test_salary_amounts(self):
        result = extract_bank_statement(SAMPLE_TEXT)
        for txn in result.salary_credits:
            assert txn.credit == 1500.0

    def test_no_errors(self):
        result = extract_bank_statement(SAMPLE_TEXT)
        assert len(result.errors) == 0

    def test_empty_text_reports_error(self):
        result = extract_bank_statement("No transactions here")
        assert len(result.errors) > 0

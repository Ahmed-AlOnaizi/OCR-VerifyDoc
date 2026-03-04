import pytest

from app.models.document import DocType
from app.services.classifier import classify_document


class TestClassifier:
    def test_civil_id_english(self):
        text = "CIVIL ID CARD\nCivil ID No: 123456789012\nName: John Doe"
        assert classify_document(text) == DocType.CIVIL_ID

    def test_civil_id_arabic(self):
        text = "البطاقة المدنية\nالرقم المدني: 123456789012"
        assert classify_document(text) == DocType.CIVIL_ID

    def test_bank_statement(self):
        text = "Account Statement\nStatement From Date: 01/01/2025\nBeginning Balance: 5000.000"
        assert classify_document(text) == DocType.BANK_STATEMENT

    def test_salary_transfer(self):
        text = "To Whom It May Concern\nThis is to certify that Mr. John Doe receives a salary of 1500 KWD"
        assert classify_document(text) == DocType.SALARY_TRANSFER

    def test_unknown_text(self):
        text = "Some random text that doesn't match anything"
        assert classify_document(text) is None

    def test_bank_statement_with_salary_transfer_transactions(self):
        """Bank statement containing 'SALARY TRANSFER' in transaction lines
        should still be classified as bank_statement, not salary_transfer."""
        text = (
            "Account Statement\n"
            "Statement From Date: 01/01/2025\n"
            "Beginning Balance: 5000.000\n"
            "05/01/2025 SALARY TRANSFER 1,500.000 6,500.000\n"
            "05/02/2025 SALARY TRANSFER 1,500.000 8,000.000\n"
        )
        assert classify_document(text) == DocType.BANK_STATEMENT

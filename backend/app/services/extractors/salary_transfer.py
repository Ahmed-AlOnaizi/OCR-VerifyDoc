import re
from dataclasses import dataclass, field

from app.services.normalization import normalize_digits, normalize_whitespace


@dataclass
class SalaryTransferData:
    employee_name: str = ""
    civil_id: str = ""
    employer: str = ""
    total_salary: float = 0.0
    bank_name: str = ""
    account_number: str = ""
    is_salary_transfer_letter: bool = False
    errors: list[str] = field(default_factory=list)


_SALARY_LETTER_KEYWORDS = {
    "salary transfer", "salary certificate", "تحويل الراتب",
    "خطاب تحويل", "شهادة راتب",
}


def extract_salary_transfer(text: str) -> SalaryTransferData:
    """Extract fields from salary transfer letter OCR text."""
    result = SalaryTransferData()
    text = normalize_digits(text)
    lines = [normalize_whitespace(l) for l in text.split("\n") if l.strip()]

    lower_text = text.lower()
    result.is_salary_transfer_letter = any(kw in lower_text for kw in _SALARY_LETTER_KEYWORDS)

    if not result.is_salary_transfer_letter:
        result.errors.append("Document does not appear to be a salary transfer letter")

    for line in lines:
        # Employee name
        name_match = re.search(r"Employee\s*Name\s*:\s*(.+)", line, re.IGNORECASE)
        if name_match and not result.employee_name:
            result.employee_name = name_match.group(1).strip()

        # Civil ID
        cid_match = re.search(r"Civil\s*ID\s*:\s*(\d{12})", line, re.IGNORECASE)
        if cid_match:
            result.civil_id = cid_match.group(1)

        # Total salary
        salary_match = re.search(r"Total\s*Monthly\s*Salary\s*:\s*(?:KWD\s*)?([0-9,]+\.\d+)", line, re.IGNORECASE)
        if salary_match:
            result.total_salary = float(salary_match.group(1).replace(",", ""))

        # Bank name
        bank_match = re.search(r"Bank\s*Name\s*:\s*(.+)", line, re.IGNORECASE)
        if bank_match:
            result.bank_name = bank_match.group(1).strip()

        # Account number
        acct_match = re.search(r"Account\s*Number\s*:\s*(\d+)", line, re.IGNORECASE)
        if acct_match and not result.account_number:
            result.account_number = acct_match.group(1)

    # Try extracting employer from first non-empty lines (letterhead)
    for line in lines[:5]:
        stripped = line.strip()
        if len(stripped) > 5 and not any(kw in stripped.lower() for kw in ["salary", "date", "whom", "خطاب"]):
            if re.search(r"[A-Za-z]{3,}", stripped):
                result.employer = stripped
                break

    if not result.employee_name:
        result.errors.append("Could not extract employee name")
    if not result.civil_id:
        result.errors.append("Could not extract civil ID")

    return result

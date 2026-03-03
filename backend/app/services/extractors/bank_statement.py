import re
from dataclasses import dataclass, field

from app.services.normalization import normalize_digits, normalize_whitespace


@dataclass
class Transaction:
    date: str
    description: str
    debit: float | None = None
    credit: float | None = None
    balance: float | None = None
    category: str = "other"


@dataclass
class BankStatementData:
    account_holder: str = ""
    account_number: str = ""
    transactions: list[Transaction] = field(default_factory=list)
    salary_credits: list[Transaction] = field(default_factory=list)
    loan_debits: list[Transaction] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


KEYWORD_REGISTRY = {
    "salary": ["salary", "salary transfer", "payroll", "راتب", "تحويل راتب"],
    "loan": ["loan", "loan repayment", "installment", "financing",
             "قرض", "قسط", "اسداد قسط مرابحة", "قسط مرابحة"],
}

_AMOUNT_RE = re.compile(r"[\d,]+\.\d{3}")
_DATE_RE = re.compile(r"\d{1,2}/\d{1,2}/\d{4}")


def _parse_amount(s: str) -> float:
    return float(s.replace(",", ""))


def _classify_transaction(desc: str) -> str:
    lower = desc.lower()
    for category, keywords in KEYWORD_REGISTRY.items():
        if any(kw in lower for kw in keywords):
            return category
    return "other"


def extract_bank_statement(text: str) -> BankStatementData:
    """Extract fields from bank statement OCR text."""
    result = BankStatementData()
    text = normalize_digits(text)
    lines = [normalize_whitespace(l) for l in text.split("\n") if l.strip()]

    # Extract account holder
    for i, line in enumerate(lines):
        holder_match = re.search(r"(?:Account\s*Holder|Client|Name)\s*:?\s*(.+)", line, re.IGNORECASE)
        if holder_match:
            value = holder_match.group(1).strip()
            if value:
                result.account_holder = value
            elif i + 1 < len(lines):
                result.account_holder = lines[i + 1].strip()
            break

    # Extract account number
    for i, line in enumerate(lines):
        acct_match = re.search(r"Account\s*Number\s*:?\s*(\d+)?", line, re.IGNORECASE)
        if acct_match:
            if acct_match.group(1):
                result.account_number = acct_match.group(1).strip()
            elif i + 1 < len(lines):
                num_match = re.match(r"(\d+)", lines[i + 1].strip())
                if num_match:
                    result.account_number = num_match.group(1)
            break

    # Parse transaction lines
    for idx, line in enumerate(lines):
        date_match = _DATE_RE.match(line.strip())
        if not date_match:
            continue

        date_str = date_match.group()
        amounts = _AMOUNT_RE.findall(line)

        # If no amounts on this line, look at subsequent non-date lines
        if not amounts:
            for lookahead in lines[idx + 1:]:
                if _DATE_RE.match(lookahead.strip()):
                    break
                amounts.extend(_AMOUNT_RE.findall(lookahead))

        # Extract description: text between the date and the first amount
        rest = line[date_match.end():].strip()
        desc_match = re.match(r"[|]?\s*(.+?)\s*[|]", rest)
        if desc_match:
            desc = desc_match.group(1).strip()
        else:
            # Fallback: text between date and first number
            desc_part = re.split(r"\d", rest, maxsplit=1)[0]
            desc = re.sub(r"[|]", "", desc_part).strip()

        category = _classify_transaction(desc)

        txn = Transaction(date=date_str, description=desc)

        # Parse amounts based on position
        if len(amounts) >= 3:
            txn.debit = _parse_amount(amounts[0]) if amounts[0] != "0.000" else None
            txn.credit = _parse_amount(amounts[1]) if amounts[1] != "0.000" else None
            txn.balance = _parse_amount(amounts[2])
        elif len(amounts) == 2:
            # Could be debit+balance or credit+balance
            if category == "salary":
                txn.credit = _parse_amount(amounts[0])
                txn.balance = _parse_amount(amounts[1])
            else:
                txn.debit = _parse_amount(amounts[0])
                txn.balance = _parse_amount(amounts[1])
        elif len(amounts) == 1:
            txn.balance = _parse_amount(amounts[0])

        txn.category = category
        result.transactions.append(txn)

        if category == "salary":
            result.salary_credits.append(txn)
        elif category == "loan":
            result.loan_debits.append(txn)

    if not result.transactions:
        result.errors.append("No transactions found in statement")

    return result

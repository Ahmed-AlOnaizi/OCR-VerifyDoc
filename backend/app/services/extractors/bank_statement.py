import re
from dataclasses import dataclass, field

from app.services.normalization import normalize_digits, normalize_unicode, normalize_whitespace


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


_SALARY_KEYWORDS = {"salary", "transfer", "payroll", "راتب"}
_LOAN_KEYWORDS = {"loan", "repayment", "installment", "قرض", "قسط"}

_AMOUNT_RE = re.compile(r"[\d,]+\.\d{3}")
_DATE_RE = re.compile(r"\d{4}/\d{1,2}/\d{1,2}|\d{1,2}/\d{1,2}/\d{4}")
_TRAILING_AMOUNT_RE = re.compile(r"([\d,]+\.\d{3})\s*$")


def _parse_amount(s: str) -> float:
    return float(s.replace(",", ""))


def _classify_transaction(desc: str) -> str:
    lower = desc.lower()
    if any(kw in lower for kw in _SALARY_KEYWORDS):
        return "salary"
    if any(kw in lower for kw in _LOAN_KEYWORDS):
        return "loan"
    return "other"


def _is_date_only(line: str) -> re.Match | None:
    """Check if a line contains only a date (cell-per-line extraction)."""
    m = _DATE_RE.match(line.strip())
    if m and m.group() == line.strip():
        return m
    return None


def _is_standalone_amount(line: str) -> bool:
    """Check if a line is just a single amount value."""
    stripped = line.strip()
    m = _AMOUNT_RE.match(stripped)
    return m is not None and m.group() == stripped


def _add_transaction(result: BankStatementData, txn: Transaction) -> None:
    """Add a transaction to result and classify into salary/loan lists."""
    result.transactions.append(txn)
    if txn.category == "salary":
        result.salary_credits.append(txn)
    elif txn.category == "loan":
        result.loan_debits.append(txn)


def _assign_amounts(txn: Transaction, amounts: list[str], category: str) -> None:
    """Assign debit/credit/balance from a list of amount strings."""
    if len(amounts) >= 3:
        txn.debit = _parse_amount(amounts[0]) if amounts[0] != "0.000" else None
        txn.credit = _parse_amount(amounts[1]) if amounts[1] != "0.000" else None
        txn.balance = _parse_amount(amounts[2])
    elif len(amounts) == 2:
        if category == "salary":
            txn.credit = _parse_amount(amounts[0])
            txn.balance = _parse_amount(amounts[1])
        else:
            txn.debit = _parse_amount(amounts[0])
            txn.balance = _parse_amount(amounts[1])
    elif len(amounts) == 1:
        txn.balance = _parse_amount(amounts[0])


def _parse_multiline_transactions(lines: list[str], result: BankStatementData) -> None:
    """Parse transactions from cell-per-line format (PyMuPDF table extraction).

    Each transaction spans multiple lines:
      - Date on its own line
      - Description on next line(s), possibly with trailing debit amount
      - Remaining amounts (credit, balance) on subsequent lines
    """
    # Find all date-only line indices
    date_indices = []
    for i, line in enumerate(lines):
        if _is_date_only(line):
            date_indices.append(i)

    if not date_indices:
        return

    for pos, line_idx in enumerate(date_indices):
        date_str = lines[line_idx].strip()

        # Collect lines until next date or end
        next_idx = date_indices[pos + 1] if pos + 1 < len(date_indices) else len(lines)
        block = lines[line_idx + 1 : next_idx]

        if not block:
            continue

        # Split block into description lines and amount lines
        desc_parts = []
        amount_strs = []
        for bline in block:
            if _is_standalone_amount(bline):
                amount_strs.append(bline.strip())
            elif amount_strs:
                # Non-amount after amounts → belongs to next block, stop
                break
            else:
                desc_parts.append(bline)

        if not desc_parts:
            continue

        # Check if last description line has a trailing amount (e.g., "راتب0.000")
        last_desc = desc_parts[-1]
        trailing = _TRAILING_AMOUNT_RE.search(last_desc)
        if trailing:
            desc_parts[-1] = last_desc[: trailing.start()].strip()
            amount_strs.insert(0, trailing.group(1))

        desc = " ".join(desc_parts).strip()
        if not desc:
            continue

        category = _classify_transaction(desc)
        txn = Transaction(date=date_str, description=desc)
        _assign_amounts(txn, amount_strs, category)
        txn.category = category
        _add_transaction(result, txn)


def _parse_single_line_transactions(lines: list[str], result: BankStatementData) -> None:
    """Parse transactions where each line contains date + description + amounts."""
    for line in lines:
        date_match = _DATE_RE.match(line.strip())
        if not date_match:
            continue

        date_str = date_match.group()
        amounts = _AMOUNT_RE.findall(line)

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
        _assign_amounts(txn, amounts, category)
        txn.category = category
        _add_transaction(result, txn)


def _extract_account_holder(lines: list[str]) -> str:
    """Extract account holder name from statement lines."""
    for line in lines:
        holder_match = re.search(r"(?:Account\s*Holder|Name)\s*:\s*(.+)", line, re.IGNORECASE)
        if holder_match:
            return holder_match.group(1).strip()
    return ""


def _extract_account_number(lines: list[str]) -> str:
    """Extract account number from statement lines."""
    for line in lines:
        acct_match = re.search(r"Account\s*(?:Number|No\.?)\s*[:\.]?\s*(\d+)", line, re.IGNORECASE)
        if acct_match:
            return acct_match.group(1).strip()
    return ""


def extract_bank_statement(text: str) -> BankStatementData:
    """Extract fields from bank statement OCR text."""
    result = BankStatementData()
    text = normalize_unicode(text)
    text = normalize_digits(text)
    lines = [normalize_whitespace(l) for l in text.split("\n") if l.strip()]

    result.account_holder = _extract_account_holder(lines)
    result.account_number = _extract_account_number(lines)

    # Detect format: date-only lines indicate cell-per-line extraction (PyMuPDF)
    date_only_count = sum(1 for line in lines if _is_date_only(line))

    if date_only_count >= 3:
        _parse_multiline_transactions(lines, result)

    # Fallback to single-line parser (pipe-delimited tables, OCR with inline amounts)
    if not result.transactions:
        _parse_single_line_transactions(lines, result)

    if not result.transactions:
        result.errors.append("No transactions found in statement")

    return result

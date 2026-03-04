"""Standalone OCR test script.

Usage:
    python test_ocr.py <pdf_path> [--out output.json]

Runs PaddleOCR on the given file, then shows:
  - Raw OCR text (per page)
  - Classifier result (detected doc type)
  - Extracted fields (bank statement extractor)
  - Keyword scan (which salary/loan keywords were found and where)
"""

import argparse
import json
import os
import re
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app", ".."))

from app.services.ocr_service import pdf_to_images, PaddleOCRService, _extract_pdf_text
from app.services.classifier import classify_document, KEYWORDS as CLASSIFIER_KEYWORDS
from app.services.extractors.bank_statement import (
    extract_bank_statement, _SALARY_KEYWORDS, _LOAN_KEYWORDS,
)
from app.services.normalization import normalize_digits, normalize_unicode, normalize_whitespace
from dataclasses import asdict


def scan_keywords(text: str) -> dict:
    """Scan text for all salary/loan keywords and report matches with line numbers."""
    lower = text.lower()
    lines = text.split("\n")

    results = {"salary_keywords": {}, "loan_keywords": {}, "classifier_keywords": {}}

    # Salary keywords
    for kw in _SALARY_KEYWORDS:
        hits = []
        for i, line in enumerate(lines, 1):
            if kw in line.lower():
                hits.append({"line": i, "text": line.strip()})
        if hits:
            results["salary_keywords"][kw] = hits
        else:
            results["salary_keywords"][kw] = None

    # Loan keywords
    for kw in _LOAN_KEYWORDS:
        hits = []
        for i, line in enumerate(lines, 1):
            if kw in line.lower():
                hits.append({"line": i, "text": line.strip()})
        if hits:
            results["loan_keywords"][kw] = hits
        else:
            results["loan_keywords"][kw] = None

    # Classifier keywords (all doc types)
    for doc_type, keywords in CLASSIFIER_KEYWORDS.items():
        type_hits = {}
        for kw in keywords:
            found = kw in lower
            type_hits[kw] = found
        results["classifier_keywords"][doc_type.value] = type_hits

    return results


def main():
    parser = argparse.ArgumentParser(description="Test OCR on a document")
    parser.add_argument("pdf_path", help="Path to PDF or image file")
    parser.add_argument("--out", help="Output JSON file path (default: prints to stdout)")
    parser.add_argument("--dpi", type=int, default=150, help="DPI for PDF rendering")
    args = parser.parse_args()

    if not os.path.exists(args.pdf_path):
        print(f"File not found: {args.pdf_path}")
        sys.exit(1)

    print(f"Processing: {args.pdf_path}")

    # Try embedded text extraction first (for digital PDFs)
    embedded_text = None
    if args.pdf_path.lower().endswith(".pdf"):
        print("  Trying embedded text extraction (PyMuPDF)...")
        embedded_text = _extract_pdf_text(args.pdf_path)
        if embedded_text:
            print(f"  Embedded text found: {len(embedded_text)} chars - skipping OCR")
        else:
            print("  No embedded text - falling back to PaddleOCR")

    pages = []
    if embedded_text:
        import fitz
        doc = fitz.open(args.pdf_path)
        all_text_parts = []
        for i, page in enumerate(doc):
            page_text = page.get_text()
            page_lines = [l for l in page_text.split("\n") if l.strip()]
            pages.append({
                "page": i + 1,
                "source": "embedded",
                "line_count": len(page_lines),
                "text": page_text,
            })
            all_text_parts.append(page_text)
        doc.close()
        full_text = "\n".join(all_text_parts)
    else:
        print("  Loading PaddleOCR...")
        ocr_service = PaddleOCRService()

        if args.pdf_path.lower().endswith(".pdf"):
            image_paths = pdf_to_images(args.pdf_path, dpi=args.dpi)
        else:
            image_paths = [args.pdf_path]

        all_text_parts = []
        for i, img_path in enumerate(image_paths):
            print(f"  OCR page {i + 1}/{len(image_paths)}...")
            page_lines = []
            for result in ocr_service._ocr.predict(img_path):
                res = result.json.get("res", result.json) if isinstance(result.json, dict) else {}
                if isinstance(res, dict) and "rec_texts" in res:
                    page_lines.extend(res["rec_texts"])

            page_text = "\n".join(page_lines)
            pages.append({
                "page": i + 1,
                "source": "paddleocr",
                "image": img_path,
                "line_count": len(page_lines),
                "text": page_text,
            })
            all_text_parts.append(page_text)

        full_text = "\n".join(all_text_parts)

    # Normalize for analysis
    normalized_text = normalize_unicode(normalize_digits(full_text))
    normalized_lines = [normalize_whitespace(l) for l in normalized_text.split("\n") if l.strip()]
    normalized_full = "\n".join(normalized_lines)

    print(f"  Total lines: {sum(p['line_count'] for p in pages)}")
    print(f"  Total chars: {len(full_text)}")

    # Classify
    detected_type = classify_document(full_text)
    print(f"  Detected type: {detected_type.value if detected_type else 'UNKNOWN'}")

    # Keyword scan
    print(f"  Scanning keywords...")
    keyword_results = scan_keywords(normalized_full)

    # Extract (bank statement)
    print(f"  Running bank statement extractor...")
    bs_extracted = extract_bank_statement(full_text)
    bs_data = asdict(bs_extracted)

    # Build output
    output = {
        "file": args.pdf_path,
        "pages": len(pages),
        "total_lines": sum(p["line_count"] for p in pages),
        "detected_type": detected_type.value if detected_type else None,
        "keyword_scan": keyword_results,
        "bank_statement_extraction": {
            "account_holder": bs_data["account_holder"],
            "account_number": bs_data["account_number"],
            "total_transactions": len(bs_data["transactions"]),
            "salary_credits_found": len(bs_data["salary_credits"]),
            "loan_debits_found": len(bs_data["loan_debits"]),
            "salary_credits": [
                {"date": t["date"], "description": t["description"],
                 "credit": t["credit"], "category": t["category"]}
                for t in bs_data["salary_credits"]
            ],
            "loan_debits": [
                {"date": t["date"], "description": t["description"],
                 "debit": t["debit"], "category": t["category"]}
                for t in bs_data["loan_debits"]
            ],
            "errors": bs_data["errors"],
        },
        "raw_ocr_per_page": pages,
        "normalized_text": normalized_full,
    }

    out_json = json.dumps(output, ensure_ascii=False, indent=2)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out_json)
        print(f"\nOutput saved to: {args.out}")
    else:
        print("\n" + "=" * 60)
        print(out_json)

    # Print summary (use ascii repr for Arabic to avoid Windows encoding issues)
    def safe(s):
        try:
            return s.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8")
        except Exception:
            return ascii(s)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Detected type: {detected_type.value if detected_type else 'UNKNOWN'}")
    print(f"Salary keywords found:")
    for kw, hits in keyword_results["salary_keywords"].items():
        status = f"{len(hits)} hit(s)" if hits else "NOT FOUND"
        print(f"  {safe(repr(kw))}: {status}")
    print(f"Loan keywords found:")
    for kw, hits in keyword_results["loan_keywords"].items():
        status = f"{len(hits)} hit(s)" if hits else "NOT FOUND"
        print(f"  {safe(repr(kw))}: {status}")
    print(f"Salary credits extracted: {len(bs_data['salary_credits'])}")
    print(f"Loan debits extracted: {len(bs_data['loan_debits'])}")
    print(f"Total transactions: {len(bs_data['transactions'])}")


if __name__ == "__main__":
    main()

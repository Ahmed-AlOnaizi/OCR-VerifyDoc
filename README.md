# OCR-VerifyDoc

A document verification service that accepts uploaded documents (PDFs/images), runs OCR, extracts structured data, and verifies it against a user database. Built for Kuwaiti financial document workflows: Civil IDs, bank statements, and salary transfer letters.

## Quick Start

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Docker
```bash
docker-compose up --build
# API: http://localhost:8000
# UI:  http://localhost:3000
```

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                    React Frontend                        │
│  UserList ─► UserDetail ─► DocumentUploadDialog          │
│                  │              (3 drag-and-drop zones)   │
│                  ▼                                       │
│          VerificationProgress ──► ResultDisplay           │
│             (SSE live updates)    (per-doc feedback)      │
└──────────────────────┬───────────────────────────────────┘
                       │ REST API + SSE
┌──────────────────────▼───────────────────────────────────┐
│                   FastAPI Backend                         │
│                                                          │
│  /api/users          ── User CRUD                        │
│  /api/users/{id}/documents ── Upload (auto-classify)     │
│  /api/users/{id}/verify    ── Start pipeline             │
│  /api/jobs/{id}/events     ── SSE progress stream        │
│                                                          │
│  ┌─────────────────────────────────────────────────┐     │
│  │            Verification Pipeline                 │     │
│  │  Ingest ► OCR ► Extract ► Verify ► Decision     │     │
│  └─────────────────────────────────────────────────┘     │
│                                                          │
│  SQLite + SQLAlchemy    PaddleOCR / Mock OCR              │
└──────────────────────────────────────────────────────────┘
```

**Stack**: FastAPI, SQLAlchemy, SQLite, PaddleOCR, React 19, Vite 6, Material UI 6

## How It Works

### 1. User Registration

Users are created with their identity details:
- **Name** (English and Arabic)


These fields serve as the ground truth that uploaded documents are verified against.

### 2. Document Upload

Three document types are supported, each uploaded via a dedicated drag-and-drop zone:

| Document | Purpose | Accepted Formats |
|----------|---------|-----------------|
| **Civil ID** | Identity verification | PDF, PNG, JPG |
| **Bank Statement** | Salary & debt analysis | PDF, PNG, JPG |
| **Salary Transfer** | Employment confirmation | PDF, PNG, JPG |

If `doc_type` is not provided during upload, the system auto-classifies the document using keyword matching (e.g., "كشف حساب" → bank statement, "البطاقة المدنية" → civil ID).

### 3. Verification Pipeline

When "Verify Documents" is clicked, the backend runs a 5-phase pipeline with real-time SSE progress:

#### Phase 1 — Ingest (10%)
Loads all uploaded documents for the user from the database.

#### Phase 2 — OCR (30%)
Extracts text from each document:
- **Digital PDFs**: Uses PyMuPDF embedded text extraction (fast, high accuracy)
- **Scanned PDFs/Images**: Falls back to PaddleOCR with Arabic language support
- Text is normalized: Arabic-Indic digits → Western digits, Unicode NFKC, whitespace collapse, diacritics removal

#### Phase 3 — Extract (40%)
Each document type has a specialized extractor that parses structured data from the raw OCR text:

**Civil ID Extractor** — Extracts:
- 12-digit civil ID number (`\b\d{12}\b`)
- English name (from "Name:" label)
- Arabic name (from "اسم" label or contextual lines)

**Bank Statement Extractor** — Two parsing modes:
- **Single-line mode**: For pipe-delimited tables (e.g., `01/07/2025 | SALARY TRANSFER | 1,500.000`)
- **Multi-line mode**: For PyMuPDF cell-per-line extraction where each table cell appears on a separate line (auto-detected when 3+ date-only lines are found)

Supports both `DD/MM/YYYY` and `YYYY/MM/DD` date formats. Classifies each transaction by keywords:
- Salary: "salary", "payroll", "راتب"
- Loan: "loan", "repayment", "installment", "قسط"

**Salary Transfer Extractor** — Extracts:
- Employee name, civil ID, monthly salary amount
- Validates the document is a salary letter by keyword presence

#### Phase 4 — Verify (80%)
Each extracted document is verified against the user's registered data:

**Civil ID Verification**:
- Fuzzy name matching using `token_sort_ratio` (TheFuzz library)
- Matches against both English and Arabic names
- Threshold: 80% similarity (configurable)

**Bank Statement Verification**:
- **Salary Recurrence**: Minimum 3 months of salary deposits required
- **Salary Stability**: All salary amounts must be within 15% of the average
- **Salary Amount Match** (optional): Compared against declared salary
- **Debt Analysis**: Detects loan repayments and calculates debt-to-salary ratio
- **Eligibility**: Passed (salary OK) + debt ratio ≤ 40% → Eligible

**Salary Transfer Verification**:
- Civil ID exact match
- Employee name fuzzy match (80% threshold)
- Salary amount tolerance check

#### Phase 5 — Decision (100%)
Computes the final outcome:
- **PASS**: All documents verified successfully
- **FAIL**: One or more document verifications failed
- **NOT_ELIGIBLE**: Documents verified but debt ratio exceeds 40%

### 4. Results Display

Results show per-document accordions with:
- Pass/Fail/Not Eligible status chips
- Individual check details (expected vs. found values, match scores)
- Actionable error messages, e.g.:
  - *"The name on the Civil ID does not match the registered name"*
  - *"No salary deposits were detected in the bank statement"*
  - *"Monthly debt exceeds 40% of salary (ratio: X%)"*

## Project Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app, routes, startup
│   ├── config.py                # Pydantic settings (.env support)
│   ├── database.py              # SQLAlchemy engine + session
│   ├── seed.py                  # Sample user data
│   ├── api/                     # Route handlers
│   │   ├── users.py             # User CRUD
│   │   ├── documents.py         # Upload + classification
│   │   ├── jobs.py              # Verification jobs + SSE
│   │   └── job_store.py         # In-memory job state for SSE
│   ├── models/                  # SQLAlchemy ORM models
│   ├── schemas/                 # Pydantic request/response schemas
│   ├── services/
│   │   ├── classifier.py        # Keyword-based doc type detection
│   │   ├── pipeline.py          # 5-phase verification orchestrator
│   │   ├── ocr_service.py       # PaddleOCR + Mock OCR abstraction
│   │   ├── normalization.py     # Arabic/Unicode text normalization
│   │   ├── extractors/          # Per-doc-type data extraction
│   │   │   ├── civil_id.py
│   │   │   ├── bank_statement.py
│   │   │   └── salary_transfer.py
│   │   └── verifiers/           # Per-doc-type verification logic
│   │       ├── civil_id.py
│   │       ├── bank_statement.py
│   │       └── salary_transfer.py
│   ├── fixtures/                # Mock OCR text files for testing
│   └── tests/                   # pytest unit tests
├── requirements.txt
├── Dockerfile
└── test_ocr.py                  # Standalone OCR diagnostic tool

frontend/
├── src/
│   ├── App.jsx                  # Two-column layout (users | detail)
│   ├── main.jsx                 # React entry point
│   ├── api/client.js            # Axios client + SSE subscription
│   └── components/
│       ├── UserList.jsx         # User selection + creation dialog
│       ├── UserDetail.jsx       # Documents + verification trigger
│       ├── DocumentUploadDialog.jsx  # 3-card drag-and-drop upload
│       ├── VerificationProgress.jsx  # SSE-powered step progress
│       └── ResultDisplay.jsx    # Per-document results + feedback
├── package.json
├── vite.config.js
└── Dockerfile

doc-test/                        # Test PDFs for development
docker-compose.yml
```

## Configuration

All settings are in `backend/.env` (or environment variables):

| Variable | Default | Description |
|----------|---------|-------------|
| `OCR_PROVIDER` | `paddleocr` | OCR engine (`paddleocr` or `mock`) |
| `OCR_DPI` | `150` | Image resolution for PDF rendering |
| `DATABASE_URL` | `sqlite:///./verifydoc.db` | Database connection string |
| `UPLOAD_DIR` | `./uploads` | File storage directory |
| `NAME_MATCH_THRESHOLD` | `80` | Fuzzy name match minimum (%) |
| `SALARY_RECURRENCE_MIN_MONTHS` | `3` | Minimum months of salary deposits |
| `SALARY_STABILITY_TOLERANCE` | `0.15` | Salary variation tolerance (15%) |
| `DEBT_TO_SALARY_MAX_RATIO` | `0.40` | Maximum debt-to-salary ratio (40%) |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed frontend origins |

## Running Tests

```bash
cd backend
python -m pytest app/tests/ -v
```

### OCR Diagnostic Tool

Test OCR extraction on any document without running the full server:

```bash
cd backend
python test_ocr.py ../doc-test/Example-3.pdf --out output.json
```

This shows: raw OCR text, detected document type, keyword matches, extracted transactions, and salary/loan classification.

## Test Documents

Place test PDFs in `doc-test/`. The system has been tested with:
- **Civil ID cards** (bilingual Arabic/English)
- **KFH bank statements** (YYYY/MM/DD dates, cell-per-line PyMuPDF extraction)
- **KIB bank statements** (DD/MM/YYYY dates, pipe-delimited format)
- **Boubyan bank statements** (bilingual with Arabic descriptions)
- **Salary transfer letters** (English format & Arabic Format)

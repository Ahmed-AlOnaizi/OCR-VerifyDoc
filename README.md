# Document Verification Service

A production-style prototype that accepts uploaded documents (PDFs/images), runs OCR via PaddleOCR, extracts fields, and verifies them against a user database.

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

## Architecture

- **Backend**: FastAPI + SQLAlchemy + SQLite + PaddleOCR
- **Frontend**: React + Vite + Material UI
- **Processing**: Background tasks with SSE progress streaming

## Test Documents

Place test PDFs in `doc-test/` — the system supports:
- Civil ID cards
- Bank statements
- Salary transfer letters

## Running Tests
```bash
cd backend
python -m pytest tests/ -v
```

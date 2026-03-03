import datetime
import json
import logging
import os
import traceback
from dataclasses import asdict

from app.config import settings
from app.database import SessionLocal
from app.models.document import Document, DocType
from app.models.user import User
from app.models.verification_job import VerificationJob, JobStatus
from app.api.job_store import job_store
from app.services.ocr_service import get_ocr_service
from app.services.extractors.civil_id import extract_civil_id
from app.services.extractors.bank_statement import extract_bank_statement
from app.services.extractors.salary_transfer import extract_salary_transfer
from app.services.verifiers.civil_id import verify_civil_id
from app.services.verifiers.bank_statement import verify_bank_statement
from app.services.verifiers.salary_transfer import verify_salary_transfer

logger = logging.getLogger(__name__)


def _update(job_id: int, db, **kwargs):
    """Update both the DB job record and the in-memory job store."""
    job = db.query(VerificationJob).get(job_id)
    if job:
        for k, v in kwargs.items():
            if hasattr(job, k):
                setattr(job, k, v)
        db.commit()

    # Update in-memory store (triggers SSE)
    store_kwargs = {k: v for k, v in kwargs.items() if k in ("status", "phase", "progress", "result", "error")}
    job_store.update_job(job_id, **store_kwargs)


def _save_ocr_output(job_id: int, user_id: int, ocr_results: dict, extracted: dict) -> str:
    """Save raw OCR text and extracted fields to a JSON file. Returns file path."""
    user_dir = os.path.join(settings.UPLOAD_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)

    output = {
        "job_id": job_id,
        "user_id": user_id,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "documents": {},
    }

    for doc_type, raw_text in ocr_results.items():
        doc_entry = {"raw_ocr_text": raw_text}
        if doc_type in extracted:
            doc_entry["extracted_fields"] = asdict(extracted[doc_type])
        output["documents"][doc_type] = doc_entry

    filepath = os.path.join(user_dir, f"ocr_output_job_{job_id}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    logger.info(f"OCR output saved to {filepath}")
    return filepath


def run_verification_pipeline(job_id: int, user_id: int):
    """Main verification pipeline. Runs in a background thread."""
    db = SessionLocal()
    try:
        _run_pipeline(job_id, user_id, db)
    except Exception as e:
        logger.error(f"Pipeline error for job {job_id}: {e}\n{traceback.format_exc()}")
        _update(job_id, db,
                 status=JobStatus.FAILED,
                 phase="error",
                 progress=0.0,
                 error=str(e))
    finally:
        db.close()


def _run_pipeline(job_id: int, user_id: int, db):
    """Execute the pipeline phases. Civil ID is processed first; early exit on name mismatch."""
    _update(job_id, db, status=JobStatus.RUNNING, phase="ingest", progress=0.0)

    # --- Phase 1: Ingest ---
    user = db.query(User).get(user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")

    documents = db.query(Document).filter(Document.user_id == user_id).all()
    if not documents:
        raise ValueError(f"No documents uploaded for user {user_id}")

    doc_map: dict[DocType, Document] = {}
    for doc in documents:
        doc_map[doc.doc_type] = doc  # latest per type

    _update(job_id, db, phase="ingest", progress=10.0)

    # --- Phase 2: OCR + Extract + Verify civil ID first (early exit) ---
    ocr = get_ocr_service()
    ocr_results: dict[str, str] = {}
    extracted: dict[str, object] = {}
    verifications: dict[str, dict] = {}

    if DocType.CIVIL_ID not in doc_map:
        raise ValueError("Civil ID document is required")

    # OCR civil ID
    _update(job_id, db, phase="ocr", progress=15.0)
    cid_doc = doc_map[DocType.CIVIL_ID]
    ocr_results[DocType.CIVIL_ID.value] = ocr.extract_text(cid_doc.filepath)
    _update(job_id, db, phase="ocr", progress=25.0)

    # Extract civil ID
    _update(job_id, db, phase="extract", progress=30.0)
    cid_extracted = extract_civil_id(ocr_results[DocType.CIVIL_ID.value])
    extracted[DocType.CIVIL_ID.value] = cid_extracted

    # Verify civil ID (name-only)
    _update(job_id, db, phase="verify", progress=35.0)
    cid_verification = verify_civil_id(
        cid_extracted,
        expected_name=user.name,
    )
    verifications["civil_id"] = {
        "passed": cid_verification.passed,
        "checks": cid_verification.checks,
        "errors": cid_verification.errors,
    }

    _update(job_id, db, phase="verify", progress=40.0)

    # Early exit if name doesn't match
    if not cid_verification.passed:
        ocr_output_file = _save_ocr_output(job_id, user_id, ocr_results, extracted)

        all_errors = [f"[civil_id] {err}" for err in cid_verification.errors]
        result = {
            "decision": "FAIL",
            "early_exit": True,
            "early_exit_reason": "Civil ID name verification failed",
            "documents_verified": 1,
            "verifications": verifications,
            "errors": all_errors,
            "ocr_output_file": ocr_output_file,
        }

        _update(job_id, db,
                 status=JobStatus.COMPLETED,
                 phase="decision",
                 progress=100.0,
                 result=result)

        job = db.query(VerificationJob).get(job_id)
        if job:
            job.completed_at = datetime.datetime.utcnow()
            db.commit()
        return

    # --- Phase 3: OCR remaining documents ---
    remaining_types = [dt for dt in doc_map if dt != DocType.CIVIL_ID]
    total_remaining = len(remaining_types)

    for i, doc_type in enumerate(remaining_types):
        doc = doc_map[doc_type]
        ocr_results[doc_type.value] = ocr.extract_text(doc.filepath)
        progress = 40.0 + (20.0 * (i + 1) / max(total_remaining, 1))
        _update(job_id, db, phase="ocr", progress=progress)

    # --- Phase 4: Extract remaining documents ---
    _update(job_id, db, phase="extract", progress=60.0)

    if DocType.BANK_STATEMENT.value in ocr_results:
        extracted["bank_statement"] = extract_bank_statement(ocr_results[DocType.BANK_STATEMENT.value])

    if DocType.SALARY_TRANSFER.value in ocr_results:
        extracted["salary_transfer"] = extract_salary_transfer(ocr_results[DocType.SALARY_TRANSFER.value])

    _update(job_id, db, phase="extract", progress=70.0)

    # --- Phase 5: Verify remaining documents ---
    _update(job_id, db, phase="verify", progress=70.0)

    if "bank_statement" in extracted:
        v = verify_bank_statement(
            extracted["bank_statement"],
        )
        verifications["bank_statement"] = {
            "passed": v.passed,
            "salary_months_found": v.salary_months_found,
            "average_salary": v.average_salary,
            "has_loans": v.has_loans,
            "loan_count": v.loan_count,
            "checks": v.checks,
            "errors": v.errors,
        }

    if "salary_transfer" in extracted:
        v = verify_salary_transfer(
            extracted["salary_transfer"],
            expected_name=user.name,
        )
        verifications["salary_transfer"] = {
            "passed": v.passed,
            "checks": v.checks,
            "errors": v.errors,
        }

    _update(job_id, db, phase="verify", progress=80.0)

    # --- Phase 6: Decision ---
    _update(job_id, db, phase="decision", progress=80.0)

    # Save OCR output
    ocr_output_file = _save_ocr_output(job_id, user_id, ocr_results, extracted)

    all_passed = all(v["passed"] for v in verifications.values())
    all_errors = []
    for doc_type, v in verifications.items():
        for err in v.get("errors", []):
            all_errors.append(f"[{doc_type}] {err}")

    result = {
        "decision": "PASS" if all_passed else "FAIL",
        "documents_verified": len(verifications),
        "verifications": verifications,
        "errors": all_errors,
        "ocr_output_file": ocr_output_file,
    }

    _update(job_id, db,
             status=JobStatus.COMPLETED,
             phase="decision",
             progress=100.0,
             result=result)

    # Update completed_at
    job = db.query(VerificationJob).get(job_id)
    if job:
        job.completed_at = datetime.datetime.utcnow()
        db.commit()

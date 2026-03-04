import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.document import Document, DocType
from app.schemas.document import DocumentResponse
from app.services.ocr_service import get_ocr_service
from app.services.classifier import classify_document

router = APIRouter(tags=["documents"])


@router.get("/users/{user_id}/documents", response_model=list[DocumentResponse])
def list_documents(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return db.query(Document).filter(Document.user_id == user_id).all()


@router.post("/users/{user_id}/documents", response_model=DocumentResponse, status_code=201)
async def upload_document(
    user_id: int,
    file: UploadFile = File(...),
    doc_type: str | None = Form(None),
    db: Session = Depends(get_db),
):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Save file first (needed for OCR if auto-detecting)
    user_dir = os.path.join(settings.UPLOAD_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    ext = os.path.splitext(file.filename or "file")[1]
    saved_name = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(user_dir, saved_name)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    if doc_type:
        # Explicit type provided — validate
        try:
            dtype = DocType(doc_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid doc_type. Must be one of: {[e.value for e in DocType]}")
    else:
        # Auto-detect via OCR
        ocr = get_ocr_service()
        ocr_text = ocr.extract_text(filepath)
        detected = classify_document(ocr_text)
        if detected is None:
            os.remove(filepath)
            raise HTTPException(status_code=422, detail="Could not determine document type from content")
        dtype = detected

    doc = Document(
        user_id=user_id,
        doc_type=dtype,
        filename=file.filename or "unknown",
        filepath=filepath,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

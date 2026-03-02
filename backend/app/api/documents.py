import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.document import Document, DocType
from app.schemas.document import DocumentResponse

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
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        dtype = DocType(doc_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid doc_type. Must be one of: {[e.value for e in DocType]}")

    # Save file
    user_dir = os.path.join(settings.UPLOAD_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    ext = os.path.splitext(file.filename or "file")[1]
    saved_name = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(user_dir, saved_name)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

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

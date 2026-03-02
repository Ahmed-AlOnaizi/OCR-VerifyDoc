from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.verification_job import VerificationJob
from app.schemas.user import UserCreate, UserResponse
from app.schemas.job import JobResponse

router = APIRouter(tags=["users"])


@router.get("/users", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()


@router.post("/users", response_model=UserResponse, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.civil_id == payload.civil_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="User with this civil ID already exists")
    user = User(**payload.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/users/{user_id}/verification-latest", response_model=JobResponse | None)
def get_latest_verification(user_id: int, db: Session = Depends(get_db)):
    job = (
        db.query(VerificationJob)
        .filter(VerificationJob.user_id == user_id)
        .order_by(VerificationJob.created_at.desc())
        .first()
    )
    return job

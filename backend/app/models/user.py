import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    civil_id: Mapped[str] = mapped_column(String(12), unique=True, index=True)
    name_en: Mapped[str] = mapped_column(String(200))
    name_ar: Mapped[str] = mapped_column(String(200), default="")
    employer: Mapped[str] = mapped_column(String(200), default="")
    salary: Mapped[float] = mapped_column(default=0.0)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    verification_jobs = relationship("VerificationJob", back_populates="user", cascade="all, delete-orphan")

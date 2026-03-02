import datetime
import enum

from sqlalchemy import String, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DocType(str, enum.Enum):
    CIVIL_ID = "civil_id"
    BANK_STATEMENT = "bank_statement"
    SALARY_TRANSFER = "salary_transfer"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    doc_type: Mapped[DocType] = mapped_column(Enum(DocType))
    filename: Mapped[str] = mapped_column(String(500))
    filepath: Mapped[str] = mapped_column(String(1000))
    uploaded_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    user = relationship("User", back_populates="documents")

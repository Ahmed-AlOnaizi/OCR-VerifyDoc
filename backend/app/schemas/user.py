import datetime

from pydantic import BaseModel


class UserCreate(BaseModel):
    civil_id: str
    name_en: str
    name_ar: str = ""
    employer: str = ""
    salary: float = 0.0


class UserResponse(BaseModel):
    id: int
    civil_id: str
    name_en: str
    name_ar: str
    employer: str
    salary: float
    created_at: datetime.datetime

    model_config = {"from_attributes": True}

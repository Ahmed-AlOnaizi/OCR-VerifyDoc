import datetime

from pydantic import BaseModel


class UserCreate(BaseModel):
    name: str
    phone: str = ""
    email: str = ""


class UserResponse(BaseModel):
    id: int
    name: str
    phone: str
    email: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}

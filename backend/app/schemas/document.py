import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    user_id: int
    doc_type: str
    filename: str
    uploaded_at: datetime.datetime

    model_config = {"from_attributes": True}

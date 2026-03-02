import datetime
from typing import Any

from pydantic import BaseModel


class JobResponse(BaseModel):
    id: int
    user_id: int
    status: str
    phase: str
    progress: float
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime.datetime
    completed_at: datetime.datetime | None = None

    model_config = {"from_attributes": True}


class JobEvent(BaseModel):
    job_id: int
    status: str
    phase: str
    progress: float
    result: dict[str, Any] | None = None
    error: str | None = None

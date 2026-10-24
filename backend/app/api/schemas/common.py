from pydantic import BaseModel
from typing import Optional


class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    database: str
    vector_db: str
    llm_provider: str
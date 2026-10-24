from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ConversationBase(BaseModel):
    title: str = Field(default='', max_length=500)


class ConversationCreate(ConversationBase):
    pass


class ConversationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)


class ConversationResponse(ConversationBase):
    id: int
    created_at: datetime
    updated_at: datetime
    session_id: Optional[int] = None
    message_count: int = 0

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    conversations: List[ConversationResponse]
    total: int
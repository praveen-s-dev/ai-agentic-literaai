from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.api.dependencies import get_db
from app.api.schemas.conversation import ConversationCreate, ConversationUpdate, ConversationResponse, ConversationListResponse
from database.models import ResearchSession

router = APIRouter(prefix="/conversations", tags=["conversations"])

@router.get("", response_model=ConversationListResponse)
def list_conversations(db: Session = Depends(get_db)):
    sessions = db.query(ResearchSession).order_by(ResearchSession.updated_at.desc()).all()
    conversations = []
    for rs in sessions:
        msg_count = len(rs.analyses) + len(rs.evidence_records)
        conversations.append(ConversationResponse(
            id=rs.id,
            title=rs.research_question or f"Session {rs.id}",
            created_at=rs.created_at,
            updated_at=rs.updated_at,
            session_id=rs.id,
            message_count=msg_count
        ))
    return ConversationListResponse(conversations=conversations, total=len(conversations))

@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(data: ConversationCreate, db: Session = Depends(get_db)):
    rs = ResearchSession(research_question=data.title, status="created")
    db.add(rs)
    db.commit()
    db.refresh(rs)
    return ConversationResponse(
        id=rs.id,
        title=rs.research_question,
        created_at=rs.created_at,
        updated_at=rs.updated_at,
        session_id=rs.id,
        message_count=0
    )

@router.get("/{conv_id}", response_model=ConversationResponse)
def get_conversation(conv_id: int, db: Session = Depends(get_db)):
    rs = db.query(ResearchSession).filter(ResearchSession.id == conv_id).first()
    if not rs:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationResponse(
        id=rs.id,
        title=rs.research_question or f"Session {rs.id}",
        created_at=rs.created_at,
        updated_at=rs.updated_at,
        session_id=rs.id,
        message_count=0
    )

@router.put("/{conv_id}", response_model=ConversationResponse)
def update_conversation(conv_id: int, data: ConversationUpdate, db: Session = Depends(get_db)):
    rs = db.query(ResearchSession).filter(ResearchSession.id == conv_id).first()
    if not rs:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if data.title is not None:
        rs.research_question = data.title
    rs.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(rs)
    return ConversationResponse(
        id=rs.id,
        title=rs.research_question,
        created_at=rs.created_at,
        updated_at=rs.updated_at,
        session_id=rs.id,
        message_count=0
    )

@router.delete("/{conv_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(conv_id: int, db: Session = Depends(get_db)):
    rs = db.query(ResearchSession).filter(ResearchSession.id == conv_id).first()
    if not rs:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(rs)
    db.commit()
    return None
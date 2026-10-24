from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.api.schemas.common import ErrorResponse
from rag.rag_pipeline import RAGPipeline
from rag.retriever import Retriever
from app.config import settings

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None
    paper_ids: Optional[List[int]] = None
    use_rag: bool = True
    temperature: Optional[float] = None


class ChatResponse(BaseModel):
    response: str
    evidence: List[dict] = []
    conversation_id: Optional[int] = None


class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: str


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Chat with the AI assistant, optionally using RAG for evidence-grounded responses."""
    try:
        # Initialize RAG pipeline
        rag = RAGPipeline()
        
        # Set temperature if provided
        if request.temperature is not None:
            rag.temperature = request.temperature
        
        if request.use_rag and request.paper_ids:
            # Use RAG with specific papers
            result = rag.answer_question(
                question=request.message,
                paper_ids=request.paper_ids,
                top_k=5,
            )
            return ChatResponse(
                response=result.get("answer", ""),
                evidence=result.get("evidence", []),
                conversation_id=request.conversation_id,
            )
        elif request.use_rag:
            # Use RAG with all available papers in conversation
            if request.conversation_id:
                from database.models import Paper
                papers = db.query(Paper).filter(Paper.session_id == request.conversation_id).all()
                paper_ids = [p.id for p in papers]
                if paper_ids:
                    result = rag.answer_question(
                        question=request.message,
                        paper_ids=paper_ids,
                        top_k=5,
                    )
                    return ChatResponse(
                        response=result.get("answer", ""),
                        evidence=result.get("evidence", []),
                        conversation_id=request.conversation_id,
                    )
            
            # Fallback: general chat without RAG
            return await _general_chat(rag, request.message, request.conversation_id)
        else:
            # Pure LLM chat without RAG
            return await _general_chat(rag, request.message, request.conversation_id)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


async def _general_chat(rag: RAGPipeline, message: str, conversation_id: Optional[int]) -> ChatResponse:
    """General chat without RAG - direct LLM call."""
    try:
        # Simple chat prompt
        prompt = f"""You are a helpful AI research assistant. Answer the user's question directly and concisely.

USER: {message}

ASSISTANT:"""
        
        if hasattr(rag, 'provider') and rag.provider == "nvidia":
            response = rag.client.chat.completions.create(
                model=rag.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful AI research assistant."},
                    {"role": "user", "content": message},
                ],
                temperature=rag.temperature or 0.7,
                top_p=0.9,
                max_tokens=1024,
            )
            answer = response.choices[0].message.content or ""
        else:
            response = rag.client.generate(
                model=rag.model_name,
                prompt=f"You are a helpful AI research assistant.\n\nUSER: {message}\n\nASSISTANT:",
                options={
                    "temperature": rag.temperature or 0.7,
                    "top_p": 0.9,
                    "num_predict": 1024,
                },
            )
            answer = response.get("response", "")
        
        return ChatResponse(
            response=answer.strip(),
            evidence=[],
            conversation_id=conversation_id,
        )
    except Exception as e:
        return ChatResponse(
            response=f"Error: {str(e)}",
            evidence=[],
            conversation_id=conversation_id,
        )
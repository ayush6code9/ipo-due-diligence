"""
DRHP Chat endpoint (Phase 9A).

POST /api/drhp/{document_id}/chat — ask a question, get an evidence-backed answer
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services import chat_service
from app.services.chat_service import ChatError

router = APIRouter()


@router.post("/drhp/{document_id}/chat", response_model=ChatResponse)
def chat_with_drhp(document_id: int, body: ChatRequest, db: Session = Depends(get_db)):
    """Ask a question about a DRHP document and get an evidence-backed answer."""
    try:
        result = chat_service.chat_with_document(
            db, document_id, body.question, body.top_k
        )
    except ChatError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected error during chat. ({exc})")
    return result

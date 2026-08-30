"""
Pydantic schemas for DRHP chat / RAG (Phase 9A).
"""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Request body for POST /api/drhp/{document_id}/chat."""
    question: str
    top_k: int | None = None  # how many evidence chunks to retrieve


class ChatSource(BaseModel):
    """Source reference for a chat answer."""
    page_start: int | None = None
    page_end: int | None = None
    section: str | None = None


class ChatResponse(BaseModel):
    """Response for POST /api/drhp/{document_id}/chat."""
    document_id: int
    question: str
    answer: str
    sources: list[ChatSource] = []
    llm_used: bool = False

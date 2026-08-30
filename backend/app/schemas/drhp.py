"""
Pydantic schemas for the DRHP upload/extraction endpoints (Phase 4).
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PageExtraction(BaseModel):
    """Extracted text for a single PDF page (1-based page numbering)."""

    page_number: int
    text: str


class DRHPUploadResponse(BaseModel):
    """Full response returned right after upload + extraction."""

    document_id: int
    original_filename: str
    stored_filename: str
    file_size: int
    page_count: int
    extracted_pages: int
    pages_with_little_text: list[int]
    status: str
    pages: list[PageExtraction]


class DRHPDocumentOut(BaseModel):
    """Lightweight metadata shape for GET /api/drhp/{document_id} —
    deliberately excludes page text so this stays a small response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    file_size: int
    page_count: int | None = None
    extracted_pages: int | None = None
    pages_with_little_text: list[int] = []
    extraction_status: str
    uploaded_at: datetime
    source_url: str | None = None
    source_name: str | None = None


class DRHPPageOut(BaseModel):
    """Response shape for GET /api/drhp/{document_id}/pages/{page_number}."""

    document_id: int
    page_number: int
    text: str


class IndexResponse(BaseModel):
    """Response returned right after POST /api/drhp/{document_id}/index."""

    document_id: int
    status: str
    page_count: int
    chunk_count: int
    embedding_model: str
    vector_store: str


class IndexStatusResponse(BaseModel):
    """Response shape for GET /api/drhp/{document_id}/index/status."""

    document_id: int
    indexing_status: str
    chunk_count: int | None = None
    indexed_at: datetime | None = None
    error: str | None = None


class SearchRequest(BaseModel):
    """Request body for POST /api/drhp/{document_id}/search.

    query has no min_length here deliberately — emptiness is validated in
    the service layer so the API can return the spec'd 400 with a clear
    message, rather than FastAPI's automatic 422.
    """

    query: str
    top_k: int | None = None


class SearchResultItem(BaseModel):
    """One retrieved chunk with its source evidence — page range and
    section are what let a later LLM phase cite where an answer came from."""

    chunk_id: str
    similarity_score: float
    page_start: int
    page_end: int
    section: str | None = None
    text: str


class SearchResponse(BaseModel):
    """Response shape for POST /api/drhp/{document_id}/search."""

    document_id: int
    query: str
    status: str  # "success" | "no_relevant_results"
    result_count: int
    results: list[SearchResultItem]

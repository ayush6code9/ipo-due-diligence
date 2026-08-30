"""
Pydantic schemas for the live IPO search endpoints.
"""

from pydantic import BaseModel


class IPOSearchResult(BaseModel):
    """A single IPO search result from an external source."""

    company_name: str
    ipo_name: str | None = None
    status: str | None = None  # "Open" | "Upcoming" | "Closed" | "Listed"
    document_type: str | None = None  # "DRHP" | "RHP" | "Addendum"
    filing_date: str | None = None
    source_name: str  # "Chittorgarh" | "SEBI" | etc.
    source_url: str | None = None
    document_url: str | None = None  # Direct PDF link
    is_document_available: bool = False
    sector: str | None = None
    issue_size: str | None = None
    price_band: str | None = None


class IPOSearchResponse(BaseModel):
    """Response for GET /api/ipo/search."""

    query: str
    result_count: int
    results: list[IPOSearchResult]
    source: str
    cached: bool = False


class IPODocumentFetchRequest(BaseModel):
    """Request body for POST /api/ipo/fetch-document."""

    document_url: str
    company_name: str
    source_name: str = "External"
    document_type: str | None = "DRHP"  # "DRHP" or "RHP"


class IPODocumentFetchResponse(BaseModel):
    """Response for POST /api/ipo/fetch-document — same essential shape as
    DRHPUploadResponse so the frontend Analyzing page can handle both."""

    document_id: int
    original_filename: str
    file_size: int
    page_count: int
    extracted_pages: int
    pages_with_little_text: list[int] = []
    status: str
    source_url: str | None = None
    source_name: str | None = None
    document_type: str | None = "DRHP"

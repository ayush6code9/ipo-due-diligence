"""
Live IPO search and document retrieval router (Phases 3 & 5).

GET  /api/ipo/search         — search for current/upcoming/recent Indian IPOs
POST /api/ipo/fetch-document — retrieve official DRHP/RHP from external source
                               and ingest into the document pipeline
"""

import json
import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.paths import resolve_project_path
from app.db.database import get_db
from app.db.models import DRHPDocument
from app.schemas.ipo_search import (
    IPODocumentFetchRequest,
    IPODocumentFetchResponse,
    IPOSearchResponse,
)
from app.services import ipo_search_service
from app.services.drhp_service import (
    DRHPProcessingError,
    _determine_status,
    _validate_is_pdf_and_open,
    extract_pages,
)

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


@router.get("/ipo/search", response_model=IPOSearchResponse)
def search_live_ipos(
    q: str = Query(
        ...,
        min_length=1,
        max_length=200,
        description="Company or IPO name to search for",
    ),
    db: Session = Depends(get_db),
):
    """Search for current, upcoming, or recently filed Indian IPOs.

    Queries authoritative sources (Chittorgarh / SEBI) and caches results in SQLite.
    Returns structured results including document availability and direct PDF URLs
    when present in official filings.
    """
    clean_query = q.strip()
    if not clean_query:
        raise HTTPException(
            status_code=422,
            detail="Search query cannot be empty or just whitespace.",
        )

    try:
        results, cached = ipo_search_service.search_ipos(db, clean_query)
    except Exception as exc:
        logger.exception("IPO search failed for query: %s", clean_query)
        raise HTTPException(
            status_code=502,
            detail="Live IPO search is temporarily unavailable. You can upload the DRHP manually to continue.",
        )

    source = results[0].source_name if results else "None"

    return IPOSearchResponse(
        query=clean_query,
        result_count=len(results),
        results=results,
        source=source,
        cached=cached,
    )


@router.post("/ipo/fetch-document", response_model=IPODocumentFetchResponse)
def fetch_ipo_document(
    body: IPODocumentFetchRequest,
    db: Session = Depends(get_db),
):
    """Download an official DRHP or RHP document from a verified external source
    and ingest it into the existing document processing pipeline.

    This creates a standard DRHPDocument record with source provenance, allowing
    indexing, structured extraction, financial analysis, RAG chat, and report
    generation to operate identically to manual uploads.
    """
    doc_url = body.document_url.strip() if body.document_url else ""
    if not doc_url:
        raise HTTPException(
            status_code=400,
            detail="No document URL was provided. You can upload the DRHP manually to continue.",
        )

    if not doc_url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=400,
            detail="Invalid document URL. Only HTTP and HTTPS URLs are supported. You can upload the DRHP manually to continue.",
        )

    # 1. Download document with validation
    try:
        content, derived_filename = ipo_search_service.download_document(doc_url)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"{exc} You can upload the DRHP manually to continue.",
        )
    except Exception as exc:
        logger.exception("Failed to download document from: %s", doc_url)
        raise HTTPException(
            status_code=502,
            detail="The document could not be retrieved from the external source. You can upload the DRHP manually to continue.",
        )

    # 2. Derive user-friendly display filename
    doc_type_label = (body.document_type or "DRHP").upper()
    safe_company = "".join(c for c in body.company_name if c.isalnum() or c in (" ", "-", "_")).strip()
    safe_company = safe_company[:60] if safe_company else "IPO"
    original_filename = f"{safe_company}_{doc_type_label}.pdf"

    # 3. Store file safely in uploads directory
    upload_dir = resolve_project_path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_filename = f"{uuid.uuid4().hex}.pdf"
    stored_path = upload_dir / stored_filename

    try:
        stored_path.write_bytes(content)
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not save the retrieved document. ({exc})",
        )

    # 4. Open with PyMuPDF and extract text using the existing pipeline logic
    try:
        doc = _validate_is_pdf_and_open(stored_path)
        try:
            pages, little_text_pages = extract_pages(doc)
        finally:
            doc.close()
    except DRHPProcessingError as exc:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=exc.status_code,
            detail=f"{exc.message} You can upload the DRHP manually.",
        )
    except Exception as exc:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error while processing the retrieved document. ({exc})",
        )

    page_count = len(pages)
    extracted_pages = page_count - len(little_text_pages)
    status = _determine_status(page_count, little_text_pages)

    # 5. Persist DRHPDocument record in database
    document = DRHPDocument(
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_size=len(content),
        page_count=page_count,
        extracted_pages=extracted_pages,
        pages_with_little_text=json.dumps(little_text_pages),
        extraction_status=status,
        source_url=doc_url,
        source_name=body.source_name or "External",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    logger.info(
        "Successfully fetched and ingested document %s (id=%d, pages=%d, source=%s)",
        original_filename,
        document.id,
        page_count,
        document.source_name,
    )

    return IPODocumentFetchResponse(
        document_id=document.id,
        original_filename=original_filename,
        file_size=len(content),
        page_count=page_count,
        extracted_pages=extracted_pages,
        pages_with_little_text=little_text_pages,
        status=status,
        source_url=doc_url,
        source_name=document.source_name,
        document_type=doc_type_label,
    )

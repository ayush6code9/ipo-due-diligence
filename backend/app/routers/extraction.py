"""
Structured DRHP extraction endpoints (Phase 7A).

POST /api/drhp/{document_id}/extract   — run the extraction pipeline
GET  /api/drhp/{document_id}/extraction — get cached extraction results
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.extraction import ExtractionResponse, ExtractionStatusResponse
from app.services import drhp_service, extraction_service
from app.services.extraction_service import ExtractionError

router = APIRouter()


@router.post("/drhp/{document_id}/extract", response_model=ExtractionResponse)
def extract_drhp_document(document_id: int, db: Session = Depends(get_db)):
    """Run the full structured extraction pipeline for an indexed DRHP."""
    try:
        result = extraction_service.extract_document(db, document_id)
    except ExtractionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected error during extraction. ({exc})")
    return ExtractionResponse(
        document_id=document_id,
        status=result.status,
        extraction=result,
    )


@router.get("/drhp/{document_id}/extraction", response_model=ExtractionStatusResponse)
def get_drhp_extraction(document_id: int, db: Session = Depends(get_db)):
    """Get cached extraction results (if available)."""
    document = drhp_service.get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail=f"No document found with id {document_id}.")

    extraction = extraction_service.get_extraction(db, document_id)
    return ExtractionStatusResponse(
        document_id=document_id,
        extraction_status=document.extraction_status,
        extraction=extraction,
    )

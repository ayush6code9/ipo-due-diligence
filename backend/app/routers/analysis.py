"""
Analysis endpoints (Phase 7B).

POST /api/drhp/{document_id}/analyze   — run the analysis pipeline
GET  /api/drhp/{document_id}/analysis  — get cached analysis results
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.analysis import AnalysisResponse, AnalysisStatusResponse
from app.services import analysis_service, drhp_service
from app.services.analysis_service import AnalysisError

router = APIRouter()


@router.post("/drhp/{document_id}/analyze", response_model=AnalysisResponse)
def analyze_drhp_document(document_id: int, db: Session = Depends(get_db)):
    """Run the full analysis pipeline for an extracted DRHP."""
    try:
        result = analysis_service.analyze_document(db, document_id)
    except AnalysisError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected error during analysis. ({exc})")
    return AnalysisResponse(
        document_id=document_id,
        status=result.status,
        analysis=result,
    )


@router.get("/drhp/{document_id}/analysis", response_model=AnalysisStatusResponse)
def get_drhp_analysis(document_id: int, db: Session = Depends(get_db)):
    """Get cached analysis results (if available)."""
    document = drhp_service.get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail=f"No document found with id {document_id}.")

    analysis = analysis_service.get_analysis(db, document_id)
    return AnalysisStatusResponse(
        document_id=document_id,
        analysis_status=document.analysis_status,
        analysis=analysis,
    )

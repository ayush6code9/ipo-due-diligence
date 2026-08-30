"""
Report generation endpoint (Phase 10).

GET /api/drhp/{document_id}/report — download an HTML IPO research report
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services import report_service
from app.services.report_service import ReportError

router = APIRouter()


@router.get("/drhp/{document_id}/report")
def download_report(document_id: int, db: Session = Depends(get_db)):
    """Generate and download an IPO research report as HTML."""
    try:
        html = report_service.generate_report_html(db, document_id)
    except ReportError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected error generating report. ({exc})")

    return HTMLResponse(
        content=html,
        headers={
            "Content-Disposition": f"attachment; filename=ipo_report_{document_id}.html",
        },
    )

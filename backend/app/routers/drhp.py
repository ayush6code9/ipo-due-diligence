"""
DRHP upload + extraction + indexing + retrieval endpoints.

POST /api/drhp/upload                            - upload a PDF, get full extraction
GET  /api/drhp/{document_id}                      - document metadata only
GET  /api/drhp/{document_id}/pages/{page_number}  - one page's text, re-extracted on demand
POST /api/drhp/{document_id}/index                - chunk + embed + build FAISS index (Phase 5)
GET  /api/drhp/{document_id}/index/status          - indexing status
POST /api/drhp/{document_id}/search                - semantic evidence retrieval (Phase 6)

Note: /upload is a fixed path segment declared before /{document_id}, so
there's no ambiguity between the two at the router level. /index and
/search sub-paths are distinct path templates (extra segment) so they
don't collide with /{document_id} or /pages/{page_number} either.
"""

import json

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.drhp import (
    DRHPDocumentOut,
    DRHPPageOut,
    DRHPUploadResponse,
    IndexResponse,
    IndexStatusResponse,
    SearchRequest,
    SearchResponse,
)
from app.services import drhp_service, retrieval_service, vector_service
from app.services.drhp_service import DRHPProcessingError
from app.services.retrieval_service import RetrievalError
from app.services.vector_service import VectorIndexError

router = APIRouter()


@router.post("/drhp/upload", response_model=DRHPUploadResponse)
async def upload_drhp(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        result = await drhp_service.process_upload(db, file)
    except DRHPProcessingError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected error during upload. ({exc})")
    return result


@router.get("/drhp/{document_id}", response_model=DRHPDocumentOut)
def get_drhp_document(document_id: int, db: Session = Depends(get_db)):
    document = drhp_service.get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail=f"No document found with id {document_id}.")

    return DRHPDocumentOut(
        id=document.id,
        original_filename=document.original_filename,
        file_size=document.file_size,
        page_count=document.page_count,
        extracted_pages=document.extracted_pages,
        pages_with_little_text=json.loads(document.pages_with_little_text or "[]"),
        extraction_status=document.extraction_status,
        uploaded_at=document.uploaded_at,
        source_url=document.source_url,
        source_name=document.source_name,
    )


@router.get("/drhp/{document_id}/pages/{page_number}", response_model=DRHPPageOut)
def get_drhp_page(document_id: int, page_number: int, db: Session = Depends(get_db)):
    try:
        text = drhp_service.get_page_text(db, document_id, page_number)
    except DRHPProcessingError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)

    return DRHPPageOut(document_id=document_id, page_number=page_number, text=text)


@router.post("/drhp/{document_id}/index", response_model=IndexResponse)
def index_drhp_document(document_id: int, db: Session = Depends(get_db)):
    try:
        result = vector_service.index_document(db, document_id)
    except VectorIndexError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected error during indexing. ({exc})")
    return result


@router.get("/drhp/{document_id}/index/status", response_model=IndexStatusResponse)
def get_drhp_index_status(document_id: int, db: Session = Depends(get_db)):
    try:
        result = vector_service.get_index_status(db, document_id)
    except VectorIndexError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    return result


@router.post("/drhp/{document_id}/search", response_model=SearchResponse)
def search_drhp_document(document_id: int, body: SearchRequest, db: Session = Depends(get_db)):
    try:
        result = retrieval_service.search_document(db, document_id, body.query, body.top_k)
    except RetrievalError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected error during search. ({exc})")
    return result

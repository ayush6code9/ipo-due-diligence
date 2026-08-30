"""
DRHP upload + text extraction service.

Pipeline (per Phase 4 spec):
    validate upload -> save PDF to data/uploads -> open with PyMuPDF ->
    page-aware text extraction -> basic cleaning -> structured result

Explicitly NOT implemented here: chunking, embeddings, FAISS, RAG, LLM
calls, financial/risk/promoter analysis. Those are later phases.
"""

import json
import re
import uuid
from pathlib import Path

import fitz  # PyMuPDF
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.paths import resolve_project_path
from app.db.models import DRHPDocument

settings = get_settings()

MAX_UPLOAD_BYTES = settings.max_upload_size_mb * 1024 * 1024

# A page with fewer than this many characters of extracted text is treated
# as "little/no text" — typically a scanned/image-only page. This phase
# reports such pages rather than attempting OCR.
MIN_CHARS_FOR_READABLE_PAGE = 20


class DRHPProcessingError(Exception):
    """Raised for any expected validation/processing failure. The router
    maps `status_code` directly onto the HTTP response."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _uploads_dir() -> Path:
    directory = resolve_project_path(settings.upload_dir)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _safe_stored_filename(original_filename: str) -> str:
    """A random filename with no relation to the user-supplied name, so
    there's nothing to path-traverse or collide with. The .pdf extension is
    kept only for readability when browsing the uploads folder."""
    return f"{uuid.uuid4().hex}.pdf"


def clean_text(raw: str) -> str:
    """Safe, conservative cleanup — not a rewrite. Keeps numbers, headings,
    and paragraph breaks intact."""
    # Normalize Windows/Mac line endings to \n
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    # Strip trailing whitespace on each line, collapse runs of spaces/tabs
    lines = [re.sub(r"[ \t]+", " ", line).rstrip() for line in text.split("\n")]
    text = "\n".join(lines)
    # Collapse 3+ consecutive blank lines down to a single blank line
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _validate_is_pdf_and_open(file_path: Path) -> fitz.Document:
    """The authoritative PDF check: try to actually open it with PyMuPDF.
    Content-type headers and extensions can lie; this can't."""
    try:
        doc = fitz.open(file_path)
    except Exception as exc:  # PyMuPDF raises various error types for bad files
        raise DRHPProcessingError(
            f"The uploaded file could not be opened as a PDF. It may be corrupted. ({exc})",
            status_code=400,
        )
    if doc.is_encrypted:
        doc.close()
        raise DRHPProcessingError(
            "This PDF is password-protected and can't be read.", status_code=400
        )
    if doc.page_count == 0:
        doc.close()
        raise DRHPProcessingError("This PDF has no pages.", status_code=400)
    return doc


def extract_pages(doc: fitz.Document) -> tuple[list[dict], list[int]]:
    """Returns (pages, pages_with_little_text) where pages is a list of
    {"page_number": 1-based int, "text": cleaned str}."""
    pages = []
    little_text_pages = []

    for index in range(doc.page_count):
        page_number = index + 1
        raw_text = doc[index].get_text()
        cleaned = clean_text(raw_text)
        if len(cleaned) < MIN_CHARS_FOR_READABLE_PAGE:
            little_text_pages.append(page_number)
        pages.append({"page_number": page_number, "text": cleaned})

    return pages, little_text_pages


def _determine_status(page_count: int, little_text_pages: list[int]) -> str:
    if not little_text_pages:
        return "success"
    if len(little_text_pages) >= page_count:
        return "no_extractable_text"
    return "partial"


async def process_upload(db: Session, upload_file: UploadFile) -> dict:
    """Validate, store, and extract text from an uploaded DRHP PDF.
    Returns a dict matching DRHPUploadResponse. Raises DRHPProcessingError
    for any expected failure."""

    if upload_file is None or not upload_file.filename:
        raise DRHPProcessingError("No file was uploaded.", status_code=400)

    if not upload_file.filename.lower().endswith(".pdf"):
        raise DRHPProcessingError("Only PDF files are accepted.", status_code=400)

    contents = await upload_file.read()

    if len(contents) == 0:
        raise DRHPProcessingError("The uploaded file is empty.", status_code=400)

    if len(contents) > MAX_UPLOAD_BYTES:
        raise DRHPProcessingError(
            f"File is too large. The limit is {settings.max_upload_size_mb} MB.",
            status_code=400,
        )

    stored_filename = _safe_stored_filename(upload_file.filename)
    stored_path = _uploads_dir() / stored_filename

    try:
        stored_path.write_bytes(contents)
    except OSError as exc:
        raise DRHPProcessingError(f"Could not save the uploaded file. ({exc})", status_code=500)

    try:
        doc = _validate_is_pdf_and_open(stored_path)
        try:
            pages, little_text_pages = extract_pages(doc)
        finally:
            doc.close()
    except DRHPProcessingError:
        # Clean up the saved file if it turned out to be unusable.
        stored_path.unlink(missing_ok=True)
        raise
    except Exception as exc:
        stored_path.unlink(missing_ok=True)
        raise DRHPProcessingError(f"Unexpected error while extracting text. ({exc})", status_code=500)

    page_count = len(pages)
    extracted_pages = page_count - len(little_text_pages)
    status = _determine_status(page_count, little_text_pages)

    document = DRHPDocument(
        original_filename=upload_file.filename,
        stored_filename=stored_filename,
        file_size=len(contents),
        page_count=page_count,
        extracted_pages=extracted_pages,
        pages_with_little_text=json.dumps(little_text_pages),
        extraction_status=status,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    return {
        "document_id": document.id,
        "original_filename": document.original_filename,
        "stored_filename": document.stored_filename,
        "file_size": document.file_size,
        "page_count": page_count,
        "extracted_pages": extracted_pages,
        "pages_with_little_text": little_text_pages,
        "status": status,
        "pages": pages,
    }


def get_document(db: Session, document_id: int) -> DRHPDocument | None:
    return db.query(DRHPDocument).filter(DRHPDocument.id == document_id).first()


def get_page_text(db: Session, document_id: int, page_number: int) -> str:
    """Re-extracts a single page's text on demand from the stored PDF,
    rather than persisting full page text in the database."""
    document = get_document(db, document_id)
    if document is None:
        raise DRHPProcessingError(f"No document found with id {document_id}.", status_code=404)

    if document.page_count and not (1 <= page_number <= document.page_count):
        raise DRHPProcessingError(
            f"Page {page_number} is out of range. This document has {document.page_count} pages.",
            status_code=400,
        )

    stored_path = _uploads_dir() / document.stored_filename
    if not stored_path.exists():
        raise DRHPProcessingError("The stored PDF file is missing.", status_code=500)

    try:
        doc = fitz.open(stored_path)
        try:
            raw_text = doc[page_number - 1].get_text()
        finally:
            doc.close()
    except Exception as exc:
        raise DRHPProcessingError(f"Could not read that page. ({exc})", status_code=500)

    return clean_text(raw_text)


def get_all_pages(db: Session, document_id: int) -> list[dict]:
    """Re-extracts every page's text on demand from the stored PDF, for use
    by Phase 5 chunking/indexing. Reuses the same extraction + cleaning path
    as the original upload, just re-run against the file already on disk
    rather than persisting page text separately."""
    document = get_document(db, document_id)
    if document is None:
        raise DRHPProcessingError(f"No document found with id {document_id}.", status_code=404)

    stored_path = _uploads_dir() / document.stored_filename
    if not stored_path.exists():
        raise DRHPProcessingError("The stored PDF file is missing.", status_code=500)

    try:
        doc = fitz.open(stored_path)
        try:
            pages, _ = extract_pages(doc)
        finally:
            doc.close()
    except Exception as exc:
        raise DRHPProcessingError(f"Could not re-read the stored PDF. ({exc})", status_code=500)

    return pages

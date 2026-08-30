"""
Embedding + FAISS vector-store service (Phase 5).

Pipeline: load extracted pages (reusing the Phase 4 service) -> chunk them
(chunking_service) -> embed each chunk locally with Sentence Transformers
-> build a FAISS index -> persist index + metadata under
data/vector_store/<document_id>/.

RAG question-answering is explicitly NOT implemented here — see Phase 6.

sentence_transformers/faiss are imported lazily (inside functions, not at
module load time) so that importing this module — and therefore starting
the FastAPI app — never fails just because these optional, heavier
dependencies aren't installed in a given environment. The rest of the API
(health, IPOs, DRHP upload/extraction) must keep working regardless.
"""

import json
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.paths import PROJECT_ROOT, resolve_project_path
from app.services import drhp_service
from app.services.chunking_service import chunk_pages
from app.services.drhp_service import DRHPProcessingError

settings = get_settings()

# Cache the loaded embedding model in-process so repeated indexing calls
# within the same running server don't reload it from disk every time.
_model_cache: dict = {}


class VectorIndexError(Exception):
    """Raised for any expected indexing failure. The router maps
    `status_code` directly onto the HTTP response."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def get_embedding_model():
    """Public so Phase 6's retrieval_service can embed a query with the
    exact same cached model instance/config, without duplicating the
    load-and-cache logic."""
    if "model" not in _model_cache:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise VectorIndexError(
                f"sentence-transformers is not installed. ({exc})", status_code=500
            )
        try:
            _model_cache["model"] = SentenceTransformer(settings.embedding_model_name)
        except Exception as exc:
            raise VectorIndexError(
                f"Could not load the embedding model '{settings.embedding_model_name}'. "
                f"This usually means the model weights couldn't be downloaded "
                f"(no internet access, or the model host is unreachable). ({exc})",
                status_code=500,
            )
    return _model_cache["model"]


def embed_chunks(chunks: list[dict]):
    """Returns a float32 numpy array of shape (len(chunks), embedding_dim),
    L2-normalized so inner product == cosine similarity."""
    import numpy as np

    model = get_embedding_model()
    texts = [c["text"] for c in chunks]
    try:
        embeddings = model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
    except Exception as exc:
        raise VectorIndexError(f"Embedding generation failed. ({exc})", status_code=500)

    return np.asarray(embeddings, dtype="float32")


def build_faiss_index(embeddings):
    """Flat inner-product index — with normalized embeddings this is
    equivalent to cosine similarity. Simple and exact, appropriate for the
    handful-of-documents scale this project targets (no need for an
    approximate/quantized index)."""
    try:
        import faiss
    except ImportError as exc:
        raise VectorIndexError(f"faiss is not installed. ({exc})", status_code=500)

    if embeddings.shape[0] == 0:
        raise VectorIndexError("No embeddings to index.", status_code=400)

    try:
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings)
    except Exception as exc:
        raise VectorIndexError(f"Building the FAISS index failed. ({exc})", status_code=500)

    return index


def vector_store_dir_for(document_id: int) -> Path:
    base = resolve_project_path(settings.vector_store_dir)
    doc_dir = base / str(document_id)
    doc_dir.mkdir(parents=True, exist_ok=True)
    return doc_dir


def save_index(document_id: int, index, chunks: list[dict]) -> Path:
    """Writes index.faiss + metadata.json, overwriting any previous version
    for this document (this is how re-indexing avoids duplicate vectors —
    the whole store is rebuilt from scratch each time, never appended to)."""
    import faiss

    doc_dir = vector_store_dir_for(document_id)

    try:
        faiss.write_index(index, str(doc_dir / "index.faiss"))
    except Exception as exc:
        raise VectorIndexError(f"Could not write the FAISS index to disk. ({exc})", status_code=500)

    metadata = {
        "document_id": document_id,
        "embedding_model": settings.embedding_model_name,
        "chunk_count": len(chunks),
        "created_at": datetime.utcnow().isoformat(),
        "chunks": chunks,
    }
    try:
        (doc_dir / "metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError as exc:
        raise VectorIndexError(f"Could not write chunk metadata to disk. ({exc})", status_code=500)

    return doc_dir


def index_document(db: Session, document_id: int) -> dict:
    """Full pipeline: load pages -> chunk -> embed -> FAISS -> persist ->
    update DB status. Never leaves the document stuck in 'processing' —
    any exception is caught and recorded as 'failed' with a message before
    being re-raised."""
    document = drhp_service.get_document(db, document_id)
    if document is None:
        raise VectorIndexError(f"No document found with id {document_id}.", status_code=404)

    document.indexing_status = "processing"
    document.indexing_error = None
    db.commit()

    try:
        if document.extraction_status == "failed":
            raise VectorIndexError(
                "This document's text extraction previously failed; there is nothing to index.",
                status_code=400,
            )

        pages = drhp_service.get_all_pages(db, document_id)
        if not pages:
            raise VectorIndexError("No pages found for this document.", status_code=400)

        if not any((p.get("text") or "").strip() for p in pages):
            raise VectorIndexError(
                "This document has no extractable text to index (see Phase 4 extraction status).",
                status_code=400,
            )

        chunks = chunk_pages(pages, document_id)
        if not chunks:
            raise VectorIndexError("No chunks could be generated from this document.", status_code=400)

        embeddings = embed_chunks(chunks)
        index = build_faiss_index(embeddings)
        doc_dir = save_index(document_id, index, chunks)

        document.indexing_status = "indexed"
        document.chunk_count = len(chunks)
        document.indexed_at = datetime.utcnow()
        document.vector_store_path = str(doc_dir.relative_to(PROJECT_ROOT))
        document.indexing_error = None
        db.commit()

        return {
            "document_id": document.id,
            "status": "indexed",
            "page_count": document.page_count,
            "chunk_count": len(chunks),
            "embedding_model": settings.embedding_model_name,
            "vector_store": "faiss",
        }

    except VectorIndexError as exc:
        document.indexing_status = "failed"
        document.indexing_error = exc.message
        db.commit()
        raise
    except DRHPProcessingError as exc:
        # Raised by the Phase 4 service (e.g. stored PDF missing). Pass its
        # message/status through as-is instead of double-wrapping it.
        document.indexing_status = "failed"
        document.indexing_error = exc.message
        db.commit()
        raise VectorIndexError(exc.message, status_code=exc.status_code)
    except Exception as exc:
        message = f"Unexpected error during indexing: {exc}"
        document.indexing_status = "failed"
        document.indexing_error = message
        db.commit()
        raise VectorIndexError(message, status_code=500)


def get_index_status(db: Session, document_id: int) -> dict:
    document = drhp_service.get_document(db, document_id)
    if document is None:
        raise VectorIndexError(f"No document found with id {document_id}.", status_code=404)

    return {
        "document_id": document.id,
        "indexing_status": document.indexing_status or "not_started",
        "chunk_count": document.chunk_count,
        "indexed_at": document.indexed_at,
        "error": document.indexing_error,
    }


def verify_index(document_id: int) -> dict:
    """Internal diagnostic helper (not exposed via any API route) that
    loads a persisted index + metadata back from disk and confirms the
    vector count matches the metadata entry count. Used during development/
    testing, and reusable by Phase 6 if useful there."""
    import faiss

    doc_dir = vector_store_dir_for(document_id)
    index_path = doc_dir / "index.faiss"
    metadata_path = doc_dir / "metadata.json"

    if not index_path.exists() or not metadata_path.exists():
        raise VectorIndexError(f"No vector store found for document {document_id}.", status_code=404)

    index = faiss.read_index(str(index_path))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    chunks = metadata.get("chunks", [])

    return {
        "document_id": document_id,
        "vector_count": index.ntotal,
        "metadata_count": len(chunks),
        "match": index.ntotal == len(chunks),
        "embedding_dim": index.d,
        "sample_chunk": chunks[0] if chunks else None,
    }

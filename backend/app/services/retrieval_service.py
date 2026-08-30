"""
Semantic retrieval service (Phase 6).

Query -> embed (same model/normalization as Phase 5) -> search the
document's persisted FAISS index -> filter by relevance -> map back to
chunk metadata -> return evidence with page/section references.

This is retrieval only. No LLM call, no generated answer — see the module
docstring in vector_service.py for why: that's explicitly a later phase.

Reuses Phase 5's embedding model loader and vector-store path resolution
(app.services.vector_service.get_embedding_model /
vector_store_dir_for) rather than duplicating them.
"""

import json

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.services import drhp_service, vector_service
from app.services.vector_service import VectorIndexError

settings = get_settings()


class RetrievalError(Exception):
    """Raised for any expected retrieval failure. The router maps
    `status_code` directly onto the HTTP response."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _validate_query(query: str) -> str:
    cleaned = (query or "").strip()
    if not cleaned:
        raise RetrievalError("Query cannot be empty.", status_code=400)
    if len(cleaned) > settings.retrieval_max_query_length:
        raise RetrievalError(
            f"Query is too long. The limit is {settings.retrieval_max_query_length} characters.",
            status_code=400,
        )
    return cleaned


def _validate_top_k(top_k: int | None) -> int:
    if top_k is None:
        return settings.retrieval_top_k_default
    if top_k < 1 or top_k > settings.retrieval_top_k_max:
        raise RetrievalError(
            f"top_k must be between 1 and {settings.retrieval_top_k_max}.", status_code=400
        )
    return top_k


def _load_index_and_metadata(document_id: int):
    """Loads the already-persisted FAISS index + metadata.json for a
    document. Never rebuilds the index — that only happens via Phase 5's
    /index endpoint."""
    import faiss

    doc_dir = vector_service.vector_store_dir_for(document_id)
    index_path = doc_dir / "index.faiss"
    metadata_path = doc_dir / "metadata.json"

    if not index_path.exists() or not metadata_path.exists():
        raise RetrievalError(
            f"No vector store found for document {document_id}. It may not have been indexed yet.",
            status_code=500,
        )

    try:
        index = faiss.read_index(str(index_path))
    except Exception as exc:
        raise RetrievalError(f"Could not read the FAISS index. ({exc})", status_code=500)

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        chunks = metadata.get("chunks", [])
    except (OSError, json.JSONDecodeError) as exc:
        raise RetrievalError(f"Could not read chunk metadata. ({exc})", status_code=500)

    if index.ntotal != len(chunks):
        raise RetrievalError(
            f"Vector store is inconsistent for document {document_id}: "
            f"{index.ntotal} vectors but {len(chunks)} metadata entries. "
            f"Try re-indexing the document.",
            status_code=500,
        )

    return index, chunks


def embed_query(query: str):
    """Embeds a single query string with the exact same model, and the
    same normalize_embeddings=True setting, used for the stored document
    chunks in Phase 5 — required so the query vector is directly comparable
    via inner product / cosine similarity."""
    import numpy as np

    try:
        model = vector_service.get_embedding_model()
        vector = model.encode(
            [query], normalize_embeddings=True, show_progress_bar=False, convert_to_numpy=True
        )
    except VectorIndexError as exc:
        # Raised by vector_service.get_embedding_model() (e.g. model
        # couldn't be downloaded). Pass its message/status through as-is
        # instead of double-wrapping it.
        raise RetrievalError(exc.message, status_code=exc.status_code)
    except Exception as exc:
        raise RetrievalError(f"Could not embed the query. ({exc})", status_code=500)

    return np.asarray(vector, dtype="float32")


def search_document(db: Session, document_id: int, query: str, top_k: int | None = None) -> dict:
    """Full retrieval pipeline. Validation order follows the Phase 6 spec:
    query -> top_k -> document exists -> document indexed -> vector store
    loadable/consistent -> embed + search."""
    clean_query = _validate_query(query)
    k = _validate_top_k(top_k)

    document = drhp_service.get_document(db, document_id)
    if document is None:
        raise RetrievalError(f"No document found with id {document_id}.", status_code=404)

    if document.indexing_status != "indexed":
        raise RetrievalError(
            f"Document {document_id} has not been indexed yet "
            f"(current status: {document.indexing_status}). "
            f"Call POST /api/drhp/{document_id}/index first.",
            status_code=409,
        )

    index, chunks = _load_index_and_metadata(document_id)

    k = min(k, index.ntotal) if index.ntotal > 0 else 0
    if k == 0:
        return {
            "document_id": document_id,
            "query": clean_query,
            "status": "no_relevant_results",
            "result_count": 0,
            "results": [],
        }

    query_vector = embed_query(clean_query)
    scores, indices = index.search(query_vector, k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(chunks):  # FAISS pads with -1 if k > ntotal in some cases
            continue
        similarity = float(score)
        if similarity < settings.retrieval_relevance_threshold:
            continue
        chunk = chunks[idx]
        results.append(
            {
                "chunk_id": chunk["chunk_id"],
                "similarity_score": round(similarity, 4),
                "page_start": chunk["page_start"],
                "page_end": chunk["page_end"],
                "section": chunk.get("section"),
                "text": chunk["text"],
            }
        )

    if not results:
        return {
            "document_id": document_id,
            "query": clean_query,
            "status": "no_relevant_results",
            "result_count": 0,
            "results": [],
        }

    return {
        "document_id": document_id,
        "query": clean_query,
        "status": "success",
        "result_count": len(results),
        "results": results,
    }

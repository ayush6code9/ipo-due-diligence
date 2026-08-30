"""
DRHP Chat service (Phase 9A).

Connects the retrieval pipeline (Phase 6) to the LLM service (Phase 8)
to provide evidence-grounded answers to user questions about a DRHP.

Flow: question → embed → FAISS search → evidence chunks → LLM → answer + sources
"""

from sqlalchemy.orm import Session

from app.services import drhp_service, retrieval_service, llm_service
from app.services.retrieval_service import RetrievalError


class ChatError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def chat_with_document(db: Session, document_id: int, question: str, top_k: int | None = None) -> dict:
    """Handle a user chat question against an indexed DRHP document.

    Returns: {document_id, question, answer, sources, llm_used}
    """
    # Validate
    clean_question = (question or "").strip()
    if not clean_question:
        raise ChatError("Question cannot be empty.", status_code=400)

    if len(clean_question) > 500:
        raise ChatError("Question is too long. Please keep it under 500 characters.", status_code=400)

    # Check document exists and is indexed
    document = drhp_service.get_document(db, document_id)
    if document is None:
        raise ChatError(f"No document found with id {document_id}.", status_code=404)

    if document.indexing_status != "indexed":
        raise ChatError(
            f"Document {document_id} has not been indexed yet. "
            f"The document needs to be processed before you can chat with it.",
            status_code=409,
        )

    # Retrieve evidence
    try:
        search_result = retrieval_service.search_document(
            db, document_id, clean_question, top_k or 5
        )
        evidence_chunks = search_result.get("results", [])
    except RetrievalError as exc:
        raise ChatError(f"Could not search the document: {exc.message}", status_code=exc.status_code)
    except Exception as exc:
        raise ChatError(f"Unexpected error during retrieval: {exc}", status_code=500)

    # Generate response
    response = llm_service.generate_chat_response(clean_question, evidence_chunks)

    return {
        "document_id": document_id,
        "question": clean_question,
        "answer": response["answer"],
        "sources": response["sources"],
        "llm_used": response["llm_used"],
    }

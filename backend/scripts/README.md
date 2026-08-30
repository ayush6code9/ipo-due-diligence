# scripts/

Development-only scripts. Never imported by the running application.

`test_only_mock_embeddings.py` — a deterministic bag-of-words embedding
used ONLY to validate Phase 6 retrieval mechanics in environments where
the real `all-MiniLM-L6-v2` model can't be downloaded (e.g. a sandboxed
network with no access to huggingface.co). It is a crude lexical
similarity stand-in, not a semantic embedding model, and is never used by
`app/services/vector_service.py` or `app/services/retrieval_service.py` —
those always use the real Sentence Transformers model.

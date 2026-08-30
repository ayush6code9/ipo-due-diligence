"""
TEST-ONLY mock embedding function.

This is NOT part of the shipped application. app/services/vector_service.py
and app/services/retrieval_service.py always use the real
sentence-transformers "all-MiniLM-L6-v2" model — nothing in app/ imports
this file.

Purpose: in a sandboxed environment where huggingface.co is unreachable
(confirmed for this project's dev sandbox), the real model can't be
downloaded, so genuine semantic retrieval can't be exercised end-to-end.
Rather than testing with meaningless random vectors (which can validate
plumbing but not *whether relevant chunks actually rank higher*), this
gives a crude but real lexical-similarity signal — bag-of-words with
feature hashing, L2-normalized — so retrieval ranking can be honestly
validated: does asking about "risk" actually surface the Risk Factors
chunk above unrelated ones? That's a meaningful test even though the
underlying vectors aren't true semantic embeddings.

Anywhere the real model CAN be downloaded (i.e. normal internet access,
which is all real deployment targets), this file is irrelevant — the app
never touches it.
"""

import re

import numpy as np

DIM = 384  # matches all-MiniLM-L6-v2's real output dimension
_TOKEN_RE = re.compile(r"[a-zA-Z]+")

_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "is", "are",
    "was", "were", "be", "been", "as", "at", "by", "with", "from", "that",
    "this", "our", "we", "us", "it", "its", "has", "have", "had", "will",
    "which", "any", "such", "may", "not", "no",
}


def _tokenize(text: str) -> list[str]:
    return [w.lower() for w in _TOKEN_RE.findall(text) if w.lower() not in _STOPWORDS and len(w) > 2]


def _stable_hash(token: str) -> int:
    """A deterministic hash (Python's built-in hash() is randomized per
    process via PYTHONHASHSEED, which would make indexing-time and
    query-time feature hashing land in different buckets across separate
    process runs)."""
    h = 0
    for ch in token:
        h = (h * 131 + ord(ch)) % 1_000_003
    return h


def mock_embed_texts(texts: list[str]) -> np.ndarray:
    """Bag-of-words feature hashing into a fixed DIM-dimensional vector per
    text, L2-normalized (so it's drop-in compatible with the real
    normalize_embeddings=True + IndexFlatIP setup)."""
    vectors = np.zeros((len(texts), DIM), dtype="float32")
    for i, text in enumerate(texts):
        for token in _tokenize(text):
            idx = _stable_hash(token) % DIM
            vectors[i, idx] += 1.0
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0  # avoid divide-by-zero for empty/all-stopword text
    return vectors / norms

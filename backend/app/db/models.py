"""
IPO database model.

Field list follows the Phase 3 spec (basic info, market info, assessment,
financial info). A few small fields — sector, status, overview, created_at —
are added beyond that list because the existing Phase 2 dashboard and search
UI already display them; without these, seeded rows wouldn't be usable by
the frontend they're meant to eventually feed. Nothing else was added.
"""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class IPO(Base):
    __tablename__ = "ipos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # --- Basic IPO information ---
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    ipo_name: Mapped[str] = mapped_column(String(200), nullable=False)
    issue_size: Mapped[str | None] = mapped_column(String(50))
    price_band: Mapped[str | None] = mapped_column(String(50))
    lot_size: Mapped[str | None] = mapped_column(String(50))
    minimum_investment: Mapped[str | None] = mapped_column(String(50))
    ipo_open_date: Mapped[date | None] = mapped_column(Date)
    ipo_close_date: Mapped[date | None] = mapped_column(Date)
    listing_date: Mapped[date | None] = mapped_column(Date)

    # --- Small additions used by the existing frontend (see module docstring) ---
    sector: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str | None] = mapped_column(String(20))  # Open / Upcoming / Closed
    overview: Mapped[str | None] = mapped_column(Text)

    # --- Market information ---
    gmp: Mapped[float | None] = mapped_column(Float)
    gmp_updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    retail_subscription: Mapped[float | None] = mapped_column(Float)
    nii_subscription: Mapped[float | None] = mapped_column(Float)
    qib_subscription: Mapped[float | None] = mapped_column(Float)
    overall_subscription: Mapped[float | None] = mapped_column(Float)

    # --- Assessment ---
    overall_score: Mapped[int | None] = mapped_column(Integer)
    financial_score: Mapped[int | None] = mapped_column(Integer)
    risk_level: Mapped[str | None] = mapped_column(String(20))
    promoter_quality: Mapped[str | None] = mapped_column(String(20))
    market_interest: Mapped[str | None] = mapped_column(String(20))

    # --- Financial information ---
    revenue_growth: Mapped[float | None] = mapped_column(Float)
    profit_margin: Mapped[float | None] = mapped_column(Float)
    debt_level: Mapped[float | None] = mapped_column(Float)
    roe: Mapped[float | None] = mapped_column(Float)
    roa: Mapped[float | None] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DRHPDocument(Base):
    """
    Metadata for an uploaded DRHP PDF (Phase 4) and its Phase 5 indexing
    status.

    Only metadata is persisted here — the extracted page text itself is not
    stored in the database (that would mean a growing text blob per
    document, which isn't needed yet). When a specific page's text is
    requested later, it's re-extracted on demand from the stored PDF file.
    Actual chunk text + vectors live in data/vector_store/<document_id>/
    (index.faiss + metadata.json), not in SQLite.
    """

    __tablename__ = "drhp_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)

    page_count: Mapped[int | None] = mapped_column(Integer)
    extracted_pages: Mapped[int | None] = mapped_column(Integer)
    # JSON-encoded list of 1-based page numbers with little/no extractable text,
    # e.g. "[37, 218]". Kept as a small text field rather than a separate table.
    pages_with_little_text: Mapped[str | None] = mapped_column(Text)

    # "success" | "partial" | "no_extractable_text" | "failed"
    extraction_status: Mapped[str] = mapped_column(String(30), nullable=False)

    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # --- Phase 5: chunking / embedding / FAISS indexing status ---
    # "not_started" | "processing" | "indexed" | "failed"
    indexing_status: Mapped[str] = mapped_column(String(20), nullable=False, default="not_started")
    chunk_count: Mapped[int | None] = mapped_column(Integer)
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime)
    # Project-relative path, e.g. "data/vector_store/3"
    vector_store_path: Mapped[str | None] = mapped_column(String(500))
    indexing_error: Mapped[str | None] = mapped_column(Text)

    # --- Phase 7A/7B: extraction + analysis status ---
    # "not_started" | "processing" | "completed" | "failed"
    extraction_status: Mapped[str] = mapped_column(String(20), nullable=False, default="not_started")
    analysis_status: Mapped[str] = mapped_column(String(20), nullable=False, default="not_started")

    # --- Source tracking (for documents fetched via IPO search) ---
    source_url: Mapped[str | None] = mapped_column(String(500))
    source_name: Mapped[str | None] = mapped_column(String(100))  # "Upload" | "Chittorgarh" | "SEBI" etc.


class DRHPExtraction(Base):
    """Persisted structured extraction results for a DRHP document (Phase 7A).

    The extracted data is stored as a JSON text blob — flexible enough to
    evolve without schema migrations, and small enough that a single TEXT
    column is fine for the project's scale.
    """

    __tablename__ = "drhp_extractions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    extraction_data: Mapped[str] = mapped_column(Text, nullable=False)  # JSON blob
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DRHPAnalysis(Base):
    """Persisted analysis results for a DRHP document (Phase 7B).

    Built from the extraction results — deterministic scoring + interpretation.
    """

    __tablename__ = "drhp_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    analysis_data: Mapped[str] = mapped_column(Text, nullable=False)  # JSON blob
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class IPOSearchCache(Base):
    """Cached IPO search results from external sources.

    Simple TTL-based cache to avoid repeated external requests for the same
    query. Stored as a JSON blob of serialized IPOSearchResult objects.
    """

    __tablename__ = "ipo_search_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query_hash: Mapped[str] = mapped_column(String(64), index=True)
    results_json: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

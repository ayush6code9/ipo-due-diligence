"""
IPO Research Platform - Backend Entry Point

Full pipeline: DRHP upload → text extraction → chunking → embeddings →
FAISS indexing → semantic retrieval → structured extraction → deterministic
analysis → AI summary → RAG chat → report generation.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.database import SessionLocal, init_db
from app.db.seed import seed_demo_data
from app.routers import analysis, chat, drhp, extraction, health, ipo_search, ipos, report

settings = get_settings()

app = FastAPI(
    title="IPO Research Platform API",
    description="Backend API for the AI-based IPO Research Platform for retail investors.",
    version="0.1.0",
)

# CORS: allow the local Vite dev server (and any origins configured in .env)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Create the SQLite file/tables and seed demo data if the table is empty."""
    init_db()
    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()


# Routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(ipos.router, prefix="/api", tags=["ipos"])
app.include_router(ipo_search.router, prefix="/api", tags=["ipo-search"])
app.include_router(drhp.router, prefix="/api", tags=["drhp"])
app.include_router(extraction.router, prefix="/api", tags=["extraction"])
app.include_router(analysis.router, prefix="/api", tags=["analysis"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(report.router, prefix="/api", tags=["report"])


@app.get("/")
def root():
    return {"message": "IPO Research Platform API is running. See /docs for API documentation."}

"""
Health check endpoint.

Used to verify the backend is running, and later for simple
uptime checks from the frontend or deployment platform.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "ok"}

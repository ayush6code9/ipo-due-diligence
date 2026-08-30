"""
IPO endpoints.

GET /api/ipos               - list all IPOs (summary shape)
GET /api/ipos/search?q=...  - search by company/IPO name (summary shape)
GET /api/ipos/{ipo_id}      - single IPO, full detail

Note: the /search route is declared before /{ipo_id} so "search" isn't
swallowed as an attempted (invalid) integer id.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.ipo import IPODetail, IPOListItem
from app.services import ipo_service

router = APIRouter()


@router.get("/ipos", response_model=list[IPOListItem])
def list_ipos(db: Session = Depends(get_db)):
    try:
        return ipo_service.get_all_ipos(db)
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Could not read IPOs from the database.")


@router.get("/ipos/search", response_model=list[IPOListItem])
def search_ipos(
    q: str = Query(..., min_length=1, description="Company or IPO name to search for"),
    db: Session = Depends(get_db),
):
    try:
        return ipo_service.search_ipos(db, q)
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Search failed due to a database error.")


@router.get("/ipos/{ipo_id}", response_model=IPODetail)
def get_ipo(ipo_id: int, db: Session = Depends(get_db)):
    try:
        ipo = ipo_service.get_ipo_by_id(db, ipo_id)
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Could not read this IPO from the database.")

    if ipo is None:
        raise HTTPException(status_code=404, detail=f"No IPO found with id {ipo_id}.")
    return ipo

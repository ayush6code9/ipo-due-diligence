"""
IPO service layer.

Thin query functions between the router and the database. Kept separate
from the router so the router stays focused on HTTP concerns (status
codes, request/response shapes) and this stays focused on queries.
"""

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.models import IPO


def get_all_ipos(db: Session) -> list[IPO]:
    return db.query(IPO).order_by(IPO.company_name).all()


def get_ipo_by_id(db: Session, ipo_id: int) -> IPO | None:
    return db.query(IPO).filter(IPO.id == ipo_id).first()


def search_ipos(db: Session, query: str) -> list[IPO]:
    pattern = f"%{query.strip()}%"
    return (
        db.query(IPO)
        .filter(or_(IPO.company_name.ilike(pattern), IPO.ipo_name.ilike(pattern)))
        .order_by(IPO.company_name)
        .all()
    )

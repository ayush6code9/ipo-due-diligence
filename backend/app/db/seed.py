"""
Seed mechanism for demo IPO data.

`seed_demo_data(db)` is idempotent — it only inserts records if the table
is empty, so it's safe to call automatically on every app startup. It can
also be run manually:

    cd backend
    python -m app.db.seed

Values mirror the Phase 2 mock data (see frontend/src/data/mockData.js) so
the eventual frontend/backend swap is a straightforward data-source change,
not a redesign.
"""

from datetime import date, datetime

from sqlalchemy.orm import Session

from app.db.database import SessionLocal, init_db
from app.db.models import IPO

DEMO_IPOS = [
    {
        "company_name": "Apex Industrial Components Ltd",
        "ipo_name": "Apex Industrial Components IPO",
        "issue_size": "₹1,240 Cr",
        "price_band": "₹412 – ₹434",
        "lot_size": "34 shares",
        "minimum_investment": "₹14,756",
        "ipo_open_date": date(2026, 8, 18),
        "ipo_close_date": date(2026, 8, 21),
        "listing_date": None,
        "sector": "Industrial Manufacturing",
        "status": "Open",
        "overview": (
            "Apex Industrial Components manufactures precision-machined parts for the "
            "automotive and heavy-equipment industries, supplying both domestic and "
            "export customers from three facilities in Gujarat and Tamil Nadu."
        ),
        "gmp": 38.0,
        "gmp_updated_at": datetime(2026, 8, 18, 9, 40),
        "retail_subscription": 1.8,
        "nii_subscription": 2.3,
        "qib_subscription": 0.6,
        "overall_subscription": 1.6,
        "overall_score": 84,
        "financial_score": 84,
        "risk_level": "Medium",
        "promoter_quality": "Good",
        "market_interest": "High",
        "revenue_growth": 18.4,
        "profit_margin": 12.1,
        "debt_level": 0.42,
        "roe": 21.3,
        "roa": 9.7,
    },
    {
        "company_name": "Northgate Logistics Ltd",
        "ipo_name": "Northgate Logistics IPO",
        "issue_size": "₹640 Cr",
        "price_band": "₹128 – ₹135",
        "lot_size": "110 shares",
        "minimum_investment": "₹14,850",
        "ipo_open_date": date(2026, 9, 2),
        "ipo_close_date": date(2026, 9, 4),
        "listing_date": None,
        "sector": "Logistics & Supply Chain",
        "status": "Upcoming",
        "overview": (
            "Northgate Logistics operates a fleet-based freight and warehousing network "
            "across northern and western India, serving e-commerce and FMCG clients."
        ),
        "gmp": 6.0,
        "gmp_updated_at": datetime(2026, 8, 20, 10, 15),
        "retail_subscription": None,
        "nii_subscription": None,
        "qib_subscription": None,
        "overall_subscription": None,
        "overall_score": 61,
        "financial_score": 58,
        "risk_level": "Medium",
        "promoter_quality": "Average",
        "market_interest": "Medium",
        "revenue_growth": 9.2,
        "profit_margin": 6.4,
        "debt_level": 0.88,
        "roe": 11.5,
        "roa": 4.9,
    },
]


def seed_demo_data(db: Session):
    """Insert demo IPO rows only if the table is currently empty."""
    already_seeded = db.query(IPO).first() is not None
    if already_seeded:
        return 0

    for record in DEMO_IPOS:
        db.add(IPO(**record))
    db.commit()
    return len(DEMO_IPOS)


if __name__ == "__main__":
    init_db()
    session = SessionLocal()
    try:
        inserted = seed_demo_data(session)
        if inserted:
            print(f"Inserted {inserted} demo IPO record(s).")
        else:
            print("Table already has data — nothing inserted.")
    finally:
        session.close()

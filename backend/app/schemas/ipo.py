"""
Pydantic response models for the IPO endpoints.

Two shapes are used:
- IPOListItem: a lighter summary for GET /api/ipos and the search endpoint
  (enough to render a search result row).
- IPODetail: the full record, for GET /api/ipos/{id} (enough to render the
  dashboard).
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class IPOListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_name: str
    ipo_name: str
    sector: str | None = None
    status: str | None = None
    overall_score: int | None = None
    risk_level: str | None = None
    gmp: float | None = None


class IPODetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int

    # Basic IPO information
    company_name: str
    ipo_name: str
    issue_size: str | None = None
    price_band: str | None = None
    lot_size: str | None = None
    minimum_investment: str | None = None
    ipo_open_date: date | None = None
    ipo_close_date: date | None = None
    listing_date: date | None = None

    sector: str | None = None
    status: str | None = None
    overview: str | None = None

    # Market information
    gmp: float | None = None
    gmp_updated_at: datetime | None = None
    retail_subscription: float | None = None
    nii_subscription: float | None = None
    qib_subscription: float | None = None
    overall_subscription: float | None = None

    # Assessment
    overall_score: int | None = None
    financial_score: int | None = None
    risk_level: str | None = None
    promoter_quality: str | None = None
    market_interest: str | None = None

    # Financial information
    revenue_growth: float | None = None
    profit_margin: float | None = None
    debt_level: float | None = None
    roe: float | None = None
    roa: float | None = None

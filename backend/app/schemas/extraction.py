"""
Pydantic schemas for structured DRHP extraction results (Phase 7A).

Every important extracted value carries source evidence (chunk_id,
page_start, page_end, section) for traceability.
"""

from __future__ import annotations

from pydantic import BaseModel


# ---- Source evidence attached to extracted values ----

class SourceEvidence(BaseModel):
    chunk_id: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    section: str | None = None
    text_snippet: str | None = None  # short excerpt from the source chunk


# ---- Sub-structures ----

class CompanyInfo(BaseModel):
    company_name: str | None = None
    business_description: str | None = None
    sector: str | None = None
    incorporation_date: str | None = None
    registered_office: str | None = None
    evidence: list[SourceEvidence] = []


class IPOParameters(BaseModel):
    issue_size: str | None = None
    price_band: str | None = None
    lot_size: str | None = None
    minimum_investment: str | None = None
    ipo_open_date: str | None = None
    ipo_close_date: str | None = None
    listing_date: str | None = None
    fresh_issue: str | None = None
    offer_for_sale: str | None = None
    face_value: str | None = None
    evidence: list[SourceEvidence] = []


class FinancialYearData(BaseModel):
    """Financial data for a single year."""
    year: str | None = None  # e.g. "FY2024", "FY2023"
    revenue: float | None = None  # in crores
    profit: float | None = None  # PAT, in crores
    total_assets: float | None = None
    total_liabilities: float | None = None
    net_worth: float | None = None
    total_debt: float | None = None
    cash_flow_operations: float | None = None
    evidence: list[SourceEvidence] = []


class FinancialData(BaseModel):
    years: list[FinancialYearData] = []
    currency: str = "INR"
    unit: str = "Crores"
    evidence: list[SourceEvidence] = []


class FinancialRatios(BaseModel):
    """Deterministically calculated from FinancialData — NOT extracted."""
    revenue_growth_pct: float | None = None
    profit_margin_pct: float | None = None
    debt_to_equity: float | None = None
    roe_pct: float | None = None
    roa_pct: float | None = None
    current_year: str | None = None


class PromoterInfo(BaseModel):
    name: str | None = None
    designation: str | None = None
    experience_years: int | None = None
    experience_description: str | None = None


class PromoterData(BaseModel):
    promoters: list[PromoterInfo] = []
    pre_issue_shareholding_pct: float | None = None
    post_issue_shareholding_pct: float | None = None
    evidence: list[SourceEvidence] = []


class RiskFactor(BaseModel):
    category: str  # "Business Risk", "Financial Risk", "Legal Risk", etc.
    description: str
    severity: str | None = None  # "Low", "Medium", "High" — inferred
    evidence: list[SourceEvidence] = []


class LitigationItem(BaseModel):
    description: str
    parties: str | None = None
    status: str | None = None  # "Pending", "Resolved", etc.
    amount: str | None = None
    evidence: list[SourceEvidence] = []


# ---- Top-level extraction result ----

class ExtractionResult(BaseModel):
    document_id: int
    status: str  # "completed" | "partial" | "failed"
    company_info: CompanyInfo = CompanyInfo()
    ipo_parameters: IPOParameters = IPOParameters()
    financial_data: FinancialData = FinancialData()
    financial_ratios: FinancialRatios = FinancialRatios()
    promoter_data: PromoterData = PromoterData()
    risk_factors: list[RiskFactor] = []
    litigation: list[LitigationItem] = []
    strengths: list[str] = []
    concerns: list[str] = []


# ---- API response shapes ----

class ExtractionResponse(BaseModel):
    """Response for POST /api/drhp/{document_id}/extract"""
    document_id: int
    status: str
    extraction: ExtractionResult


class ExtractionStatusResponse(BaseModel):
    """Response for GET /api/drhp/{document_id}/extraction"""
    document_id: int
    extraction_status: str
    extraction: ExtractionResult | None = None

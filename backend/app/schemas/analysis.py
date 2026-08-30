"""
Pydantic schemas for the analysis layer (Phase 7B).
"""

from __future__ import annotations

from pydantic import BaseModel


class FinancialHealthAnalysis(BaseModel):
    score: int | None = None  # 0-100
    max_score: int = 100
    status: str = "Unavailable"  # "Strong", "Moderate", "Weak", "Unavailable"
    level: str = "moderate"  # "strong", "moderate", "high-risk"
    revenue_trend: str | None = None  # "Growing", "Stable", "Declining", "Unavailable"
    profit_trend: str | None = None
    margin_trend: str | None = None
    debt_position: str | None = None
    cash_flow_status: str | None = None
    reasons: list[str] = []


class RiskAnalysisItem(BaseModel):
    category: str
    severity: str  # "Low", "Medium", "High"
    level: str  # "strong", "moderate", "high-risk"
    reason: str
    impact: str | None = None


class RiskAnalysis(BaseModel):
    overall_risk_level: str = "Medium"  # "Low", "Medium", "High"
    overall_level: str = "moderate"  # for UI color
    risks: list[RiskAnalysisItem] = []


class PromoterAnalysis(BaseModel):
    stars: int = 0  # 0-5
    max_stars: int = 5
    label: str = "Unavailable"  # "Excellent", "Good", "Average", "Needs Attention"
    level: str = "moderate"
    points: list[str] = []
    litigation_present: bool = False
    litigation_note: str | None = None


class OverallAssessment(BaseModel):
    score: int = 0  # 0-100
    max_score: int = 100
    label: str = "Unavailable"
    level: str = "moderate"  # "strong", "moderate", "high-risk"


class FinancialMetric(BaseModel):
    key: str
    label: str
    value: str
    trend: str  # "up", "down", "flat"
    meaning: str
    learn_more: str


class AnalysisResult(BaseModel):
    document_id: int
    status: str  # "completed" | "partial" | "failed"

    overall_assessment: OverallAssessment = OverallAssessment()
    risk_level: dict = {"label": "Medium", "level": "moderate"}
    promoter_quality_summary: dict = {"label": "Unavailable", "level": "moderate"}
    market_interest: dict = {"label": "Unavailable", "level": "moderate"}

    financial_health: FinancialHealthAnalysis = FinancialHealthAnalysis()
    financial_metrics: list[FinancialMetric] = []
    risk_analysis: RiskAnalysis = RiskAnalysis()
    promoter_analysis: PromoterAnalysis = PromoterAnalysis()

    top_strengths: list[str] = []
    top_risks: list[str] = []

    ai_summary: str | None = None

    # Chart data for frontend
    charts: dict = {}

    # Company info (passed through from extraction)
    company_name: str | None = None
    sector: str | None = None
    overview: str | None = None

    # IPO parameters (passed through from extraction)
    ipo_parameters: dict = {}


class AnalysisResponse(BaseModel):
    document_id: int
    status: str
    analysis: AnalysisResult


class AnalysisStatusResponse(BaseModel):
    document_id: int
    analysis_status: str
    analysis: AnalysisResult | None = None

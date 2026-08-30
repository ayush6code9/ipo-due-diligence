"""
Deterministic analysis service (Phase 7B).

Transforms extracted DRHP data (Phase 7A) into scored assessments,
beginner-friendly financial metrics, and categorized risk/promoter analysis.

All scoring is deterministic and testable. No LLM calls. Missing data
produces "Unavailable" — never guesses or fabricates.

Language conventions:
  - "Financially Strong", "Moderate Risk", "High Risk"
  - "Good Promoter Quality", "Needs Attention"
  - NEVER "Guaranteed Buy", "Guaranteed Apply", "Risk-Free"
"""

import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import DRHPAnalysis, DRHPDocument
from app.schemas.analysis import (
    AnalysisResult,
    FinancialHealthAnalysis,
    FinancialMetric,
    OverallAssessment,
    PromoterAnalysis,
    RiskAnalysis,
    RiskAnalysisItem,
)
from app.schemas.extraction import ExtractionResult
from app.services import drhp_service, extraction_service, llm_service
from app.services.extraction_service import ExtractionError


class AnalysisError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# ---------------------------------------------------------------------------
# Financial Health Analysis
# ---------------------------------------------------------------------------

def _analyze_financial_health(extraction: ExtractionResult) -> FinancialHealthAnalysis:
    """Deterministic financial health scoring from extracted data."""
    health = FinancialHealthAnalysis()
    score = 0
    max_components = 0
    reasons = []

    ratios = extraction.financial_ratios
    fin = extraction.financial_data

    # 1. Revenue trend (20 points max)
    max_components += 20
    if ratios.revenue_growth_pct is not None:
        if ratios.revenue_growth_pct > 15:
            score += 20
            health.revenue_trend = "Growing"
            reasons.append(f"Revenue has grown by {ratios.revenue_growth_pct}% — strong growth")
        elif ratios.revenue_growth_pct > 5:
            score += 15
            health.revenue_trend = "Growing"
            reasons.append(f"Revenue has grown by {ratios.revenue_growth_pct}% — steady growth")
        elif ratios.revenue_growth_pct >= 0:
            score += 10
            health.revenue_trend = "Stable"
            reasons.append(f"Revenue is roughly stable ({ratios.revenue_growth_pct}% change)")
        else:
            score += 3
            health.revenue_trend = "Declining"
            reasons.append(f"Revenue has declined by {abs(ratios.revenue_growth_pct)}%")
    else:
        health.revenue_trend = "Unavailable"

    # 2. Profitability (20 points max)
    max_components += 20
    if ratios.profit_margin_pct is not None:
        if ratios.profit_margin_pct > 15:
            score += 20
            health.profit_trend = "Strong"
            reasons.append(f"Profit margin is healthy at {ratios.profit_margin_pct}%")
        elif ratios.profit_margin_pct > 5:
            score += 15
            health.profit_trend = "Moderate"
            reasons.append(f"Profit margin is moderate at {ratios.profit_margin_pct}%")
        elif ratios.profit_margin_pct > 0:
            score += 8
            health.profit_trend = "Thin"
            reasons.append(f"Profit margin is thin at {ratios.profit_margin_pct}%")
        else:
            score += 0
            health.profit_trend = "Loss-Making"
            reasons.append("The company is currently operating at a loss")
    else:
        health.profit_trend = "Unavailable"

    # 3. Debt position (20 points max)
    max_components += 20
    if ratios.debt_to_equity is not None:
        if ratios.debt_to_equity < 0.3:
            score += 20
            health.debt_position = "Very Low"
            reasons.append(f"Debt levels are very low (D/E: {ratios.debt_to_equity})")
        elif ratios.debt_to_equity < 0.7:
            score += 16
            health.debt_position = "Manageable"
            reasons.append(f"Debt is under control (D/E: {ratios.debt_to_equity})")
        elif ratios.debt_to_equity < 1.5:
            score += 10
            health.debt_position = "Moderate"
            reasons.append(f"Moderate debt levels (D/E: {ratios.debt_to_equity})")
        else:
            score += 3
            health.debt_position = "High"
            reasons.append(f"Debt levels are high (D/E: {ratios.debt_to_equity})")
    else:
        health.debt_position = "Unavailable"

    # 4. ROE (20 points max)
    max_components += 20
    if ratios.roe_pct is not None:
        if ratios.roe_pct > 20:
            score += 20
            reasons.append(f"Strong return on equity ({ratios.roe_pct}%)")
        elif ratios.roe_pct > 12:
            score += 15
        elif ratios.roe_pct > 5:
            score += 10
        elif ratios.roe_pct > 0:
            score += 5
        else:
            score += 0
            reasons.append(f"Negative return on equity ({ratios.roe_pct}%)")

    # 5. ROA (20 points max)
    max_components += 20
    if ratios.roa_pct is not None:
        if ratios.roa_pct > 10:
            score += 20
        elif ratios.roa_pct > 5:
            score += 15
        elif ratios.roa_pct > 2:
            score += 10
        elif ratios.roa_pct > 0:
            score += 5

    # Calculate final score as percentage
    if max_components > 0:
        final_score = int(round((score / max_components) * 100))
    else:
        final_score = None

    health.score = final_score
    health.reasons = reasons

    if final_score is not None:
        if final_score >= 70:
            health.status = "Strong"
            health.level = "strong"
        elif final_score >= 40:
            health.status = "Moderate"
            health.level = "moderate"
        else:
            health.status = "Weak"
            health.level = "high-risk"

    return health


# ---------------------------------------------------------------------------
# Financial Metrics (beginner-friendly)
# ---------------------------------------------------------------------------

def _build_financial_metrics(extraction: ExtractionResult) -> list[FinancialMetric]:
    """Build financial metrics with plain-English meanings."""
    metrics = []
    ratios = extraction.financial_ratios

    if ratios.revenue_growth_pct is not None:
        trend = "up" if ratios.revenue_growth_pct > 2 else ("down" if ratios.revenue_growth_pct < -2 else "flat")
        metrics.append(FinancialMetric(
            key="revenueGrowth",
            label="Revenue Growth",
            value=f"{ratios.revenue_growth_pct}%",
            trend=trend,
            meaning="Sales have grown by this much compared to the previous year — a sign the business is expanding." if ratios.revenue_growth_pct > 0
                else "Sales have declined compared to the previous year.",
            learn_more="Revenue growth alone doesn't guarantee profit — check this alongside profit margin to see if growth is translating into earnings.",
        ))

    if ratios.profit_margin_pct is not None:
        trend = "up" if ratios.profit_margin_pct > 10 else ("down" if ratios.profit_margin_pct < 0 else "flat")
        value_desc = (
            f"Out of every ₹100 in sales, the company keeps about ₹{abs(round(ratios.profit_margin_pct))} as profit after all expenses."
            if ratios.profit_margin_pct > 0
            else "The company is currently spending more than it earns — operating at a loss."
        )
        metrics.append(FinancialMetric(
            key="profitMargin",
            label="Profit Margin",
            value=f"{ratios.profit_margin_pct}%",
            trend=trend,
            meaning=value_desc,
            learn_more="Profit margins vary a lot by industry, so this is most meaningful when compared with similar companies.",
        ))

    if ratios.debt_to_equity is not None:
        trend = "flat"
        if ratios.debt_to_equity > 1:
            trend = "down"
        elif ratios.debt_to_equity < 0.3:
            trend = "up"
        metrics.append(FinancialMetric(
            key="debtToEquity",
            label="Debt-to-Equity",
            value=f"{ratios.debt_to_equity}",
            trend=trend,
            meaning="Shows how much the company relies on borrowed money compared with shareholders' money. Below 1 is generally considered manageable.",
            learn_more="A very low ratio isn't automatically better — some borrowing can help a company grow faster. Extremely high ratios are the bigger warning sign.",
        ))

    if ratios.roe_pct is not None:
        trend = "up" if ratios.roe_pct > 15 else ("down" if ratios.roe_pct < 5 else "flat")
        metrics.append(FinancialMetric(
            key="roe",
            label="ROE (Return on Equity)",
            value=f"{ratios.roe_pct}%",
            trend=trend,
            meaning=f"The company generates about ₹{round(ratios.roe_pct)} of profit for every ₹100 of shareholders' money. Higher is generally better.",
            learn_more="A high ROE driven mainly by heavy borrowing (rather than genuine efficiency) can be misleading — read alongside Debt-to-Equity.",
        ))

    if ratios.roa_pct is not None:
        trend = "up" if ratios.roa_pct > 8 else ("down" if ratios.roa_pct < 3 else "flat")
        metrics.append(FinancialMetric(
            key="roa",
            label="ROA (Return on Assets)",
            value=f"{ratios.roa_pct}%",
            trend=trend,
            meaning="Shows how efficiently the company uses everything it owns — factories, equipment, cash — to generate profit.",
            learn_more="Asset-heavy industries like manufacturing typically show lower ROA than asset-light businesses like software — compare within the same sector.",
        ))

    return metrics


# ---------------------------------------------------------------------------
# Risk Analysis
# ---------------------------------------------------------------------------

def _analyze_risks(extraction: ExtractionResult) -> RiskAnalysis:
    """Categorize and score risks."""
    analysis = RiskAnalysis()
    items = []

    # Map extracted risk factors to analysis items
    category_risks: dict[str, list] = {}
    for rf in extraction.risk_factors:
        cat = rf.category
        if cat not in category_risks:
            category_risks[cat] = []
        category_risks[cat].append(rf)

    severity_to_level = {"Low": "strong", "Medium": "moderate", "High": "high-risk"}

    for category, risks in category_risks.items():
        # Use the highest severity in this category
        severities = [r.severity or "Medium" for r in risks]
        if "High" in severities:
            overall_severity = "High"
        elif "Medium" in severities:
            overall_severity = "Medium"
        else:
            overall_severity = "Low"

        # Combine descriptions for this category
        reason = risks[0].description if risks else "No specific details available."
        impact = None
        if overall_severity == "High":
            impact = "This could have a significant impact on the company's operations or finances."
        elif overall_severity == "Medium":
            impact = "Moderate expected impact — worth understanding before investing."
        else:
            impact = "Low expected impact on operations or finances at this time."

        items.append(RiskAnalysisItem(
            category=category,
            severity=overall_severity,
            level=severity_to_level.get(overall_severity, "moderate"),
            reason=reason[:300],
            impact=impact,
        ))

    # If no risks were extracted, add defaults
    if not items:
        # Check if litigation was found
        if extraction.litigation:
            items.append(RiskAnalysisItem(
                category="Legal Risk",
                severity="Medium",
                level="moderate",
                reason="Litigation matters were disclosed in the DRHP.",
                impact="Legal proceedings could have financial implications.",
            ))
        else:
            items.append(RiskAnalysisItem(
                category="General",
                severity="Medium",
                level="moderate",
                reason="Insufficient data was available to identify specific risk factors from the DRHP.",
                impact="Review the document manually for detailed risk information.",
            ))

    analysis.risks = items

    # Overall risk level
    high_count = sum(1 for r in items if r.severity == "High")
    medium_count = sum(1 for r in items if r.severity == "Medium")

    if high_count >= 2:
        analysis.overall_risk_level = "High"
        analysis.overall_level = "high-risk"
    elif high_count >= 1 or medium_count >= 3:
        analysis.overall_risk_level = "Medium"
        analysis.overall_level = "moderate"
    else:
        analysis.overall_risk_level = "Low"
        analysis.overall_level = "strong"

    return analysis


# ---------------------------------------------------------------------------
# Promoter Analysis
# ---------------------------------------------------------------------------

def _analyze_promoters(extraction: ExtractionResult) -> PromoterAnalysis:
    """Score promoter quality."""
    analysis = PromoterAnalysis()
    points = []
    star_score = 0  # out of 5

    promoter_data = extraction.promoter_data

    # Experience
    if promoter_data.promoters:
        exp_years = [p.experience_years for p in promoter_data.promoters if p.experience_years]
        if exp_years:
            max_exp = max(exp_years)
            if max_exp >= 15:
                star_score += 2
                points.append(f"Promoters have {max_exp}+ years of industry experience")
            elif max_exp >= 8:
                star_score += 1.5
                points.append(f"Promoters have {max_exp}+ years of experience")
            elif max_exp >= 3:
                star_score += 1
                points.append(f"Promoters have {max_exp} years of experience")
        else:
            points.append("Promoter experience details could not be reliably extracted")

        # Names
        names = [p.name for p in promoter_data.promoters if p.name]
        if names:
            points.append(f"Identified promoters: {', '.join(names[:3])}")
    else:
        points.append("Promoter details could not be reliably extracted from the DRHP")

    # Ownership
    if promoter_data.pre_issue_shareholding_pct is not None:
        if promoter_data.pre_issue_shareholding_pct > 70:
            star_score += 1.5
            points.append(f"Promoters hold {promoter_data.pre_issue_shareholding_pct}% stake (pre-issue) — significant ownership")
        elif promoter_data.pre_issue_shareholding_pct > 50:
            star_score += 1
            points.append(f"Promoters hold {promoter_data.pre_issue_shareholding_pct}% stake (pre-issue)")
        else:
            star_score += 0.5
            points.append(f"Promoters hold {promoter_data.pre_issue_shareholding_pct}% stake (pre-issue)")

    # Litigation
    if extraction.litigation:
        analysis.litigation_present = True
        count = len(extraction.litigation)
        pending = sum(1 for l in extraction.litigation if l.status == "Pending")
        if pending > 0:
            analysis.litigation_note = f"{count} disclosed litigation matter(s), {pending} pending."
            if pending >= 3:
                star_score -= 0.5
        else:
            analysis.litigation_note = f"{count} disclosed litigation matter(s), none currently pending."
            star_score += 0.5
    else:
        analysis.litigation_present = False
        analysis.litigation_note = "No significant litigation was identified in the analysed document."
        star_score += 0.5

    # Calculate stars (0-5)
    analysis.stars = max(0, min(5, round(star_score)))
    analysis.points = points

    # Label
    if analysis.stars >= 4:
        analysis.label = "Good"
        analysis.level = "strong"
    elif analysis.stars >= 3:
        analysis.label = "Average"
        analysis.level = "moderate"
    else:
        analysis.label = "Needs Attention"
        analysis.level = "high-risk"

    return analysis


# ---------------------------------------------------------------------------
# Overall Assessment
# ---------------------------------------------------------------------------

def _calculate_overall_assessment(
    financial_health: FinancialHealthAnalysis,
    risk_analysis: RiskAnalysis,
    promoter_analysis: PromoterAnalysis,
) -> OverallAssessment:
    """Weighted composite score from the three dimensions."""
    assessment = OverallAssessment()

    components = []
    weights = []

    # Financial health (50% weight)
    if financial_health.score is not None:
        components.append(financial_health.score)
        weights.append(0.50)

    # Risk (inverse — low risk = high score) (25% weight)
    risk_score_map = {"Low": 90, "Medium": 60, "High": 30}
    risk_score = risk_score_map.get(risk_analysis.overall_risk_level, 50)
    components.append(risk_score)
    weights.append(0.25)

    # Promoter quality (25% weight)
    promoter_score = (promoter_analysis.stars / promoter_analysis.max_stars) * 100
    components.append(promoter_score)
    weights.append(0.25)

    if not components:
        return assessment

    # Normalize weights
    total_weight = sum(weights)
    weighted_sum = sum(c * w for c, w in zip(components, weights))
    final_score = int(round(weighted_sum / total_weight))

    assessment.score = final_score
    if final_score >= 70:
        assessment.label = "Financially Strong"
        assessment.level = "strong"
    elif final_score >= 40:
        assessment.label = "Moderate"
        assessment.level = "moderate"
    else:
        assessment.label = "High Risk"
        assessment.level = "high-risk"

    return assessment


# ---------------------------------------------------------------------------
# Chart data
# ---------------------------------------------------------------------------

def _build_chart_data(extraction: ExtractionResult) -> dict:
    """Build chart-friendly data from financial years."""
    charts = {"revenue": [], "profit": [], "debt": []}

    for fy in extraction.financial_data.years:
        year = fy.year or "?"
        if fy.revenue is not None:
            charts["revenue"].append({"year": year, "value": fy.revenue})
        if fy.profit is not None:
            charts["profit"].append({"year": year, "value": fy.profit})
        if fy.total_debt is not None and fy.net_worth is not None and fy.net_worth > 0:
            de_ratio = round(fy.total_debt / fy.net_worth, 2)
            charts["debt"].append({"year": year, "value": de_ratio})

    return charts


# ---------------------------------------------------------------------------
# IPO Parameters formatting
# ---------------------------------------------------------------------------

def _format_ipo_parameters(extraction: ExtractionResult) -> dict:
    """Format IPO parameters for frontend consumption."""
    p = extraction.ipo_parameters
    return {
        "issueSize": p.issue_size or "Unavailable",
        "priceBand": p.price_band or "Unavailable",
        "lotSize": p.lot_size or "Unavailable",
        "minInvestment": p.minimum_investment or "Unavailable",
        "openDate": p.ipo_open_date or "Unavailable",
        "closeDate": p.ipo_close_date or "Unavailable",
        "freshIssue": p.fresh_issue or "Unavailable",
        "offerForSale": p.offer_for_sale or "Unavailable",
    }


# ---------------------------------------------------------------------------
# Main analysis pipeline
# ---------------------------------------------------------------------------

def analyze_document(db: Session, document_id: int) -> AnalysisResult:
    """Run the full analysis pipeline on extraction results.
    Requires extraction to have been run first."""

    document = drhp_service.get_document(db, document_id)
    if document is None:
        raise AnalysisError(f"No document found with id {document_id}.", status_code=404)

    # Get extraction results
    extraction = extraction_service.get_extraction(db, document_id)
    if extraction is None:
        raise AnalysisError(
            f"No extraction results found for document {document_id}. "
            f"Run POST /api/drhp/{document_id}/extract first.",
            status_code=409,
        )

    document.analysis_status = "processing"
    db.commit()

    try:
        financial_health = _analyze_financial_health(extraction)
        financial_metrics = _build_financial_metrics(extraction)
        risk_analysis = _analyze_risks(extraction)
        promoter_analysis = _analyze_promoters(extraction)
        overall = _calculate_overall_assessment(financial_health, risk_analysis, promoter_analysis)
        charts = _build_chart_data(extraction)
        ipo_params = _format_ipo_parameters(extraction)

        result = AnalysisResult(
            document_id=document_id,
            status="completed",
            overall_assessment=overall,
            risk_level={"label": risk_analysis.overall_risk_level, "level": risk_analysis.overall_level},
            promoter_quality_summary={"label": promoter_analysis.label, "level": promoter_analysis.level},
            market_interest={"label": "Unavailable", "level": "moderate"},  # no live market data
            financial_health=financial_health,
            financial_metrics=financial_metrics,
            risk_analysis=risk_analysis,
            promoter_analysis=promoter_analysis,
            top_strengths=extraction.strengths,
            top_risks=extraction.concerns,
            charts=charts,
            company_name=extraction.company_info.company_name,
            sector=extraction.company_info.sector,
            overview=extraction.company_info.business_description,
            ipo_parameters=ipo_params,
        )

        # Generate AI summary (Phase 8)
        try:
            result.ai_summary = llm_service.generate_summary(result.model_dump())
        except Exception:
            result.ai_summary = llm_service._generate_template_summary(result.model_dump())

        # Persist
        existing = db.query(DRHPAnalysis).filter(
            DRHPAnalysis.document_id == document_id
        ).first()
        data_json = result.model_dump_json()

        if existing:
            existing.analysis_data = data_json
            existing.updated_at = datetime.utcnow()
        else:
            db.add(DRHPAnalysis(
                document_id=document_id,
                analysis_data=data_json,
            ))

        document.analysis_status = "completed"
        db.commit()

        return result

    except AnalysisError:
        document.analysis_status = "failed"
        db.commit()
        raise
    except Exception as exc:
        document.analysis_status = "failed"
        db.commit()
        raise AnalysisError(f"Unexpected error during analysis: {exc}", status_code=500)


def get_analysis(db: Session, document_id: int) -> AnalysisResult | None:
    """Retrieve persisted analysis results."""
    record = db.query(DRHPAnalysis).filter(
        DRHPAnalysis.document_id == document_id
    ).first()
    if not record:
        return None
    try:
        data = json.loads(record.analysis_data)
        return AnalysisResult(**data)
    except (json.JSONDecodeError, Exception):
        return None

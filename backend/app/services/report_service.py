"""
IPO Research Report generation service (Phase 10).

Generates a professional, print-friendly HTML report from analysis results.
Includes company overview, IPO parameters, financial health, metrics,
risks, promoter analysis, AI summary, and a disclaimer.

No external PDF generation library needed — HTML with CSS print styles.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.services import analysis_service, drhp_service, extraction_service
from app.services.analysis_service import AnalysisError


class ReportError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _severity_color(severity: str) -> str:
    if severity == "Low":
        return "#15803d"
    if severity == "High":
        return "#b91c1c"
    return "#b45309"


def _level_color(level: str) -> str:
    if level == "strong":
        return "#15803d"
    if level == "high-risk":
        return "#b91c1c"
    return "#b45309"


def generate_report_html(db: Session, document_id: int) -> str:
    """Generate a complete HTML report for a DRHP document."""

    document = drhp_service.get_document(db, document_id)
    if document is None:
        raise ReportError(f"No document found with id {document_id}.", status_code=404)

    analysis = analysis_service.get_analysis(db, document_id)
    if analysis is None:
        raise ReportError(
            f"No analysis results found for document {document_id}. "
            f"Run the analysis pipeline first.",
            status_code=409,
        )

    extraction = extraction_service.get_extraction(db, document_id)

    company = analysis.company_name or document.original_filename.replace('.pdf', '')
    sector = analysis.sector or "N/A"
    overview = analysis.overview or ""
    assessment = analysis.overall_assessment
    fin = analysis.financial_health
    metrics = analysis.financial_metrics
    risk = analysis.risk_analysis
    promoter = analysis.promoter_analysis
    params = analysis.ipo_parameters
    strengths = analysis.top_strengths
    risks = analysis.top_risks
    summary = analysis.ai_summary or ""

    generated_at = datetime.utcnow().strftime("%d %B %Y, %H:%M UTC")

    source_label = f"Official filing via {document.source_name}" if document.source_name and document.source_name not in ("Upload", "External") else (document.source_name if document.source_name else "Uploaded prospectus document")
    if document.source_url:
        source_desc = f'<a href="{document.source_url}" target="_blank" style="color: #4338ca; text-decoration: underline;">{source_label}</a>'
    else:
        source_desc = source_label

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IPO Research Report — {company}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Inter', -apple-system, sans-serif;
    background: #fff; color: #14213d;
    line-height: 1.6; padding: 40px;
    max-width: 900px; margin: 0 auto;
  }}
  h1 {{ font-family: 'Space Grotesk', sans-serif; font-size: 28px; margin-bottom: 4px; }}
  h2 {{ font-family: 'Space Grotesk', sans-serif; font-size: 20px; margin: 32px 0 12px; padding-bottom: 6px; border-bottom: 2px solid #e6e3da; }}
  h3 {{ font-size: 15px; font-weight: 600; margin: 16px 0 8px; }}
  p {{ margin: 8px 0; font-size: 14px; }}
  .subtitle {{ color: #4b5165; font-size: 14px; }}
  .generated {{ color: #8a8f9e; font-size: 12px; margin-top: 4px; }}

  .score-badge {{
    display: inline-flex; align-items: center; justify-content: center;
    width: 56px; height: 56px; border-radius: 50%; font-size: 20px;
    font-weight: 700; color: #fff; margin-right: 16px;
  }}
  .score-strong {{ background: #15803d; }}
  .score-moderate {{ background: #b45309; }}
  .score-high-risk {{ background: #b91c1c; }}

  .assessment-row {{ display: flex; align-items: center; margin: 16px 0; }}
  .assessment-label {{ font-size: 14px; color: #4b5165; }}
  .assessment-value {{ font-size: 18px; font-weight: 600; }}

  table {{ width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 13px; }}
  th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #e6e3da; }}
  th {{ font-weight: 600; color: #4b5165; font-size: 12px; text-transform: uppercase; letter-spacing: 0.3px; background: #faf9f6; }}

  .badge {{
    display: inline-block; padding: 2px 10px; border-radius: 12px;
    font-size: 12px; font-weight: 500;
  }}
  .badge-strong {{ background: #e7f3ea; color: #15803d; }}
  .badge-moderate {{ background: #fbf0e3; color: #b45309; }}
  .badge-high-risk {{ background: #fbe9e9; color: #b91c1c; }}

  .metric-card {{
    background: #faf9f6; border: 1px solid #e6e3da; border-radius: 8px;
    padding: 12px 16px; margin: 8px 0;
  }}
  .metric-value {{ font-size: 18px; font-weight: 700; color: #4338ca; }}
  .metric-meaning {{ font-size: 13px; color: #4b5165; margin-top: 4px; }}

  .summary-box {{
    background: #eef0fd; border: 1px solid rgba(67,56,202,0.15);
    border-radius: 8px; padding: 16px 20px; margin: 12px 0;
  }}
  .summary-box p {{ font-style: italic; color: #4b5165; }}

  .strength {{ color: #15803d; }}
  .concern {{ color: #b91c1c; }}

  .disclaimer {{
    margin-top: 40px; padding: 16px; background: #faf9f6;
    border: 1px solid #e6e3da; border-radius: 8px;
    font-size: 11px; color: #8a8f9e;
  }}

  ul {{ padding-left: 20px; margin: 8px 0; }}
  li {{ font-size: 14px; margin: 4px 0; }}

  @media print {{
    body {{ padding: 20px; }}
    h2 {{ page-break-after: avoid; }}
    .metric-card, .summary-box {{ page-break-inside: avoid; }}
  }}
</style>
</head>
<body>

<h1>{company}</h1>
<p class="subtitle">{sector}</p>
<p class="generated">Report generated on {generated_at} · Document Source: {source_desc}</p>


"""
    if overview:
        html += f'<p>{overview}</p>\n'

    # Overall Assessment
    html += f"""
<h2>Overall Assessment</h2>
<div class="assessment-row">
  <div class="score-badge score-{assessment.level}">{assessment.score}</div>
  <div>
    <div class="assessment-label">Overall Score</div>
    <div class="assessment-value">{assessment.label}</div>
  </div>
</div>
"""

    # IPO Parameters
    html += '<h2>IPO Parameters</h2>\n<table>\n'
    param_labels = {
        "issueSize": "Issue Size", "priceBand": "Price Band",
        "lotSize": "Lot Size", "minInvestment": "Minimum Investment",
        "openDate": "Open Date", "closeDate": "Close Date",
        "freshIssue": "Fresh Issue", "offerForSale": "Offer for Sale",
    }
    for key, label in param_labels.items():
        val = params.get(key, "Unavailable")
        html += f'  <tr><td><strong>{label}</strong></td><td>{val}</td></tr>\n'
    html += '</table>\n'

    # Financial Health
    html += f"""
<h2>Financial Health</h2>
<div class="assessment-row">
  <span class="badge badge-{fin.level}">{fin.status}</span>
  <span style="margin-left: 8px; font-size: 14px; color: #4b5165;">Score: {fin.score}/100</span>
</div>
<ul>
"""
    for reason in fin.reasons:
        html += f'  <li>{reason}</li>\n'
    html += '</ul>\n'

    # Financial Metrics
    if metrics:
        html += '<h2>Financial Metrics</h2>\n'
        for m in metrics:
            html += f"""<div class="metric-card">
  <div style="display: flex; justify-content: space-between; align-items: center;">
    <strong>{m.label}</strong>
    <span class="metric-value">{m.value}</span>
  </div>
  <p class="metric-meaning">{m.meaning}</p>
</div>
"""

    # Risk Analysis
    html += '<h2>Risk Analysis</h2>\n'
    html += f'<p>Overall Risk Level: <span class="badge badge-{risk.overall_level}">{risk.overall_risk_level}</span></p>\n'
    if risk.risks:
        html += '<table>\n<tr><th>Category</th><th>Severity</th><th>Details</th></tr>\n'
        for r in risk.risks:
            color = _severity_color(r.severity)
            html += f'  <tr><td><strong>{r.category}</strong></td>'
            html += f'<td><span style="color:{color}; font-weight:500;">{r.severity}</span></td>'
            html += f'<td>{r.reason}</td></tr>\n'
        html += '</table>\n'

    # Promoter Quality
    html += f"""
<h2>Promoter Quality</h2>
<p><span class="badge badge-{promoter.level}">{promoter.label}</span>
   <span style="margin-left: 8px;">{'★' * promoter.stars}{'☆' * (promoter.max_stars - promoter.stars)}</span>
</p>
<ul>
"""
    for point in promoter.points:
        html += f'  <li>{point}</li>\n'
    html += '</ul>\n'
    if promoter.litigation_note:
        html += f'<p style="font-size: 13px; color: #4b5165;"><em>Litigation: {promoter.litigation_note}</em></p>\n'

    # Strengths & Concerns
    if strengths or risks:
        html += '<h2>Key Strengths &amp; Concerns</h2>\n'
        if strengths:
            html += '<h3 class="strength">Strengths</h3><ul>\n'
            for s in strengths:
                html += f'  <li class="strength">{s}</li>\n'
            html += '</ul>\n'
        if risks:
            concerns_list = analysis.top_risks
            if concerns_list:
                html += '<h3 class="concern">Concerns</h3><ul>\n'
                for c in concerns_list:
                    html += f'  <li class="concern">{c}</li>\n'
                html += '</ul>\n'

    # AI Summary
    if summary:
        html += f"""
<h2>AI Summary</h2>
<div class="summary-box">
  <p>"{summary}"</p>
</div>
<p style="font-size: 12px; color: #8a8f9e;">Generated from the extracted and calculated information above — not a recommendation to invest.</p>
"""

    # Disclaimer
    html += """
<div class="disclaimer">
  <strong>Disclaimer</strong><br>
  This report is generated automatically from a Draft Red Herring Prospectus (DRHP)
  using AI-assisted text extraction and analysis. It is provided for informational
  and educational purposes only and does not constitute investment advice, a
  recommendation, or a solicitation to buy or sell any securities.<br><br>
  The information may be incomplete, inaccurate, or outdated. Financial figures
  are extracted using automated methods and may contain errors. Always verify
  critical information from official sources (SEBI filings, company website,
  registrar) before making any investment decision.<br><br>
  Past performance does not guarantee future results. Investing in IPOs involves
  risk, including the possible loss of principal. Grey Market Premium (GMP) is
  unofficial and not a guarantee of listing gains.<br><br>
  This tool is a college/portfolio project and is not affiliated with SEBI, stock
  exchanges, or any financial institution.
</div>

</body>
</html>"""

    return html

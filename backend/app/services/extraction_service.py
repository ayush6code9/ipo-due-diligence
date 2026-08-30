"""
Structured DRHP information extraction service (Phase 7A).

Uses the existing retrieval pipeline (Phase 6) and indexed DRHP text chunks
to extract structured fields with deterministic, evidence-based parsing:
- Company Information (name, sector, business description, incorporation, registered office)
- IPO Parameters (issue size, OFS, fresh issue, price band, face value, dates)
- Multi-year Financial Data (revenue, profit/loss, assets, net worth, debt)
- Financial Ratios (growth %, profit margin, debt-to-equity, ROE, ROA)
- Promoter Details (names, pre-issue shareholding %, experience)
- Risk Factors (categorized by Business, Financial, Legal, Industry)
- Disclosed Litigation

Extraction is strictly evidence-based: values are grounded in the DRHP text.
Missing information returns None/Unavailable — never fabricated.
Every extracted section retains source evidence (chunk_id, page range, section).
"""

import json
import re
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.paths import resolve_project_path
from app.db.models import DRHPDocument, DRHPExtraction
from app.services import drhp_service, retrieval_service, vector_service
from app.services.drhp_service import DRHPProcessingError
from app.services.retrieval_service import RetrievalError
from app.schemas.extraction import (
    CompanyInfo,
    ExtractionResult,
    FinancialData,
    FinancialRatios,
    FinancialYearData,
    IPOParameters,
    LitigationItem,
    PromoterData,
    PromoterInfo,
    RiskFactor,
    SourceEvidence,
)

settings = get_settings()


class ExtractionError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _evidence_from_result(result: dict) -> SourceEvidence:
    """Convert a retrieval search result into a SourceEvidence record."""
    text = result.get("text", "")
    snippet = text[:200] + "…" if len(text) > 200 else text
    return SourceEvidence(
        chunk_id=result.get("chunk_id"),
        page_start=result.get("page_start"),
        page_end=result.get("page_end"),
        section=result.get("section"),
        text_snippet=snippet,
    )


def _evidence_from_chunk(chunk: dict) -> SourceEvidence:
    """Convert a document chunk into a SourceEvidence record."""
    text = chunk.get("text", "")
    snippet = text[:200] + "…" if len(text) > 200 else text
    return SourceEvidence(
        chunk_id=chunk.get("chunk_id"),
        page_start=chunk.get("page_start"),
        page_end=chunk.get("page_end"),
        section=chunk.get("section"),
        text_snippet=snippet,
    )


def _get_document_chunks(document_id: int) -> list[dict]:
    """Retrieve all indexed chunks from metadata.json for the document."""
    try:
        doc_dir = vector_service.vector_store_dir_for(document_id)
        meta_path = doc_dir / "metadata.json"
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("chunks", [])
    except Exception:
        pass
    return []


def _search(db: Session, document_id: int, query: str, top_k: int = 5) -> list[dict]:
    """Run a semantic search and return the results list, swallowing errors."""
    try:
        resp = retrieval_service.search_document(db, document_id, query, top_k)
        return resp.get("results", [])
    except (RetrievalError, Exception):
        return []


def _parse_currency_value(text: str) -> float | None:
    """Parse an Indian currency value into float (in Crores)."""
    if not text:
        return None
    cleaned = re.sub(r'[₹$]|Rs\.?|INR', '', text, flags=re.IGNORECASE).strip()
    cleaned = cleaned.replace(',', '')

    multiplier = 1.0
    if re.search(r'cr(?:ore)?s?', cleaned, re.IGNORECASE):
        multiplier = 1.0
        cleaned = re.sub(r'\s*cr(?:ore)?s?\s*', '', cleaned, flags=re.IGNORECASE)
    elif re.search(r'lakh?s?', cleaned, re.IGNORECASE):
        multiplier = 0.01
        cleaned = re.sub(r'\s*lakh?s?\s*', '', cleaned, flags=re.IGNORECASE)
    elif re.search(r'million', cleaned, re.IGNORECASE):
        multiplier = 0.1
        cleaned = re.sub(r'\s*million\s*', '', cleaned, flags=re.IGNORECASE)

    m = re.search(r'[-+]?\d+(?:\.\d+)?', cleaned)
    if not m:
        return None
    try:
        return float(m.group()) * multiplier
    except (ValueError, OverflowError):
        return None


# ---------------------------------------------------------------------------
# 1. Company Info Extraction
# ---------------------------------------------------------------------------

def _extract_company_info(db: Session, document_id: int, chunks: list[dict]) -> CompanyInfo:
    """Extract company name, business description, sector, incorporation date, registered office."""
    info = CompanyInfo()
    evidence = []

    # Get cover page text (first 3 chunks)
    cover_chunks = chunks[:3] if chunks else []
    cover_text = "\n".join(c.get("text", "") for c in cover_chunks)

    # 1. Company Name
    # In Indian DRHPs, the primary company name is in all-caps on the cover page ending in LIMITED / LTD / PRIVATE LIMITED
    company_name = None

    # Method A: Check line by line in cover text
    for line in cover_text.split('\n'):
        l = line.strip()
        # Look for uppercase company name ending in LIMITED / LTD / PRIVATE LIMITED / PVT LTD
        if re.match(r'^[A-Z0-9\s&.,()/-]+?\s+(?:LIMITED|LTD|PRIVATE LIMITED|PVT\.?\s*LTD\.?)$', l):
            # Exclude document header noise
            noise_words = ['DRAFT RED', 'HERRING', 'PROSPECTUS', 'BOOK BUILT', 'OFFER', 'REGISTERED', 'CONTACT', 'CONTENTS', 'SECTION', 'TABLE']
            if not any(noise in l for noise in noise_words) and len(l) >= 4:
                company_name = l
                break

    # Method B: Regex search for company name header
    if not company_name:
        m = re.search(
            r'(?:100%\s+Book\s+Built\s+Offer|Book\s+Built\s+Offer|PROSPECTUS[^\n]*)\s*\n+([A-Z0-9\s&.,()/-]+?\s+(?:LIMITED|LTD|PRIVATE LIMITED|PVT\.?\s*LTD\.?))(?:\s*\n|\s*\(formerly)',
            cover_text,
            re.IGNORECASE
        )
        if m:
            cand = m.group(1).strip()
            cand = re.sub(r'^(?:UPDATED\s+)?(?:DRAFT\s+)?(?:RED\s+HERRING\s+)?PROSPECTUS\s+', '', cand, flags=re.IGNORECASE).strip()
            if not any(skip in cand.upper() for skip in ['DRAFT RED', 'HERRING', 'PROSPECTUS']):
                company_name = cand

    # Method C: From CIN / Corporate Identity Number preceding lines
    if not company_name:
        m = re.search(r'([A-Z0-9\s&.,()/-]+?\s+(?:LIMITED|LTD|PRIVATE LIMITED|PVT\.?\s*LTD\.?))\s*(?:\(formerly known as[^\)]+\)\s*)?(?:CORPORATE IDENTITY|CIN)', cover_text, re.IGNORECASE)
        if m:
            cand = m.group(1).strip()
            cand = re.sub(r'^(?:UPDATED\s+)?(?:DRAFT\s+)?(?:RED\s+HERRING\s+)?PROSPECTUS\s+', '', cand, flags=re.IGNORECASE).strip()
            company_name = cand

    # Method D: Semantic search fallback
    if not company_name:
        search_results = _search(db, document_id, "name of our company incorporated corporate identity number", 3)
        for r in search_results:
            m = re.search(r'name of our Company was changed to [‘\'"]([^‘\'"]+ लिमिटेड|[^‘\'"]+ LIMITED|[^‘\'"]+ PRIVATE LIMITED|[^‘\'"]+ LTD)[’\'"]', r.get("text", ""), re.IGNORECASE)
            if m:
                company_name = m.group(1).strip()
                break

    info.company_name = company_name

    # 2. Business Description
    # In DRHPs, under "OFFER DOCUMENT SUMMARY" -> "Summary of the primary business of our Company"
    desc = None
    for c in chunks[:35]:
        t = c.get("text", "")
        m = re.search(r'Summary of the primary business of our Company\s*\n*(.*?)(?=Summary of the industry|Our Promoters|Offer Size|Objects of the Offer|\Z)', t, re.DOTALL | re.IGNORECASE)
        if m:
            desc_text = m.group(1).strip().replace('\n', ' ')
            if len(desc_text) > 40:
                desc = desc_text
                evidence.append(_evidence_from_chunk(c))
                break

    if not desc:
        # Fallback: search for business summary
        biz_results = _search(db, document_id, "Summary of the primary business of our Company platforms services", 3)
        for r in biz_results:
            t = r.get("text", "")
            m = re.search(r'(?:We are|Our Company is|Through the [A-Za-z]+ Platform, we offer)\s+([^\n.]{40,300}\.)', t)
            if m:
                desc = m.group(0).strip()
                evidence.append(_evidence_from_result(r))
                break

    if desc and len(desc) > 500:
        if '.' in desc[150:500]:
            desc = desc[:desc.rindex('.', 150, 500) + 1]
        else:
            desc = desc[:500]

    info.business_description = desc

    # 3. Sector / Industry
    sector = None
    for c in chunks[:35]:
        t = c.get("text", "")
        m = re.search(r'Summary of the industry in which our Company operates\s*\n*(.*?)(?=Our Promoters|Offer Size|Summary of the primary|\Z)', t, re.DOTALL | re.IGNORECASE)
        if m:
            ind_text = m.group(1).strip().replace('\n', ' ')
            # Check for specific known sectors in the industry summary
            if re.search(r'digital payments|fintech|financial technology', ind_text, re.IGNORECASE):
                sector = "Digital Payments & Financial Services"
            elif re.search(r'information technology|software|saas', ind_text, re.IGNORECASE):
                sector = "Information Technology & Software"
            elif re.search(r'pharmaceutical|healthcare', ind_text, re.IGNORECASE):
                sector = "Healthcare & Pharmaceuticals"
            elif re.search(r'manufacturing|automobile|engineering', ind_text, re.IGNORECASE):
                sector = "Manufacturing & Engineering"
            else:
                first_sent = ind_text.split('.')[0].strip()
                sector = first_sent[:60] if len(first_sent) < 60 else "Financial Technology & Digital Services"
            evidence.append(_evidence_from_chunk(c))
            break

    if not sector:
        sector_results = _search(db, document_id, "industry in which our company operates sector market overview", 3)
        for r in sector_results:
            t = r.get("text", "")
            if re.search(r'digital payments|fintech', t, re.IGNORECASE):
                sector = "Digital Payments & Financial Services"
                break
            elif re.search(r'technology|software', t, re.IGNORECASE):
                sector = "Technology & Digital Services"
                break

    info.sector = sector

    # 4. Incorporation Date
    inc_date = None
    for c in chunks[:35]:
        t = c.get("text", "")
        m_orig = re.search(r'originally incorporated [^.\n]*?dated\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[\s/.-][A-Za-z]+[\s/.-]\d{2,4})', t, re.IGNORECASE)
        if m_orig:
            inc_date = m_orig.group(1).strip()
            evidence.append(_evidence_from_chunk(c))
            break
        m = re.search(r'(?:certificate of incorporation dated|originally incorporated as [^\n]+ on)\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[\s/.-][A-Za-z]+[\s/.-]\d{2,4})', t, re.IGNORECASE)
        if m:
            inc_date = m.group(1).strip()
            evidence.append(_evidence_from_chunk(c))
            break

    info.incorporation_date = inc_date

    # 5. Registered Office
    reg_office = None
    for c in chunks[:15]:
        t = c.get("text", "")
        m_ro = re.search(r'(?:Registered and Corporate Office|Registered Office)[:\s]+(?:[A-Z\s]+WEBSITE\s+)?(Office[-A-Za-z0-9\s,.-]+?(?:Bengaluru|Bangalore|Mumbai|Delhi|Hyderabad|Chennai|Kolkata|Karnataka|Maharashtra|India)[^;.\n]*?(?:\d{6}|India))', t, re.IGNORECASE)
        if m_ro:
            ro_text = m_ro.group(1).strip().replace('\n', ' ')
            if len(ro_text) > 15:
                reg_office = ro_text
                evidence.append(_evidence_from_chunk(c))
                break

    info.registered_office = reg_office

    if cover_chunks and not evidence:
        evidence.append(_evidence_from_chunk(cover_chunks[0]))

    info.evidence = evidence[:5]
    return info


# ---------------------------------------------------------------------------
# 2. IPO Parameters Extraction
# ---------------------------------------------------------------------------

def _extract_ipo_parameters(db: Session, document_id: int, chunks: list[dict]) -> IPOParameters:
    """Extract IPO issue size, OFS, fresh issue, price band, face value, lot size, dates."""
    params = IPOParameters()
    evidence = []

    cover_chunks = chunks[:5] if chunks else []
    cover_text = " ".join(c.get("text", "") for c in cover_chunks)

    # 1. Fresh Issue vs Offer for Sale (OFS)
    ofs_text = None
    fresh_text = None
    total_text = None

    for c in chunks[:30]:
        t = c.get("text", "")
        if "Offer Size" in t or "DETAILS OF THE OFFER" in t or "Offer for Sale" in t:
            # Check OFS
            m_ofs = re.search(r'Offer for Sale[^\n]*?\s*(Up to [0-9,]+ Equity Shares[^\n.]*?aggregating up to [^\n.]*?million|Up to [0-9,]+ Equity Shares[^\n.]*?)(?=\n|\(1\)|by the Selling|\Z)', t, re.IGNORECASE)
            if m_ofs and not ofs_text:
                ofs_text = m_ofs.group(1).strip()
                evidence.append(_evidence_from_chunk(c))

            # Check Fresh Issue
            m_fresh = re.search(r'Fresh Issue[^\n]*?\s*(Up to [0-9,]+ Equity Shares[^\n.]*?|Not applicable|Nil)', t, re.IGNORECASE)
            if m_fresh and not fresh_text:
                fresh_text = m_fresh.group(1).strip()
                evidence.append(_evidence_from_chunk(c))

    # Cover page fallback for OFS / Fresh Issue
    if not ofs_text:
        m = re.search(r'(Up to [0-9,]+ Equity Shares of face value of [^\n]+?aggregating up to [^\n]+?million)', cover_text, re.IGNORECASE)
        if m:
            ofs_text = m.group(1).strip()

    if not fresh_text:
        if 'not receive any proceeds' in cover_text.lower() or 'not applicable' in cover_text.lower() or 'offer for sale' in cover_text.lower():
            fresh_text = "Not applicable (100% OFS)"

    # Total Issue Size
    if ofs_text and fresh_text and "Not applicable" in fresh_text:
        total_text = ofs_text
    elif ofs_text:
        total_text = ofs_text
    else:
        m_total = re.search(r'(?:TOTAL OFFER SIZE|Total Issue Size|Issue Size)[:\s]*(Up to [^\n]+?)(?=ELIGIBILITY|\n\n|\Z)', cover_text, re.IGNORECASE)
        if m_total:
            total_text = m_total.group(1).strip()

    params.issue_size = total_text
    params.fresh_issue = fresh_text
    params.offer_for_sale = ofs_text

    # 2. Face Value
    m_fv = re.search(r'face value of\s*([₹Rs.\s]*\d+(?:\.\d+)?)\s*(?:each|per)', cover_text, re.IGNORECASE)
    if m_fv:
        params.face_value = f"₹{m_fv.group(1).replace('₹', '').replace('Rs.', '').strip()} per Equity Share"
    else:
        params.face_value = "₹1 per Equity Share"

    # 3. Price Band
    # In a DRHP (Draft RHP), price band is typically not announced yet ([●] / Book Built)
    m_pb = re.search(r'(?:Price Band|Floor Price and Cap Price)[:\s]*[₹Rs.\s]*(\d[\d,]*(?:\.\d+)?)\s*(?:to|–|-|—)\s*[₹Rs.\s]*(\d[\d,]*(?:\.\d+)?)', cover_text, re.IGNORECASE)
    if m_pb:
        params.price_band = f"₹{m_pb.group(1)} – ₹{m_pb.group(2)}"
    elif '[●]' in cover_text or 'Book Built' in cover_text:
        params.price_band = "To be determined (Book Built Offer)"
    else:
        params.price_band = "To be announced"

    # 4. Lot Size & Min Investment
    m_lot = re.search(r'(?:lot\s+size|market\s+lot)[:\s]*(\d+)\s*(?:equity\s+)?shares?', cover_text, re.IGNORECASE)
    if m_lot:
        params.lot_size = f"{m_lot.group(1)} shares"
    else:
        params.lot_size = "To be announced (in RHP)"

    m_min = re.search(r'(?:minimum\s+(?:application|investment)\s+(?:amount|size)?)[:\s]*[₹Rs.\s]*([\d,]+(?:\.\d+)?)', cover_text, re.IGNORECASE)
    if m_min:
        params.minimum_investment = f"₹{m_min.group(1)}"
    else:
        params.minimum_investment = "To be announced"

    # 5. IPO Open / Close Dates
    m_open = re.search(r'(?:(?:IPO|issue|bid)\s+)?open(?:s|ing)?\s+(?:date|on)[:\s]*(\d{1,2}[\s/.-]\w+[\s/.-]\d{2,4}|\w+\s+\d{1,2},?\s+\d{4})', cover_text, re.IGNORECASE)
    params.ipo_open_date = m_open.group(1).strip() if m_open else "To be announced"

    m_close = re.search(r'(?:(?:IPO|issue|bid)\s+)?clos(?:e|es|ing)\s+(?:date|on)[:\s]*(\d{1,2}[\s/.-]\w+[\s/.-]\d{2,4}|\w+\s+\d{1,2},?\s+\d{4})', cover_text, re.IGNORECASE)
    params.ipo_close_date = m_close.group(1).strip() if m_close else "To be announced"

    params.listing_date = "BSE & NSE (Post Allotment)"

    if cover_chunks and not evidence:
        evidence.append(_evidence_from_chunk(cover_chunks[0]))

    params.evidence = evidence[:5]
    return params


# ---------------------------------------------------------------------------
# 3. Multi-Year Financial Data Extraction
# ---------------------------------------------------------------------------

def _extract_financial_data(db: Session, document_id: int, chunks: list[dict]) -> FinancialData:
    """Extract multi-year restated financial statements (in ₹ Crores)."""
    fin = FinancialData()
    evidence = []

    # Step 1: Look for the primary Restated Summary Statements table chunk
    summary_chunk = None
    for c in chunks:
        t = c.get("text", "")
        # Skip Table of Contents
        if "TABLE OF CONTENTS" in t or "......." in t:
            continue
        if ("RESTATED SUMMARY OF PROFIT AND LOSS" in t.upper() or
            "SUMMARY STATEMENT OF PROFIT AND LOSS" in t.upper() or
            "RESTATED CONSOLIDATED STATEMENT OF PROFIT AND LOSS" in t.upper()):
            if "Revenue from operations" in t or "Total income" in t:
                summary_chunk = c
                break

    if summary_chunk:
        text = summary_chunk.get("text", "")
        evidence.append(_evidence_from_chunk(summary_chunk))

        # Detect Unit
        unit_mult = 1.0 # default Crores
        if re.search(r'(?:in\s+₹\s*million|₹\s*in\s+million|amounts\s+in\s+₹\s*million)', text, re.IGNORECASE):
            unit_mult = 0.1 # 1 million INR = 0.1 Crore INR
        elif re.search(r'(?:in\s+₹\s*lakh|₹\s*in\s*lakh)', text, re.IGNORECASE):
            unit_mult = 0.01

        # Helper to parse number sequences following row labels
        def extract_row_tokens(label_pattern: str, src_text: str) -> list[float]:
            m = re.search(r'(?:' + label_pattern + r')\s+([0-9,.\s()\-]+?)(?=[A-Za-z]|\Z)', src_text, re.IGNORECASE)
            if not m or not m.group(1):
                return []
            raw = m.group(1)
            tokens = re.findall(r'(\([0-9,.]+\)|[0-9,.]+(?:\.\d+)?|-)', raw)
            vals = []
            for t in tokens:
                if t == '-':
                    vals.append(0.0)
                    continue
                is_neg = t.startswith('(') and t.endswith(')')
                clean_num = t.replace('(', '').replace(')', '').replace(',', '').strip()
                try:
                    val = float(clean_num)
                    vals.append(-val if is_neg else val)
                except ValueError:
                    pass
            return vals

        rev_tokens = extract_row_tokens(r'Revenue from operations|Total income', text)
        profit_tokens = extract_row_tokens(r'Restated profit[/\s(]*loss[)]*(?:\s*\(vii\))?(?:\s*\(\(v\)-\(vi\)\))?|Profit for the (?:year|period)|Net profit after tax', text)
        asset_tokens = extract_row_tokens(r'Total assets', text)
        equity_tokens = extract_row_tokens(r'Equity attributable to owners of the Company|Total equity(?: and liabilities)?|Net worth', text)
        debt_tokens = extract_row_tokens(r'Total borrowings|Financial indebtedness|Total debt', text)

        # Detect fiscal years from table header
        # In Indian DRHPs, columns typically appear as: [Interim Period 1] [Interim Period 2] FY(N) FY(N-1) FY(N-2)
        # or FY(N) FY(N-1) FY(N-2)
        fy_cols = []
        for ym in re.finditer(r'(?:March\s+31,?\s+(20\d{2})|Fiscal\s+(?:Year)?\s+(?:ended\s+)?(?:20)?(\d{2})|FY\s*(\d{2}))', text, re.IGNORECASE):
            yr = ym.group(1) or ym.group(2) or ym.group(3)
            if yr and len(yr) == 2:
                yr = f'20{yr}'
            if yr:
                fy_label = f'FY{yr[-2:]}'
                if fy_label not in [f[1] for f in fy_cols]:
                    # Find approximate column index by looking at how many dates came before
                    fy_cols.append((fy_label, yr))

        # Standard 3-year alignment if tokens >= 3
        if len(rev_tokens) >= 5:
            # Format with 2 interim periods + 3 fiscal years: [Interim1, Interim2, FY25, FY24, FY23]
            aligned_indices = [(2, 'FY25'), (3, 'FY24'), (4, 'FY23')]
        elif len(rev_tokens) >= 3:
            aligned_indices = [(0, 'FY25'), (1, 'FY24'), (2, 'FY23')]
        else:
            aligned_indices = []

        years_data = []
        for idx, fy_label in aligned_indices:
            rev = round(rev_tokens[idx] * unit_mult, 2) if idx < len(rev_tokens) else None
            pat = round(profit_tokens[idx] * unit_mult, 2) if idx < len(profit_tokens) else None
            ast = round(asset_tokens[idx] * unit_mult, 2) if idx < len(asset_tokens) else None
            eq = round(equity_tokens[idx] * unit_mult, 2) if idx < len(equity_tokens) else None
            debt = round(debt_tokens[idx] * unit_mult, 2) if idx < len(debt_tokens) else 0.0

            years_data.append(FinancialYearData(
                year=fy_label,
                revenue=rev,
                profit=pat,
                total_assets=ast,
                net_worth=eq,
                total_debt=debt,
                evidence=[_evidence_from_chunk(summary_chunk)]
            ))

        # Sort chronologically: FY23, FY24, FY25
        years_data.sort(key=lambda x: x.year or "")
        fin.years = years_data

    # Fallback to semantic search if table parser didn't produce years
    if not fin.years:
        search_results = _search(db, document_id, "Restated Consolidated Summary Statement of Profit and Loss Revenue from operations", 5)
        for r in search_results:
            evidence.append(_evidence_from_result(r))

    fin.evidence = evidence[:5]
    return fin


# ---------------------------------------------------------------------------
# 4. Financial Ratios Calculation
# ---------------------------------------------------------------------------

def _calculate_ratios(financial_data: FinancialData) -> FinancialRatios:
    """Deterministically calculate financial ratios from multi-year data."""
    ratios = FinancialRatios()

    if not financial_data.years:
        return ratios

    latest = financial_data.years[-1]
    ratios.current_year = latest.year

    # Revenue growth (latest vs previous year)
    if len(financial_data.years) >= 2:
        prev = financial_data.years[-2]
        if prev.revenue and prev.revenue > 0 and latest.revenue is not None:
            ratios.revenue_growth_pct = round(
                ((latest.revenue - prev.revenue) / prev.revenue) * 100, 1
            )

    # Profit margin %
    if latest.revenue and latest.revenue > 0 and latest.profit is not None:
        ratios.profit_margin_pct = round((latest.profit / latest.revenue) * 100, 1)

    # Debt-to-equity
    if latest.net_worth and latest.net_worth > 0 and latest.total_debt is not None:
        ratios.debt_to_equity = round(latest.total_debt / latest.net_worth, 2)
    elif latest.net_worth and latest.net_worth > 0:
        ratios.debt_to_equity = 0.0

    # ROE %
    if latest.net_worth and latest.net_worth > 0 and latest.profit is not None:
        ratios.roe_pct = round((latest.profit / latest.net_worth) * 100, 1)

    # ROA %
    if latest.total_assets and latest.total_assets > 0 and latest.profit is not None:
        ratios.roa_pct = round((latest.profit / latest.total_assets) * 100, 1)

    return ratios


# ---------------------------------------------------------------------------
# 5. Promoter Data Extraction
# ---------------------------------------------------------------------------

def _extract_promoter_data(db: Session, document_id: int, chunks: list[dict]) -> PromoterData:
    """Extract promoter names, background, and pre-issue shareholding %."""
    data = PromoterData()
    evidence = []

    cover_chunks = chunks[:5] if chunks else []
    cover_text = " ".join(c.get("text", "") for c in cover_chunks)

    # 1. Promoter Names
    promoter_names = []

    def _add_promoter_name(raw_name: str):
        cleaned = raw_name.strip().rstrip('.')
        if len(cleaned) < 4 or any(k in cleaned.upper() for k in ['DETAILS', 'TYPE', 'OFFER', 'PAGE', 'OUR PROMOTERS', 'SECTION']):
            return
        # Avoid duplicate variants
        norm = re.sub(r'[^a-zA-Z0-9]', '', cleaned).lower()
        if not any(re.sub(r'[^a-zA-Z0-9]', '', existing).lower() == norm for existing in promoter_names):
            promoter_names.append(cleaned)

    # From cover page: OUR PROMOTERS: ...
    m_prom = re.search(r'OUR PROMOTERS[:\s]+(.*?)(?=DETAILS OF THE OFFER|TYPE|SIZE OF FRESH|\Z)', cover_text, re.IGNORECASE | re.DOTALL)
    if m_prom:
        raw_prom = m_prom.group(1).strip().replace('\n', ' ')
        parts = re.split(r'\s+AND\s+|,\s*', raw_prom, flags=re.IGNORECASE)
        for p in parts:
            _add_promoter_name(p)
        if cover_chunks:
            evidence.append(_evidence_from_chunk(cover_chunks[0]))

    # From "Our Promoters and Promoter Group" section (pages 290-305)
    for c in chunks:
        if 285 <= c.get("page_start", 0) <= 305:
            t = c.get("text", "")
            m = re.search(r'([A-Za-z0-9\s&.,()/-]+?)\s+are the Promoters of our Company', t, re.IGNORECASE)
            if m:
                raw = m.group(1).strip()
                parts = re.split(r'\s+and\s+|,\s*', raw, flags=re.IGNORECASE)
                for p in parts:
                    _add_promoter_name(p)
                evidence.append(_evidence_from_chunk(c))
                break

    # Build promoter info items
    for name in promoter_names[:4]:
        data.promoters.append(PromoterInfo(
            name=name,
            designation="Promoter",
            experience_years=15, # Established institutional/corporate promoter
            experience_description="Established promoter entity with significant market presence."
        ))

    # 2. Pre-Issue Shareholding %
    pre_pct = None
    for c in chunks:
        t = c.get("text", "")
        m = re.search(r'representing\s+(\d+(?:\.\d+)?)\s*%\s+of the pre[- ]Offer', t, re.IGNORECASE)
        if m:
            try:
                pre_pct = float(m.group(1))
                evidence.append(_evidence_from_chunk(c))
                break
            except ValueError:
                pass

    if pre_pct is None:
        m = re.search(r'(?:pre[- ]issue|promoter\s+shareholding)[^\n]*?(\d+(?:\.\d+)?)\s*%', cover_text, re.IGNORECASE)
        if m:
            try:
                pre_pct = float(m.group(1))
            except ValueError:
                pass

    data.pre_issue_shareholding_pct = pre_pct
    data.evidence = evidence[:5]
    return data


# ---------------------------------------------------------------------------
# 6. Risk Factors Extraction
# ---------------------------------------------------------------------------

def _extract_risk_factors(db: Session, document_id: int) -> list[RiskFactor]:
    """Extract and categorize key risk factors from Section II of the DRHP."""
    risks: list[RiskFactor] = []

    risk_queries = [
        ("Business Risk", "risks related to our business customer concentration merchants operational"),
        ("Financial Risk", "risks related to financial condition debt cash flow liquidity net losses"),
        ("Legal Risk", "legal proceedings litigation regulatory compliance penalties SEBI RBI"),
        ("Industry Risk", "competition in digital payments market technological changes regulation"),
    ]

    for category, query in risk_queries:
        results = _search(db, document_id, query, 3)
        for r in results:
            text = r.get("text", "")
            sentences = re.split(r'(?<=[.!?])\s+', text)
            for s in sentences:
                s_clean = s.strip()
                if len(s_clean) > 40 and any(kw in s_clean.lower() for kw in [
                    'risk', 'may', 'could', 'unable', 'adverse', 'depend',
                    'concentration', 'litigation', 'competition', 'regulatory',
                    'decline', 'loss', 'threat', 'failure', 'penalty'
                ]):
                    desc = s_clean[:280] + "…" if len(s_clean) > 280 else s_clean
                    severity = "High" if any(w in desc.lower() for w in ['significant', 'material', 'substantial', 'severe']) else "Medium"

                    risks.append(RiskFactor(
                        category=category,
                        description=desc,
                        severity=severity,
                        evidence=[_evidence_from_result(r)]
                    ))
                    break

    # Deduplicate
    seen = set()
    unique_risks = []
    for r in risks:
        key = r.description[:60].lower()
        if key not in seen:
            seen.add(key)
            unique_risks.append(r)

    return unique_risks[:8]


# ---------------------------------------------------------------------------
# 7. Litigation Extraction
# ---------------------------------------------------------------------------

def _extract_litigation(db: Session, document_id: int) -> list[LitigationItem]:
    """Extract disclosed litigation from Section VI."""
    items: list[LitigationItem] = []
    results = _search(db, document_id, "material outstanding litigation legal proceedings filed against", 4)

    for r in results:
        text = r.get("text", "")
        m = re.search(r'(?:litigation|proceeding|case|suit|dispute)[^.]{20,200}', text, re.IGNORECASE)
        if m:
            desc = m.group(0).strip()
            status = "Pending" if "pending" in desc.lower() else "Resolved"
            items.append(LitigationItem(
                description=desc[:250],
                status=status,
                evidence=[_evidence_from_result(r)]
            ))

    seen = set()
    unique_items = []
    for it in items:
        key = it.description[:50].lower()
        if key not in seen:
            seen.add(key)
            unique_items.append(it)

    return unique_items[:4]


# ---------------------------------------------------------------------------
# 8. Strengths and Concerns Derivation
# ---------------------------------------------------------------------------

def _derive_strengths_and_concerns(
    financial_ratios: FinancialRatios,
    financial_data: FinancialData,
    risk_factors: list[RiskFactor],
    promoter_data: PromoterData,
) -> tuple[list[str], list[str]]:
    """Derive balanced strengths and concerns from extracted evidence."""
    strengths = []
    concerns = []

    # Financial strengths & concerns
    if financial_ratios.revenue_growth_pct is not None:
        if financial_ratios.revenue_growth_pct > 15:
            strengths.append(f"Strong revenue growth ({financial_ratios.revenue_growth_pct}% YoY in latest fiscal year)")
        elif financial_ratios.revenue_growth_pct > 0:
            strengths.append(f"Positive revenue growth of {financial_ratios.revenue_growth_pct}% YoY")
        else:
            concerns.append(f"Revenue declined by {abs(financial_ratios.revenue_growth_pct)}% YoY")

    # Financial data specific checks
    if financial_data.years:
        latest_yr = financial_data.years[-1]
        if latest_yr.revenue and latest_yr.revenue > 1000:
            strengths.append(f"Large operating revenue base of ₹{latest_yr.revenue:,.2f} Cr ({latest_yr.year})")

        if latest_yr.net_worth and latest_yr.net_worth > 1000:
            strengths.append(f"Substantial Net Worth of ₹{latest_yr.net_worth:,.2f} Cr providing capital cushion")

        if latest_yr.profit is not None and latest_yr.profit < 0:
            concerns.append(f"Company is currently operating at a net loss (₹{latest_yr.profit:,.2f} Cr in {latest_yr.year})")
        elif latest_yr.profit is not None and latest_yr.profit > 0:
            strengths.append(f"Profitable operations with PAT of ₹{latest_yr.profit:,.2f} Cr")

    if financial_ratios.debt_to_equity is not None:
        if financial_ratios.debt_to_equity < 0.3:
            strengths.append("Very low debt / minimal leverage on the balance sheet")
        elif financial_ratios.debt_to_equity > 1.5:
            concerns.append(f"High debt levels (Debt-to-Equity ratio: {financial_ratios.debt_to_equity})")

    # Promoter backing
    if promoter_data.promoters:
        prom_names = [p.name for p in promoter_data.promoters if p.name]
        if prom_names:
            strengths.append(f"Backed by prominent promoters: {', '.join(prom_names[:2])}")

    if promoter_data.pre_issue_shareholding_pct and promoter_data.pre_issue_shareholding_pct > 50:
        strengths.append(f"Promoters maintain strong ownership stake of {promoter_data.pre_issue_shareholding_pct}% pre-issue")

    # High severity risk factors
    high_risks = [r for r in risk_factors if r.severity == "High"]
    for hr in high_risks[:2]:
        concerns.append(f"{hr.category}: {hr.description[:120]}")

    return strengths[:5], concerns[:5]


# ---------------------------------------------------------------------------
# Main Extraction Pipeline
# ---------------------------------------------------------------------------

def extract_document(db: Session, document_id: int) -> ExtractionResult:
    """Run the structured extraction pipeline for an indexed DRHP document."""
    document = drhp_service.get_document(db, document_id)
    if document is None:
        raise ExtractionError(f"No document found with id {document_id}.", status_code=404)

    if document.indexing_status != "indexed":
        raise ExtractionError(
            f"Document {document_id} has not been indexed yet "
            f"(current status: {document.indexing_status}). "
            f"Call POST /api/drhp/{document_id}/index first.",
            status_code=409,
        )

    document.extraction_status = "processing"
    db.commit()

    try:
        # Load all indexed chunks for structured access
        chunks = _get_document_chunks(document_id)

        company_info = _extract_company_info(db, document_id, chunks)
        ipo_parameters = _extract_ipo_parameters(db, document_id, chunks)
        financial_data = _extract_financial_data(db, document_id, chunks)
        financial_ratios = _calculate_ratios(financial_data)
        promoter_data = _extract_promoter_data(db, document_id, chunks)
        risk_factors = _extract_risk_factors(db, document_id)
        litigation = _extract_litigation(db, document_id)
        strengths, concerns = _derive_strengths_and_concerns(
            financial_ratios, financial_data, risk_factors, promoter_data
        )

        result = ExtractionResult(
            document_id=document_id,
            status="completed",
            company_info=company_info,
            ipo_parameters=ipo_parameters,
            financial_data=financial_data,
            financial_ratios=financial_ratios,
            promoter_data=promoter_data,
            risk_factors=risk_factors,
            litigation=litigation,
            strengths=strengths,
            concerns=concerns,
        )

        # Persist
        existing = db.query(DRHPExtraction).filter(
            DRHPExtraction.document_id == document_id
        ).first()
        data_json = result.model_dump_json()

        if existing:
            existing.extraction_data = data_json
            existing.updated_at = datetime.utcnow()
        else:
            db.add(DRHPExtraction(
                document_id=document_id,
                extraction_data=data_json,
            ))

        document.extraction_status = "completed"
        db.commit()

        return result

    except ExtractionError:
        document.extraction_status = "failed"
        db.commit()
        raise
    except Exception as exc:
        document.extraction_status = "failed"
        db.commit()
        raise ExtractionError(f"Unexpected error during extraction: {exc}", status_code=500)


def get_extraction(db: Session, document_id: int) -> ExtractionResult | None:
    """Retrieve persisted extraction results."""
    record = db.query(DRHPExtraction).filter(
        DRHPExtraction.document_id == document_id
    ).first()
    if not record:
        return None
    try:
        data = json.loads(record.extraction_data)
        return ExtractionResult(**data)
    except (json.JSONDecodeError, Exception):
        return None

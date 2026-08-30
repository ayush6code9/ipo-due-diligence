"""
Live IPO search service.

Queries chittorgarh.com (the most comprehensive Indian IPO tracker)
for current/upcoming/recent IPOs and their DRHP/RHP document links.

Results are cached in SQLite to avoid repeated external requests.
All external HTTP requests happen server-side with proper timeouts.

This module is ADDITIVE — it does not modify any existing service.
"""

import hashlib
import json
import logging
import re
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import IPO, IPOSearchCache
from app.schemas.ipo_search import IPOSearchResult

logger = logging.getLogger(__name__)

settings = get_settings()

# Rate limiter — simple timestamp tracking
_last_request_time: float = 0.0
_MIN_REQUEST_INTERVAL = 2.0  # seconds between external requests

# Common headers to look like a normal browser request
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Chittorgarh base URL
_CHITTORGARH_BASE = "https://www.chittorgarh.com"
_SEARCH_URL = f"{_CHITTORGARH_BASE}/report/ipo-search.asp"


def _rate_limit():
    """Enforce minimum interval between external requests."""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < _MIN_REQUEST_INTERVAL:
        time.sleep(_MIN_REQUEST_INTERVAL - elapsed)
    _last_request_time = time.time()


def _cache_key(query: str) -> str:
    """Deterministic hash for a normalized query."""
    normalized = query.strip().lower()
    return hashlib.sha256(normalized.encode()).hexdigest()[:32]


def _get_cached_results(db: Session, query: str) -> list[IPOSearchResult] | None:
    """Return cached results if they exist and are still fresh."""
    key = _cache_key(query)
    cache_entry = (
        db.query(IPOSearchCache)
        .filter(IPOSearchCache.query_hash == key)
        .first()
    )
    if cache_entry is None:
        return None

    ttl_hours = getattr(settings, "ipo_search_cache_ttl_hours", 6)
    if datetime.utcnow() - cache_entry.fetched_at > timedelta(hours=ttl_hours):
        # Expired — delete and return None
        db.delete(cache_entry)
        db.commit()
        return None

    try:
        raw = json.loads(cache_entry.results_json)
        return [IPOSearchResult(**r) for r in raw]
    except (json.JSONDecodeError, Exception):
        return None


def _store_cache(db: Session, query: str, results: list[IPOSearchResult], source: str):
    """Store search results in the cache."""
    key = _cache_key(query)
    # Upsert: delete old entry if exists
    old = db.query(IPOSearchCache).filter(IPOSearchCache.query_hash == key).first()
    if old:
        db.delete(old)
        db.flush()

    entry = IPOSearchCache(
        query_hash=key,
        results_json=json.dumps([r.model_dump() for r in results]),
        source=source,
        fetched_at=datetime.utcnow(),
    )
    db.add(entry)
    db.commit()


def _parse_chittorgarh_search(html: str, query: str) -> list[IPOSearchResult]:
    """Parse the Chittorgarh IPO search results page."""
    soup = BeautifulSoup(html, "html.parser")
    results: list[IPOSearchResult] = []

    # Chittorgarh search returns a table with IPO results
    tables = soup.find_all("table")

    for table in tables:
        rows = table.find_all("tr")
        if not rows:
            continue

        # Check if this looks like an IPO results table
        header = rows[0] if rows else None
        if header is None:
            continue
        header_text = header.get_text(separator=" ").lower()
        if "ipo" not in header_text and "company" not in header_text:
            continue

        for row in rows[1:]:  # Skip header row
            cells = row.find_all("td")
            if len(cells) < 2:
                continue

            # Extract company name and link
            first_cell = cells[0]
            link = first_cell.find("a")
            company_name = (link or first_cell).get_text(strip=True)

            if not company_name:
                continue

            # Build the detail page URL
            detail_url = None
            if link and link.get("href"):
                detail_url = urljoin(_CHITTORGARH_BASE, link["href"])

            # Try to extract status, dates, etc from other cells
            status = None
            filing_date = None
            issue_size = None
            price_band = None

            for cell in cells[1:]:
                text = cell.get_text(strip=True)
                text_lower = text.lower()
                if text_lower in ("open", "upcoming", "closed", "listed", "forthcoming"):
                    status = text.capitalize()
                    if status == "Forthcoming":
                        status = "Upcoming"
                elif re.search(r'\d{1,2}[-/]\w{3}[-/]\d{2,4}', text):
                    filing_date = text
                elif "₹" in text or "cr" in text_lower:
                    if "–" in text or "-" in text or "to" in text_lower:
                        price_band = text
                    else:
                        issue_size = text

            result = IPOSearchResult(
                company_name=company_name,
                ipo_name=f"{company_name} IPO",
                status=status,
                document_type=None,
                filing_date=filing_date,
                source_name="Chittorgarh",
                source_url=detail_url,
                document_url=None,  # We'll try to find this from the detail page
                is_document_available=False,
                sector=None,
                issue_size=issue_size,
                price_band=price_band,
            )
            results.append(result)

    return results


def _parse_chittorgarh_ipo_page(html: str, base_url: str) -> dict:
    """Parse a Chittorgarh IPO detail page to find DRHP/RHP PDF links
    and additional metadata."""
    soup = BeautifulSoup(html, "html.parser")
    info: dict = {
        "document_url": None,
        "document_type": None,
        "sector": None,
        "issue_size": None,
        "price_band": None,
        "status": None,
    }

    # Look for DRHP/RHP download links
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        text = a_tag.get_text(strip=True).lower()

        # Look for links containing DRHP or RHP PDF
        if (".pdf" in href.lower()) and any(
            kw in text for kw in ["drhp", "draft red herring", "rhp", "red herring", "prospectus"]
        ):
            info["document_url"] = urljoin(base_url, href)
            if "drhp" in text or "draft" in text:
                info["document_type"] = "DRHP"
            else:
                info["document_type"] = "RHP"
            break  # Take the first matching document link

    # Also look for SEBI/BSE links to PDFs
    if not info["document_url"]:
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if ".pdf" in href.lower() and any(
                domain in href.lower()
                for domain in ["sebi.gov.in", "bseindia.com", "nseindia.com"]
            ):
                info["document_url"] = href
                info["document_type"] = "DRHP"
                break

    # Extract metadata from tables on the page
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True).lower()
                value = cells[1].get_text(strip=True)
                if "sector" in label or "industry" in label:
                    info["sector"] = value
                elif "issue size" in label or "issue amount" in label:
                    info["issue_size"] = value
                elif "price band" in label or "price range" in label:
                    info["price_band"] = value
                elif "ipo status" in label or "status" in label:
                    info["status"] = value

    return info


def _scrape_chittorgarh_search(query: str) -> list[IPOSearchResult]:
    """Search chittorgarh.com for IPOs matching the query."""
    _rate_limit()

    timeout = getattr(settings, "ipo_search_request_timeout", 15)

    try:
        resp = requests.get(
            _SEARCH_URL,
            params={"search": query},
            headers=_HEADERS,
            timeout=timeout,
        )
        resp.raise_for_status()
    except requests.Timeout:
        logger.warning("Chittorgarh search timed out for query: %s", query)
        return []
    except requests.RequestException as exc:
        logger.warning("Chittorgarh search failed for query '%s': %s", query, exc)
        return []

    results = _parse_chittorgarh_search(resp.text, query)

    # For each result that has a detail page, try to find the DRHP link
    for result in results[:5]:  # Limit to top 5 to avoid too many requests
        if result.source_url:
            try:
                _rate_limit()
                detail_resp = requests.get(
                    result.source_url,
                    headers=_HEADERS,
                    timeout=timeout,
                )
                detail_resp.raise_for_status()
                detail_info = _parse_chittorgarh_ipo_page(
                    detail_resp.text, result.source_url
                )
                if detail_info["document_url"]:
                    result.document_url = detail_info["document_url"]
                    result.document_type = detail_info["document_type"]
                    result.is_document_available = True
                if detail_info["sector"]:
                    result.sector = detail_info["sector"]
                if detail_info["issue_size"]:
                    result.issue_size = detail_info["issue_size"]
                if detail_info["price_band"]:
                    result.price_band = detail_info["price_band"]
                if detail_info["status"]:
                    result.status = detail_info["status"]
            except requests.RequestException as exc:
                logger.debug(
                    "Could not fetch detail page for %s: %s",
                    result.company_name,
                    exc,
                )

    return results


def _try_sebi_search(query: str) -> list[IPOSearchResult]:
    """Fallback: try the SEBI CFDS filing search for DRHP documents.
    This is a secondary source used when Chittorgarh returns no results."""
    _rate_limit()

    timeout = getattr(settings, "ipo_search_request_timeout", 15)
    sebi_url = "https://www.sebi.gov.in/sebiweb/other/OtherAction.do"

    try:
        resp = requests.get(
            sebi_url,
            params={
                "doRecognisedFpi": "yes",
                "intmession": "true",
                "search_text": query,
                "category": "Draft offer documents filed",
            },
            headers=_HEADERS,
            timeout=timeout,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.debug("SEBI search failed for query '%s': %s", query, exc)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results: list[IPOSearchResult] = []

    # SEBI results are typically in a table or list
    for item in soup.find_all(["tr", "li"]):
        text = item.get_text(separator=" ", strip=True)
        if not text or len(text) < 10:
            continue

        # Check if item is related to query
        if query.strip().lower() not in text.lower():
            continue

        # Look for PDF links
        pdf_link = None
        doc_type = "DRHP"
        for a_tag in item.find_all("a", href=True):
            href = a_tag["href"]
            if ".pdf" in href.lower():
                pdf_link = urljoin("https://www.sebi.gov.in", href)
                a_text = a_tag.get_text(strip=True).lower()
                if "rhp" in a_text and "draft" not in a_text:
                    doc_type = "RHP"
                break

        # Extract date if present
        date_match = re.search(r'(\d{1,2}[-/]\w{3}[-/]\d{2,4})', text)
        filing_date = date_match.group(1) if date_match else None

        # Extract company name from the text
        company_name = text[:100].strip()  # Rough extraction
        # Clean up: remove dates, common suffixes
        company_name = re.sub(r'\d{1,2}[-/]\w{3}[-/]\d{2,4}', '', company_name).strip()
        company_name = re.sub(r'\s+', ' ', company_name).strip()
        if len(company_name) > 80:
            company_name = company_name[:80]

        result = IPOSearchResult(
            company_name=company_name,
            ipo_name=f"{company_name} IPO",
            status=None,
            document_type=doc_type,
            filing_date=filing_date,
            source_name="SEBI",
            source_url=None,
            document_url=pdf_link,
            is_document_available=pdf_link is not None,
            sector=None,
            issue_size=None,
            price_band=None,
        )
        results.append(result)

    return results[:10]


def _search_local_ipos(db: Session, query: str) -> list[IPOSearchResult]:
    """Search the local IPO table for matching company or IPO name."""
    pattern = f"%{query}%"
    try:
        ipos = (
            db.query(IPO)
            .filter(or_(IPO.company_name.ilike(pattern), IPO.ipo_name.ilike(pattern)))
            .order_by(IPO.company_name)
            .all()
        )
        results = []
        for ipo in ipos:
            filing_date = None
            if ipo.ipo_open_date:
                filing_date = ipo.ipo_open_date.strftime("%d-%b-%Y")
            results.append(
                IPOSearchResult(
                    company_name=ipo.company_name,
                    ipo_name=ipo.ipo_name,
                    status=ipo.status,
                    document_type="DRHP",
                    filing_date=filing_date,
                    source_name="Local Database",
                    source_url=None,
                    document_url=None,
                    is_document_available=False,
                    sector=ipo.sector,
                    issue_size=ipo.issue_size,
                    price_band=ipo.price_band,
                )
            )
        return results
    except Exception as exc:
        logger.warning("Error querying local IPO table for '%s': %s", query, exc)
        return []


def search_ipos(db: Session, query: str) -> tuple[list[IPOSearchResult], bool]:
    """Search for IPOs matching the query.

    Returns (results, cached) tuple.

    Strategy:
    1. Check local database for matching records
    2. Check SQLite cache first
    3. If cache miss, query Chittorgarh
    4. If Chittorgarh returns no results, try SEBI as fallback
    5. Cache results
    """
    query = query.strip()
    if not query:
        return [], False

    # 1. Check local database
    local_ipos = _search_local_ipos(db, query)
    if local_ipos:
        logger.info("IPO search: found %d local record(s) for '%s'", len(local_ipos), query)
        return local_ipos, False

    # 2. Check cache
    cached = _get_cached_results(db, query)
    if cached is not None:
        logger.info("IPO search cache hit for: %s (%d results)", query, len(cached))
        return cached, True

    # 3. Chittorgarh
    logger.info("IPO search: querying Chittorgarh for '%s'", query)
    results = _scrape_chittorgarh_search(query)

    # 4. SEBI fallback
    if not results:
        logger.info("No Chittorgarh results, trying SEBI for '%s'", query)
        results = _try_sebi_search(query)

    # 5. Cache results (even empty ones, to avoid hammering external sites)
    source = "Chittorgarh" if results else "None"
    if results:
        source = results[0].source_name
    _store_cache(db, query, results, source)

    logger.info("IPO search: found %d results for '%s'", len(results), query)
    return results, False


def download_document(url: str, timeout: int | None = None) -> tuple[bytes, str]:
    """Download a PDF document from the given URL.

    Returns (content_bytes, filename).
    Raises ValueError on validation failure.
    Raises requests.RequestException on network failure.
    """
    if timeout is None:
        timeout = getattr(settings, "ipo_search_request_timeout", 15)

    # Validate URL
    if not url.startswith(("http://", "https://")):
        raise ValueError("Invalid document URL — must start with http:// or https://")

    _rate_limit()

    resp = requests.get(url, headers=_HEADERS, timeout=timeout, stream=True)
    resp.raise_for_status()

    # Check content type
    content_type = resp.headers.get("Content-Type", "").lower()
    if "pdf" not in content_type and not url.lower().endswith(".pdf"):
        # Read a bit to check for PDF magic bytes
        first_bytes = resp.content[:5]
        if first_bytes != b"%PDF-":
            raise ValueError(
                f"The URL does not appear to point to a PDF document (content-type: {content_type})"
            )

    content = resp.content

    # Size limit
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise ValueError(
            f"Document is too large ({len(content) / (1024*1024):.1f} MB). "
            f"Limit is {settings.max_upload_size_mb} MB."
        )

    if len(content) == 0:
        raise ValueError("Downloaded file is empty.")

    # Derive a filename from the URL
    from urllib.parse import urlparse
    path = urlparse(url).path
    filename = path.rsplit("/", 1)[-1] if "/" in path else "document.pdf"
    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"

    return content, filename

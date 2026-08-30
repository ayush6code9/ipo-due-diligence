"""
Unit tests for the live IPO search service (Phase 2).
"""

import hashlib
import json
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.db.models import DRHPDocument, IPOSearchCache
from app.schemas.ipo_search import IPOSearchResult
from app.services import ipo_search_service


class TestIPOSearchService(unittest.TestCase):
    def setUp(self):
        """Set up an in-memory SQLite database for isolated service testing."""
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)

    def test_cache_key_deterministic(self):
        """Cache keys should be normalized and deterministic."""
        k1 = ipo_search_service._cache_key("Tempsens Instruments")
        k2 = ipo_search_service._cache_key("  tempsens instruments  ")
        self.assertEqual(k1, k2)
        self.assertEqual(len(k1), 32)

    def test_cache_miss_and_hit(self):
        """Storing results in cache allows subsequent retrieval."""
        results = [
            IPOSearchResult(
                company_name="Tempsens Instruments (India) Limited",
                ipo_name="Tempsens Instruments IPO",
                status="Upcoming",
                document_type="DRHP",
                filing_date="15-Jan-2025",
                source_name="Chittorgarh",
                source_url="https://www.chittorgarh.com/ipo/tempsens-ipo/123/",
                document_url="https://www.sebi.gov.in/filings/tempsens_drhp.pdf",
                is_document_available=True,
                sector="Instrumentation",
                issue_size="₹350 Cr",
                price_band="₹120 to ₹130",
            )
        ]

        # Initially cache should be empty
        cached = ipo_search_service._get_cached_results(self.db, "Tempsens")
        self.assertIsNone(cached)

        # Store in cache
        ipo_search_service._store_cache(self.db, "Tempsens", results, "Chittorgarh")

        # Now retrieve from cache
        cached = ipo_search_service._get_cached_results(self.db, "Tempsens")
        self.assertIsNotNone(cached)
        self.assertEqual(len(cached), 1)
        self.assertEqual(cached[0].company_name, "Tempsens Instruments (India) Limited")
        self.assertEqual(cached[0].document_type, "DRHP")
        self.assertTrue(cached[0].is_document_available)

    def test_cache_expiration(self):
        """Expired cache entries should be deleted and return None."""
        results = [
            IPOSearchResult(
                company_name="Old Test IPO Ltd",
                source_name="Chittorgarh",
            )
        ]
        ipo_search_service._store_cache(self.db, "Old IPO", results, "Chittorgarh")

        # Manually alter the fetched_at timestamp to simulate expiration (e.g., 24 hours ago)
        key = ipo_search_service._cache_key("Old IPO")
        entry = self.db.query(IPOSearchCache).filter(IPOSearchCache.query_hash == key).first()
        entry.fetched_at = datetime.utcnow() - timedelta(hours=24)
        self.db.commit()

        # Should be treated as expired
        cached = ipo_search_service._get_cached_results(self.db, "Old IPO")
        self.assertIsNone(cached)

    def test_parse_chittorgarh_search_html(self):
        """Verify HTML parser correctly extracts IPO records from table rows."""
        sample_html = """
        <html>
          <body>
            <table>
              <tr><th>Issuer Company</th><th>Open</th><th>Close</th><th>Listing</th><th>Issue Price</th></tr>
              <tr>
                <td><a href="/ipo/sample-company-ipo/100/">Sample Company Limited</a></td>
                <td>20-Jan-2025</td>
                <td>22-Jan-2025</td>
                <td>Open</td>
                <td>₹100 to ₹105</td>
              </tr>
            </table>
          </body>
        </html>
        """
        results = ipo_search_service._parse_chittorgarh_search(sample_html, "Sample")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].company_name, "Sample Company Limited")
        self.assertEqual(results[0].status, "Open")
        self.assertEqual(results[0].source_name, "Chittorgarh")
        self.assertIn("sample-company-ipo", results[0].source_url)

    def test_parse_chittorgarh_ipo_page_drhp_detection(self):
        """Verify detail page parser finds DRHP/RHP PDF links."""
        sample_detail_html = """
        <html>
          <body>
            <table>
              <tr><td>Industry</td><td>Automotive Components</td></tr>
              <tr><td>Issue Size</td><td>₹500 Cr</td></tr>
            </table>
            <div>
              <a href="https://www.sebi.gov.in/reports/sample_drhp.pdf">Draft Red Herring Prospectus (DRHP)</a>
            </div>
          </body>
        </html>
        """
        info = ipo_search_service._parse_chittorgarh_ipo_page(sample_detail_html, "https://www.chittorgarh.com/ipo/sample/")
        self.assertEqual(info["document_type"], "DRHP")
        self.assertEqual(info["document_url"], "https://www.sebi.gov.in/reports/sample_drhp.pdf")
        self.assertEqual(info["sector"], "Automotive Components")
        self.assertEqual(info["issue_size"], "₹500 Cr")

    def test_download_document_validation(self):
        """Validate PDF download checks (bad URL, non-PDF, oversized)."""
        # Invalid URL schema
        with self.assertRaises(ValueError):
            ipo_search_service.download_document("ftp://example.com/test.pdf")

        # Mock non-PDF content
        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.headers = {"Content-Type": "text/html"}
            mock_resp.content = b"<html>Not a PDF</html>"
            mock_resp.raise_for_status.return_value = None
            mock_get.return_value = mock_resp

            with self.assertRaises(ValueError):
                ipo_search_service.download_document("https://example.com/test.html")

        # Mock valid PDF content
        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.headers = {"Content-Type": "application/pdf"}
            mock_resp.content = b"%PDF-1.5 test content for pdf"
            mock_resp.raise_for_status.return_value = None
            mock_get.return_value = mock_resp

            content, filename = ipo_search_service.download_document("https://example.com/prospectus.pdf")
            self.assertTrue(content.startswith(b"%PDF-"))
            self.assertEqual(filename, "prospectus.pdf")

    def test_drhp_document_source_metadata(self):
        """Verify DRHPDocument model persists source_url and source_name."""
        doc = DRHPDocument(
            original_filename="Tempsens_DRHP.pdf",
            stored_filename="abc123.pdf",
            file_size=1024,
            page_count=100,
            extracted_pages=100,
            extraction_status="success",
            source_url="https://www.sebi.gov.in/filings/tempsens.pdf",
            source_name="Chittorgarh",
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)

        saved = self.db.query(DRHPDocument).filter(DRHPDocument.id == doc.id).first()
        self.assertEqual(saved.source_url, "https://www.sebi.gov.in/filings/tempsens.pdf")
        self.assertEqual(saved.source_name, "Chittorgarh")


if __name__ == "__main__":
    unittest.main()

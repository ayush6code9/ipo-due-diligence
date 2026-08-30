"""
API tests for the live IPO search and document retrieval endpoints (Phases 3 & 5).
"""

import io
import unittest
from unittest.mock import MagicMock, patch

import fitz
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.ipo_search import IPOSearchResult


def _create_test_pdf_bytes(text: str = "Test Prospectus Content for Indian IPO") -> bytes:
    """Create a minimal valid PDF byte string for testing."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


class TestIPOSearchAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("app.services.ipo_search_service.search_ipos")
    def test_search_success(self, mock_search):
        """Test successful search returns 200 with structured IPO results."""
        mock_search.return_value = (
            [
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
            ],
            False,
        )

        response = self.client.get("/api/ipo/search?q=tempsens")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["query"], "tempsens")
        self.assertEqual(data["result_count"], 1)
        self.assertFalse(data["cached"])
        self.assertEqual(data["source"], "Chittorgarh")

        result = data["results"][0]
        self.assertEqual(result["company_name"], "Tempsens Instruments (India) Limited")
        self.assertEqual(result["document_type"], "DRHP")
        self.assertTrue(result["is_document_available"])
        self.assertEqual(result["document_url"], "https://www.sebi.gov.in/filings/tempsens_drhp.pdf")

    @patch("app.services.ipo_search_service.search_ipos")
    def test_search_empty_results(self, mock_search):
        """Test clean empty results response when no IPO matches query."""
        mock_search.return_value = ([], False)

        response = self.client.get("/api/ipo/search?q=nonexistentcompany")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["query"], "nonexistentcompany")
        self.assertEqual(data["result_count"], 0)
        self.assertEqual(data["results"], [])
        self.assertEqual(data["source"], "None")

    def test_search_missing_query_param(self):
        """Test missing query parameter returns 422 Unprocessable Entity."""
        response = self.client.get("/api/ipo/search")
        self.assertEqual(response.status_code, 422)

    def test_search_whitespace_query(self):
        """Test empty/whitespace query returns 422."""
        response = self.client.get("/api/ipo/search?q=%20%20%20")
        self.assertEqual(response.status_code, 422)

    def test_search_query_too_long(self):
        """Test query exceeding max length (200) returns 422."""
        long_query = "a" * 250
        response = self.client.get(f"/api/ipo/search?q={long_query}")
        self.assertEqual(response.status_code, 422)

    @patch("app.services.ipo_search_service.search_ipos")
    def test_search_provider_failure(self, mock_search):
        """Test provider exception returns controlled 502 Bad Gateway."""
        mock_search.side_effect = Exception("External scraping connection failed")

        response = self.client.get("/api/ipo/search?q=test")
        self.assertEqual(response.status_code, 502)
        data = response.json()
        self.assertIn("temporarily unavailable", data["detail"])

    # -------------------------------------------------------------
    # Phase 5: Document Retrieval Tests (/api/ipo/fetch-document)
    # -------------------------------------------------------------

    @patch("app.services.ipo_search_service.download_document")
    def test_fetch_document_success(self, mock_download):
        """Test successful document fetch creates a DRHPDocument record."""
        pdf_bytes = _create_test_pdf_bytes("Tempsens Instruments Draft Red Herring Prospectus")
        mock_download.return_value = (pdf_bytes, "tempsens_drhp.pdf")

        payload = {
            "document_url": "https://www.sebi.gov.in/filings/tempsens_drhp.pdf",
            "company_name": "Tempsens Instruments (India) Limited",
            "source_name": "Chittorgarh",
            "document_type": "DRHP",
        }

        response = self.client.post("/api/ipo/fetch-document", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("document_id", data)
        self.assertGreater(data["document_id"], 0)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["page_count"], 1)
        self.assertEqual(data["extracted_pages"], 1)
        self.assertEqual(data["source_url"], "https://www.sebi.gov.in/filings/tempsens_drhp.pdf")
        self.assertEqual(data["source_name"], "Chittorgarh")
        self.assertEqual(data["document_type"], "DRHP")

        # Verify document exists in database via GET /api/drhp/{id}
        doc_resp = self.client.get(f"/api/drhp/{data['document_id']}")
        self.assertEqual(doc_resp.status_code, 200)

    def test_fetch_document_invalid_url(self):
        """Test non-HTTP URL returns 400 with helpful message."""
        payload = {
            "document_url": "ftp://example.com/file.pdf",
            "company_name": "Test Company",
            "source_name": "SEBI",
        }
        response = self.client.post("/api/ipo/fetch-document", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid document URL", response.json()["detail"])

    def test_fetch_document_empty_url(self):
        """Test empty URL returns 400 with helpful message."""
        payload = {
            "document_url": "   ",
            "company_name": "Test Company",
        }
        response = self.client.post("/api/ipo/fetch-document", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("No document URL", response.json()["detail"])

    @patch("app.services.ipo_search_service.download_document")
    def test_fetch_document_non_pdf_rejection(self, mock_download):
        """Test non-PDF download is rejected with 400."""
        mock_download.side_effect = ValueError("The URL does not appear to point to a PDF document")

        payload = {
            "document_url": "https://example.com/not_a_pdf.html",
            "company_name": "Test Company",
        }
        response = self.client.post("/api/ipo/fetch-document", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("upload the DRHP manually", response.json()["detail"])

    @patch("app.services.ipo_search_service.download_document")
    def test_fetch_document_network_failure(self, mock_download):
        """Test provider network error returns 502 Bad Gateway with upload fallback hint."""
        mock_download.side_effect = Exception("Connection timed out after 15s")

        payload = {
            "document_url": "https://www.sebi.gov.in/unreachable.pdf",
            "company_name": "Test Company",
        }
        response = self.client.post("/api/ipo/fetch-document", json=payload)
        self.assertEqual(response.status_code, 502)
        self.assertIn("could not be retrieved", response.json()["detail"].lower())
        self.assertIn("upload the DRHP manually", response.json()["detail"])

    def test_manual_upload_unbroken(self):
        """Ensure the manual upload endpoint /api/drhp/upload continues to work."""
        pdf_bytes = _create_test_pdf_bytes("Manual Upload Verification DRHP")
        files = {"file": ("manual_test.pdf", io.BytesIO(pdf_bytes), "application/pdf")}

        response = self.client.post("/api/drhp/upload", files=files)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("document_id", data)
        self.assertEqual(data["original_filename"], "manual_test.pdf")


if __name__ == "__main__":
    unittest.main()

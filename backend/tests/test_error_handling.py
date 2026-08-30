"""
Comprehensive failure path and fallback tests (Phase 8).
"""

import io
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class TestErrorHandlingAndFallbacks(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    # 1. Search Provider Unavailable / Exception
    @patch("app.services.ipo_search_service.search_ipos")
    def test_search_provider_unavailable_returns_safe_502(self, mock_search):
        """External search failure returns safe 502 without stack traces."""
        mock_search.side_effect = ConnectionError("Scraping connection refused by host")
        resp = self.client.get("/api/ipo/search?q=test")
        self.assertEqual(resp.status_code, 502)
        data = resp.json()
        self.assertIn("temporarily unavailable", data["detail"])
        self.assertIn("upload the DRHP manually", data["detail"])
        # Ensure no raw stack trace leaked
        self.assertNotIn("Traceback", data["detail"])

    # 2. Search Query Validation Errors
    def test_search_empty_and_whitespace_queries(self):
        """Empty or whitespace queries return 422."""
        self.assertEqual(self.client.get("/api/ipo/search?q=").status_code, 422)
        self.assertEqual(self.client.get("/api/ipo/search?q=   ").status_code, 422)

    def test_search_oversized_query(self):
        """Oversized queries return 422."""
        self.assertEqual(self.client.get(f"/api/ipo/search?q={'x'*250}").status_code, 422)

    # 3. Search Empty Results
    @patch("app.services.ipo_search_service.search_ipos")
    def test_search_no_results_returns_clean_200(self, mock_search):
        """No matching IPOs returns 200 with empty array."""
        mock_search.return_value = ([], False)
        resp = self.client.get("/api/ipo/search?q=unknowncompany12345")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["result_count"], 0)
        self.assertEqual(data["results"], [])

    # 4. Fetch Document: Invalid URL Scheme
    def test_fetch_invalid_url_scheme(self):
        """Non-HTTP schemes return 400 with manual upload fallback."""
        payload = {"document_url": "javascript:alert(1)", "company_name": "Test Company"}
        resp = self.client.post("/api/ipo/fetch-document", json=payload)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("upload the DRHP manually", resp.json()["detail"])

    # 5. Fetch Document: Non-PDF Content
    @patch("app.services.ipo_search_service.download_document")
    def test_fetch_non_pdf_content(self, mock_download):
        """Non-PDF download returns 400 with manual upload fallback."""
        mock_download.side_effect = ValueError("The URL does not appear to point to a PDF document")
        payload = {"document_url": "https://example.com/page.html", "company_name": "Test Company"}
        resp = self.client.post("/api/ipo/fetch-document", json=payload)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("upload the DRHP manually", resp.json()["detail"])

    # 6. Fetch Document: Oversized File
    @patch("app.services.ipo_search_service.download_document")
    def test_fetch_oversized_document(self, mock_download):
        """Oversized document returns 400 with manual upload fallback."""
        mock_download.side_effect = ValueError("Document is too large (85.0 MB). Limit is 50 MB.")
        payload = {"document_url": "https://example.com/huge.pdf", "company_name": "Test Company"}
        resp = self.client.post("/api/ipo/fetch-document", json=payload)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("upload the DRHP manually", resp.json()["detail"])

    # 7. Fetch Document: Network / Timeout Error
    @patch("app.services.ipo_search_service.download_document")
    def test_fetch_timeout_error(self, mock_download):
        """Download timeout returns 502 with manual upload fallback."""
        mock_download.side_effect = TimeoutError("HTTP request timed out after 15s")
        payload = {"document_url": "https://example.com/timeout.pdf", "company_name": "Test Company"}
        resp = self.client.post("/api/ipo/fetch-document", json=payload)
        self.assertEqual(resp.status_code, 502)
        self.assertIn("upload the DRHP manually", resp.json()["detail"])

    # 8. Upload DRHP: Invalid Extension
    def test_upload_invalid_file_extension(self):
        """Uploading non-PDF files returns 400."""
        files = {"file": ("test.txt", io.BytesIO(b"Hello world"), "text/plain")}
        resp = self.client.post("/api/drhp/upload", files=files)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Only PDF files are accepted", resp.json()["detail"])

    # 9. Analysis / Extraction on Non-Existent Document
    def test_operations_on_non_existent_document(self):
        """Operations on non-existent document ID return 404."""
        self.assertEqual(self.client.get("/api/drhp/99999").status_code, 404)
        self.assertEqual(self.client.get("/api/drhp/99999/extraction").status_code, 404)
        self.assertEqual(self.client.get("/api/drhp/99999/analysis").status_code, 404)
        self.assertEqual(self.client.get("/api/drhp/99999/report").status_code, 404)


if __name__ == "__main__":
    unittest.main()

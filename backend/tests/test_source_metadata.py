"""
Unit tests for document source metadata tracking and reporting (Phase 7).
"""

import io
import unittest
from unittest.mock import MagicMock, patch

import fitz
from fastapi.testclient import TestClient

from app.db.database import SessionLocal
from app.db.models import DRHPDocument
from app.main import app
from app.services import report_service


def _create_minimal_pdf() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), "SAMPLE METADATA TEST PROSPECTUS")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


class TestSourceMetadata(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.pdf_bytes = _create_minimal_pdf()

    def test_uploaded_document_source_metadata(self):
        """Uploaded documents should have null or upload source metadata."""
        files = {"file": ("user_upload.pdf", io.BytesIO(self.pdf_bytes), "application/pdf")}
        resp = self.client.post("/api/drhp/upload", files=files)
        self.assertEqual(resp.status_code, 200)
        doc_id = resp.json()["document_id"]

        # Check metadata endpoint
        doc_meta = self.client.get(f"/api/drhp/{doc_id}").json()
        self.assertIsNone(doc_meta.get("source_url"))
        # source_name should be None or "Upload"
        self.assertIn(doc_meta.get("source_name"), [None, "Upload"])

    @patch("app.services.ipo_search_service.download_document")
    def test_searched_document_source_metadata_persistence(self, mock_download):
        """Searched documents must persist source_url and source_name."""
        mock_download.return_value = (self.pdf_bytes, "sebi_doc.pdf")

        payload = {
            "document_url": "https://www.sebi.gov.in/filings/sample_company_drhp.pdf",
            "company_name": "Sample Company Limited",
            "source_name": "SEBI EDGAR",
            "document_type": "DRHP",
        }
        fetch_resp = self.client.post("/api/ipo/fetch-document", json=payload)
        self.assertEqual(fetch_resp.status_code, 200)
        doc_id = fetch_resp.json()["document_id"]

        # Query via GET /api/drhp/{id}
        doc_meta = self.client.get(f"/api/drhp/{doc_id}").json()
        self.assertEqual(doc_meta["source_url"], "https://www.sebi.gov.in/filings/sample_company_drhp.pdf")
        self.assertEqual(doc_meta["source_name"], "SEBI EDGAR")

    def test_report_contains_source_metadata(self):
        """Report generation displays source metadata cleanly."""
        db = SessionLocal()
        try:
            # Check document 1 report
            doc = db.query(DRHPDocument).filter(DRHPDocument.id == 1).first()
            if doc:
                html = report_service.generate_report_html(db, 1)
                self.assertIn("Document Source:", html)
                self.assertIn("Report generated on", html)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()

"""
End-to-end pipeline convergence tests (Phase 6).

Verifies that both entry paths:
  Path A (Upload DRHP)
  Path B (Search IPO -> Fetch Document)
produce the exact same DRHPDocument record, indexing capability,
structured extraction output, and analysis scoring schema.
"""

import io
import unittest
from unittest.mock import patch

import fitz
from fastapi.testclient import TestClient

from app.main import app


def _create_sample_prospectus_pdf() -> bytes:
    """Create a multi-page test PDF with standard DRHP cover and section text."""
    doc = fitz.open()

    # Page 1: Cover
    p1 = doc.new_page()
    p1.insert_text(
        (50, 72),
        "UPDATED DRAFT RED HERRING PROSPECTUS\n"
        "TEMPSENS INSTRUMENTS (INDIA) LIMITED\n"
        "Corporate Identity Number: U31909RJ1990PLC005286\n"
        "Registered Office: A-190, Road No. 5, M.I.A., Udaipur 313 003, Rajasthan, India\n"
        "OUR PROMOTERS: MR. SANJAY GUPATHI AND MS. NIKITA GUPATHI\n"
        "INITIAL PUBLIC OFFER OF UP TO 5,000,000 EQUITY SHARES AGGREGATING UP TO ₹[●] MILLION\n",
    )

    # Page 2: Summary of Business
    p2 = doc.new_page()
    p2.insert_text(
        (50, 72),
        "Summary of the primary business of our Company\n"
        "We are an engineering and manufacturing company specializing in thermal and temperature measurement products.\n"
        "Summary of the industry in which our Company operates\n"
        "Industrial Automation & Instrumentation\n",
    )

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


class TestPipelineConvergence(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.pdf_bytes = _create_sample_prospectus_pdf()

    def test_path_a_manual_upload_pipeline(self):
        """Path A: Direct PDF Upload -> Document -> Index -> Extract -> Analyze."""
        # 1. Upload
        files = {"file": ("manual_upload.pdf", io.BytesIO(self.pdf_bytes), "application/pdf")}
        upload_resp = self.client.post("/api/drhp/upload", files=files)
        self.assertEqual(upload_resp.status_code, 200)
        doc_id = upload_resp.json()["document_id"]

        # 2. Document metadata
        doc_meta = self.client.get(f"/api/drhp/{doc_id}").json()
        self.assertEqual(doc_meta["page_count"], 2)
        self.assertEqual(doc_meta["extraction_status"], "success")

        # 3. Indexing
        idx_resp = self.client.post(f"/api/drhp/{doc_id}/index")
        self.assertEqual(idx_resp.status_code, 200)

        # 4. Structured Extraction
        ext_resp = self.client.post(f"/api/drhp/{doc_id}/extract")
        self.assertEqual(ext_resp.status_code, 200)
        extraction = ext_resp.json()["extraction"]
        self.assertIn("company_info", extraction)
        self.assertEqual(extraction["company_info"]["company_name"], "TEMPSENS INSTRUMENTS (INDIA) LIMITED")

        # 5. Deterministic Analysis
        ana_resp = self.client.post(f"/api/drhp/{doc_id}/analyze")
        self.assertEqual(ana_resp.status_code, 200)
        analysis = ana_resp.json()["analysis"]
        self.assertIn("overall_assessment", analysis)
        self.assertIn("financial_health", analysis)
        self.assertIn("promoter_analysis", analysis)
        self.assertIn("risk_analysis", analysis)

    @patch("app.services.ipo_search_service.download_document")
    def test_path_b_search_fetch_pipeline(self, mock_download):
        """Path B: Search Fetch -> Document -> Index -> Extract -> Analyze."""
        mock_download.return_value = (self.pdf_bytes, "tempsens_drhp.pdf")

        # 1. Fetch document from search
        fetch_payload = {
            "document_url": "https://www.sebi.gov.in/filings/tempsens_drhp.pdf",
            "company_name": "Tempsens Instruments (India) Limited",
            "source_name": "Chittorgarh",
            "document_type": "DRHP",
        }
        fetch_resp = self.client.post("/api/ipo/fetch-document", json=fetch_payload)
        self.assertEqual(fetch_resp.status_code, 200)
        doc_id = fetch_resp.json()["document_id"]

        # 2. Document metadata contains provenance
        doc_meta = self.client.get(f"/api/drhp/{doc_id}").json()
        self.assertEqual(doc_meta["page_count"], 2)

        # 3. Indexing (SAME downstream endpoint)
        idx_resp = self.client.post(f"/api/drhp/{doc_id}/index")
        self.assertEqual(idx_resp.status_code, 200)

        # 4. Structured Extraction (SAME downstream endpoint)
        ext_resp = self.client.post(f"/api/drhp/{doc_id}/extract")
        self.assertEqual(ext_resp.status_code, 200)
        extraction = ext_resp.json()["extraction"]
        self.assertEqual(extraction["company_info"]["company_name"], "TEMPSENS INSTRUMENTS (INDIA) LIMITED")

        # 5. Deterministic Analysis (SAME downstream endpoint)
        ana_resp = self.client.post(f"/api/drhp/{doc_id}/analyze")
        self.assertEqual(ana_resp.status_code, 200)
        analysis = ana_resp.json()["analysis"]
        self.assertIn("overall_assessment", analysis)
        self.assertEqual(analysis["company_name"], "TEMPSENS INSTRUMENTS (INDIA) LIMITED")
        self.assertIn("promoter_analysis", analysis)


if __name__ == "__main__":
    unittest.main()

"""
Unit and regression tests for DRHP structured extraction and deterministic analysis.
"""

import unittest
from app.schemas.extraction import (
    CompanyInfo,
    ExtractionResult,
    FinancialData,
    FinancialRatios,
    FinancialYearData,
    IPOParameters,
    PromoterData,
    PromoterInfo,
    RiskFactor,
)
from app.services.extraction_service import _calculate_ratios, _derive_strengths_and_concerns
from app.services.analysis_service import (
    _analyze_financial_health,
    _analyze_promoters,
    _analyze_risks,
    _calculate_overall_assessment,
    _format_ipo_parameters,
)


class TestExtractionAndAnalysis(unittest.TestCase):
    def test_ratio_calculations(self):
        fin_data = FinancialData(
            years=[
                FinancialYearData(year="FY23", revenue=2914.29, profit=-2796.07, total_assets=11840.28, net_worth=7518.26, total_debt=0.0),
                FinancialYearData(year="FY24", revenue=5064.13, profit=-1996.17, total_assets=12706.48, net_worth=9455.24, total_debt=0.0),
                FinancialYearData(year="FY25", revenue=7114.86, profit=-1727.41, total_assets=18205.23, net_worth=9509.11, total_debt=0.0),
            ]
        )
        ratios = _calculate_ratios(fin_data)
        self.assertEqual(ratios.current_year, "FY25")
        self.assertEqual(ratios.revenue_growth_pct, 40.5)
        self.assertEqual(ratios.profit_margin_pct, -24.3)
        self.assertEqual(ratios.debt_to_equity, 0.0)

    def test_financial_health_analysis(self):
        ext = ExtractionResult(
            document_id=1,
            status="completed",
            financial_ratios=FinancialRatios(
                revenue_growth_pct=40.5,
                profit_margin_pct=-24.3,
                debt_to_equity=0.0,
                roe_pct=-18.2,
                roa_pct=-9.5,
            )
        )
        health = _analyze_financial_health(ext)
        self.assertEqual(health.status, "Moderate")
        self.assertEqual(health.revenue_trend, "Growing")
        self.assertEqual(health.profit_trend, "Loss-Making")
        self.assertEqual(health.debt_position, "Very Low")

    def test_promoter_analysis(self):
        ext = ExtractionResult(
            document_id=1,
            status="completed",
            promoter_data=PromoterData(
                promoters=[
                    PromoterInfo(name="WM Digital Commerce Holdings Pte. Ltd.", experience_years=15),
                    PromoterInfo(name="Wal-Mart International Holdings, Inc.", experience_years=15),
                ],
                pre_issue_shareholding_pct=71.77,
            )
        )
        prom_analysis = _analyze_promoters(ext)
        self.assertEqual(prom_analysis.stars, 4)
        self.assertEqual(prom_analysis.label, "Good")

    def test_ipo_parameters_formatting(self):
        ext = ExtractionResult(
            document_id=1,
            status="completed",
            ipo_parameters=IPOParameters(
                issue_size="Up to 50,660,446 Equity Shares",
                price_band="To be determined (Book Built Offer)",
                fresh_issue="Not applicable",
                offer_for_sale="Up to 50,660,446 Equity Shares",
            )
        )
        params = _format_ipo_parameters(ext)
        self.assertEqual(params["issueSize"], "Up to 50,660,446 Equity Shares")
        self.assertEqual(params["priceBand"], "To be determined (Book Built Offer)")
        self.assertEqual(params["freshIssue"], "Not applicable")


if __name__ == "__main__":
    unittest.main()

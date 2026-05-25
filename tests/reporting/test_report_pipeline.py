"""Tests for report pipeline (reporter.py)."""

from src.reporting.reporter import generate_report

ANALYZED_DATA = {
    "status": "SUCCESS",
    "company": {"name": "TestCo", "ticker": "TEST"},
    "periods_analyzed": 3,
    "analysis_period": "FY2022-FY2024",
    "ratios": {
        "profitability": {
            "gross_margin": [{"period": "FY2024", "value": 0.4, "unit": "%"}],
            "operating_margin": [{"period": "FY2024", "value": 0.25, "unit": "%"}],
            "net_margin": [{"period": "FY2024", "value": 0.18, "unit": "%"}],
        },
        "liquidity": {
            "current_ratio": [{"period": "FY2024", "value": 1.71, "unit": "ratio"}],
            "quick_ratio": [{"period": "FY2024", "value": 1.49, "unit": "ratio"}],
            "working_capital": [{"period": "FY2024", "value": 25000.0, "unit": "USD"}],
            "operating_cf_ratio": [{"period": "FY2024", "value": 0.74, "unit": "ratio"}],
        },
        "solvency": {
            "debt_to_equity": [{"period": "FY2024", "value": 1.50, "unit": "ratio"}],
            "debt_to_assets": [{"period": "FY2024", "value": 0.60, "unit": "%"}],
            "interest_coverage": [{"period": "FY2024", "value": 12.1, "unit": "ratio"}],
            "lt_debt_to_equity": [{"period": "FY2024", "value": 1.06, "unit": "ratio"}],
        },
        "efficiency": {
            "asset_turnover": [{"period": "FY2024", "value": 0.475, "unit": "ratio"}],
            "receivables_turnover": [{"period": "FY2024", "value": 6.33, "unit": "ratio"}],
            "inventory_turnover": [{"period": "FY2024", "value": 6.62, "unit": "ratio"}],
            "days_sales_outstanding": [{"period": "FY2024", "value": 57.6, "unit": "days"}],
        },
        "cash_flow_quality": {
            "fcf": [{"period": "FY2024", "value": 21000.0, "unit": "USD"}],
            "fcf_margin": [{"period": "FY2024", "value": 0.221, "unit": "%"}],
            "cf_to_ni": [{"period": "FY2024", "value": 1.49, "unit": "ratio"}],
            "fcf_to_ni": [{"period": "FY2024", "value": 1.20, "unit": "ratio"}],
        },
    },
    "trends": {
        "revenue_yoy_growth": [{"period": "FY2024", "value": 0.05}],
        "net_income_yoy_growth": [{"period": "FY2024", "value": 0.05}],
        "operating_cf_yoy_growth": [{"period": "FY2024", "value": 0.03}],
        "revenue_cagr_3yr": 0.06,
        "margin_trend": "stable",
    },
    "red_flags": [],
    "cross_validation": [
        {
            "check_name": "earnings_quality",
            "result": "PASS",
            "detail": "Avg OCF 29,000 vs Avg NI 20,000",
            "periods_evaluated": 3,
        },
    ],
    "scorecard": {
        "profitability": 16,
        "liquidity": 14,
        "solvency": 12,
        "efficiency": 15,
        "cash_flow_quality": 17,
        "total": 74,
        "assessment": "Adequate",
    },
}


class TestGenerateReport:
    def test_success(self):
        result = generate_report(ANALYZED_DATA)
        assert result["status"] == "SUCCESS"
        assert "report" in result

    def test_error_status(self):
        result = generate_report({"status": "ERROR"})
        assert result["status"] == "ERROR"

    def test_report_has_company(self):
        result = generate_report(ANALYZED_DATA)
        assert result["report"]["company"]["ticker"] == "TEST"

    def test_report_has_periods(self):
        result = generate_report(ANALYZED_DATA)
        assert result["report"]["periods_analyzed"] == "FY2022-FY2024"

    def test_report_has_generated_at(self):
        result = generate_report(ANALYZED_DATA)
        assert "generated_at" in result["report"]

    def test_report_has_executive_summary(self):
        result = generate_report(ANALYZED_DATA)
        es = result["report"]["executive_summary"]
        assert "top_findings" in es
        assert "overall_assessment" in es

    def test_report_has_scorecard(self):
        result = generate_report(ANALYZED_DATA)
        sc = result["report"]["scorecard"]
        assert sc["total"] == 74
        assert sc["assessment"] == "Adequate"

    def test_report_has_detailed_findings(self):
        result = generate_report(ANALYZED_DATA)
        df = result["report"]["detailed_findings"]
        assert "income_statement" in df
        assert "balance_sheet" in df
        assert "cash_flow_statement" in df

    def test_report_has_ratio_analysis(self):
        result = generate_report(ANALYZED_DATA)
        assert len(result["report"]["ratio_analysis"]) > 0

    def test_report_has_red_flags(self):
        result = generate_report(ANALYZED_DATA)
        assert isinstance(result["report"]["red_flags"], list)

    def test_report_has_strengths(self):
        result = generate_report(ANALYZED_DATA)
        assert isinstance(result["report"]["strengths"], list)

    def test_report_has_recommendations(self):
        result = generate_report(ANALYZED_DATA)
        assert isinstance(result["report"]["recommendations"], list)

    def test_report_has_cross_validation(self):
        result = generate_report(ANALYZED_DATA)
        assert len(result["report"]["cross_validation"]) == 1

    def test_with_critical_red_flags(self):
        data = {
            **ANALYZED_DATA,
            "red_flags": [
                {
                    "type": "earnings_quality_concern",
                    "severity": "critical",
                    "description": "Earnings quality concern detected",
                    "periods_affected": ["FY2024"],
                    "current_value": 0.3,
                    "threshold": 0.5,
                },
            ],
            "scorecard": {**ANALYZED_DATA["scorecard"], "total": 35},
        }
        result = generate_report(data)
        assert result["status"] == "SUCCESS"
        es = result["report"]["executive_summary"]
        assert len(es["top_findings"]) >= 1

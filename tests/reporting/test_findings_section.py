"""Tests for findings section builder."""

from src.reporting.findings_section import build_findings


class TestBuildFindings:
    def test_all_statements(self):
        data = {
            "ratios": {
                "profitability": {
                    "gross_margin": [{"period": "FY2024", "value": 0.44}],
                    "net_margin": [{"period": "FY2024", "value": 0.18}],
                },
                "liquidity": {
                    "current_ratio": [{"period": "FY2024", "value": 1.71}],
                },
                "solvency": {
                    "debt_to_equity": [{"period": "FY2024", "value": 1.50}],
                },
                "cash_flow_quality": {
                    "cf_to_ni": [{"period": "FY2024", "value": 1.49}],
                    "fcf": [{"period": "FY2024", "value": 21000.0, "unit": "USD"}],
                },
            },
            "trends": {
                "revenue_yoy_growth": [{"value": 0.05}],
                "operating_cf_yoy_growth": [{"value": 0.03}],
            },
        }
        result = build_findings(data)
        assert "income_statement" in result
        assert "balance_sheet" in result
        assert "cash_flow_statement" in result
        assert len(result["income_statement"]) > 0
        assert len(result["balance_sheet"]) > 0
        assert len(result["cash_flow_statement"]) > 0

    def test_empty_data(self):
        data = {"ratios": {}, "trends": {}}
        result = build_findings(data)
        assert "not available" in result["income_statement"]
        assert "not available" in result["balance_sheet"]
        assert "not available" in result["cash_flow_statement"]

    def test_healthy_current_ratio(self):
        data = {
            "ratios": {
                "liquidity": {
                    "current_ratio": [{"period": "FY2024", "value": 2.0}],
                },
            },
            "trends": {},
        }
        result = build_findings(data)
        assert "healthy" in result["balance_sheet"]

    def test_concerning_current_ratio(self):
        data = {
            "ratios": {
                "liquidity": {
                    "current_ratio": [{"period": "FY2024", "value": 0.8}],
                },
            },
            "trends": {},
        }
        result = build_findings(data)
        assert "concerning" in result["balance_sheet"]

    def test_strong_earnings_quality(self):
        data = {
            "ratios": {
                "cash_flow_quality": {
                    "cf_to_ni": [{"period": "FY2024", "value": 1.5}],
                },
            },
            "trends": {},
        }
        result = build_findings(data)
        assert "strong" in result["cash_flow_statement"]

    def test_concerning_earnings_quality(self):
        data = {
            "ratios": {
                "cash_flow_quality": {
                    "cf_to_ni": [{"period": "FY2024", "value": 0.5}],
                },
            },
            "trends": {},
        }
        result = build_findings(data)
        assert "concerning" in result["cash_flow_statement"]

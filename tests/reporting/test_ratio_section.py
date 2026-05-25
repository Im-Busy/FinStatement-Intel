"""Tests for ratio analysis section builder."""

from src.reporting.ratio_section import build_ratio_analysis


class TestBuildRatioAnalysis:
    def test_full_analysis(self):
        ratios = {
            "profitability": {
                "gross_margin": [
                    {"period": "FY2023", "value": 0.40},
                    {"period": "FY2024", "value": 0.44},
                ],
                "operating_margin": [
                    {"period": "FY2024", "value": 0.25},
                ],
            },
            "liquidity": {
                "current_ratio": [
                    {"period": "FY2024", "value": 1.71},
                ],
            },
            "solvency": {
                "debt_to_equity": [
                    {"period": "FY2024", "value": 1.50},
                ],
                "interest_coverage": [
                    {"period": "FY2024", "value": 12.1},
                ],
            },
            "cash_flow_quality": {
                "cf_to_ni": [
                    {"period": "FY2024", "value": 1.49},
                ],
            },
        }
        trends = {}
        result = build_ratio_analysis(ratios, trends)
        assert len(result) > 0
        assert "Gross margin" in result
        assert "Operating margin" in result
        assert "CF-to-NI" in result
        assert "Current ratio" in result
        assert "Interest coverage" in result

    def test_improving_gross_margin(self):
        ratios = {
            "profitability": {
                "gross_margin": [
                    {"period": "FY2023", "value": 0.35},
                    {"period": "FY2024", "value": 0.45},
                ],
            },
        }
        trends = {}
        result = build_ratio_analysis(ratios, trends)
        assert "improving" in result

    def test_declining_gross_margin(self):
        ratios = {
            "profitability": {
                "gross_margin": [
                    {"period": "FY2023", "value": 0.45},
                    {"period": "FY2024", "value": 0.35},
                ],
            },
        }
        trends = {}
        result = build_ratio_analysis(ratios, trends)
        assert "declining" in result

    def test_empty(self):
        result = build_ratio_analysis({}, {})
        assert "not available" in result

    def test_weak_liquidity(self):
        ratios = {
            "liquidity": {
                "current_ratio": [{"period": "FY2024", "value": 0.8}],
            },
        }
        result = build_ratio_analysis(ratios, {})
        assert "weak" in result

    def test_strong_liquidity(self):
        ratios = {
            "liquidity": {
                "current_ratio": [{"period": "FY2024", "value": 2.5}],
            },
        }
        result = build_ratio_analysis(ratios, {})
        assert "strong" in result

"""Tests for strengths section builder."""

from src.reporting.strengths_section import build_strengths


class TestBuildStrengths:
    def test_high_gross_margin(self):
        ratios = {
            "profitability": {
                "gross_margin": [{"period": "FY2024", "value": 0.50}],
            },
        }
        result = build_strengths(ratios, [])
        assert any("gross margins" in s.lower() for s in result)

    def test_earnings_quality(self):
        ratios = {
            "cash_flow_quality": {
                "cf_to_ni": [
                    {"period": "FY2023", "value": 1.2},
                    {"period": "FY2024", "value": 1.3},
                ],
            },
        }
        result = build_strengths(ratios, [])
        assert any("earnings quality" in s.lower() for s in result)

    def test_strong_fcf_margin(self):
        ratios = {
            "cash_flow_quality": {
                "fcf_margin": [{"period": "FY2024", "value": 0.20}],
            },
        }
        result = build_strengths(ratios, [])
        assert any("free cash flow" in s.lower() for s in result)

    def test_excellent_liquidity(self):
        ratios = {
            "liquidity": {
                "current_ratio": [{"period": "FY2024", "value": 2.5}],
            },
        }
        result = build_strengths(ratios, [])
        assert any("liquidity" in s.lower() for s in result)

    def test_strong_debt_service(self):
        ratios = {
            "solvency": {
                "interest_coverage": [{"period": "FY2024", "value": 15.0}],
            },
        }
        result = build_strengths(ratios, [])
        assert any("debt service" in s.lower() for s in result)

    def test_revenue_quality_cross_validation(self):
        cross = [
            {"check_name": "revenue_quality", "result": "PASS"},
        ]
        result = build_strengths({}, cross)
        assert any("Revenue quality" in s for s in result)

    def test_demand_health_cross_validation(self):
        cross = [
            {"check_name": "demand_health", "result": "PASS"},
        ]
        result = build_strengths({}, cross)
        assert any("demand" in s.lower() for s in result)

    def test_earnings_quality_cross_validation(self):
        cross = [
            {"check_name": "earnings_quality", "result": "PASS"},
        ]
        result = build_strengths({}, cross)
        assert any("Earnings quality" in s for s in result)

    def test_insufficient_data(self):
        result = build_strengths({}, [])
        assert "Insufficient data" in result[0]

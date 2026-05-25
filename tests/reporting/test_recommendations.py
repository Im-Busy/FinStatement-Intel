"""Tests for recommendations section builder."""

from src.reporting.recommendations import build_recommendations


class TestBuildRecommendations:
    def test_default_recommendations(self):
        result = build_recommendations({}, [], {"total": 60})
        assert len(result) >= 3
        assert any("revenue growth" in r.lower() for r in result)

    def test_earnings_quality_recommendation(self):
        flags = [
            {"type": "earnings_quality_concern", "severity": "critical"},
        ]
        result = build_recommendations({}, flags, {})
        assert any("cash flow" in r.lower() for r in result)

    def test_liquidity_crisis_recommendation(self):
        flags = [
            {"type": "liquidity_crisis_risk", "severity": "critical"},
        ]
        result = build_recommendations({}, flags, {})
        assert any("working capital" in r.lower() for r in result)

    def test_sustained_negative_ocf_recommendation(self):
        flags = [
            {"type": "sustained_negative_ocf", "severity": "critical"},
        ]
        result = build_recommendations({}, flags, {})
        assert any("viability" in r.lower() for r in result)

    def test_cannot_cover_interest_recommendation(self):
        flags = [
            {"type": "cannot_cover_interest", "severity": "critical"},
        ]
        result = build_recommendations({}, flags, {})
        assert any("debt" in r.lower() for r in result)

    def test_negative_equity_recommendation(self):
        flags = [
            {"type": "negative_equity", "severity": "critical"},
        ]
        result = build_recommendations({}, flags, {})
        assert any("solvency" in r.lower() for r in result)

    def test_excessive_leverage_recommendation(self):
        flags = [
            {"type": "excessive_leverage", "severity": "warning"},
        ]
        result = build_recommendations({}, flags, {})
        assert any("debt" in r.lower() for r in result)

    def test_demand_problem_recommendation(self):
        flags = [
            {"type": "demand_problem", "severity": "warning"},
        ]
        result = build_recommendations({}, flags, {})
        assert any("inventory" in r.lower() for r in result)

    def test_acquisition_risk_recommendation(self):
        flags = [
            {"type": "acquisition_risk", "severity": "warning"},
        ]
        result = build_recommendations({}, flags, {})
        assert any("goodwill" in r.lower() for r in result)

    def test_critical_scorecard(self):
        result = build_recommendations({}, [], {"total": 30})
        assert any("comprehensive" in r.lower() for r in result)

    def test_concerning_scorecard(self):
        result = build_recommendations({}, [], {"total": 50})
        assert any("monitoring" in r.lower() for r in result)

    def test_multiple_warnings(self):
        flags = [
            {"type": "excessive_leverage", "severity": "warning"},
            {"type": "demand_problem", "severity": "warning"},
            {"type": "acquisition_risk", "severity": "warning"},
        ]
        result = build_recommendations({}, flags, {"total": 60})
        assert any("quarterly review" in r.lower() for r in result)

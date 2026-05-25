"""Tests for scorecard builder."""

from src.reporting.scorecard_builder import build_scorecard


class TestBuildScorecard:
    def test_full_data(self):
        scorecard = {
            "profitability": 16,
            "liquidity": 14,
            "solvency": 12,
            "efficiency": 15,
            "cash_flow_quality": 17,
            "total": 74,
            "assessment": "Adequate",
        }
        result = build_scorecard(scorecard)
        assert result["profitability"] == 16
        assert result["liquidity"] == 14
        assert result["total"] == 74
        assert result["assessment"] == "Adequate"

    def test_empty(self):
        result = build_scorecard({})
        assert result["profitability"] == 0
        assert result["total"] == 0

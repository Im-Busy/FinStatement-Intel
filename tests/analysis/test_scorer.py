"""Tests for financial health scorer (0-100 composite score)."""

from src.analysis.scorer import (
    compute_scorecard,
    score_cash_flow_quality,
    score_efficiency,
    score_liquidity,
    score_profitability,
    score_solvency,
)
from src.models.ratios import RatioPoint


class TestScoreProfitability:
    def test_max_score(self):
        ratios = {
            "gross_margin": [RatioPoint("FY2023", 0.30), RatioPoint("FY2024", 0.40)],
            "operating_margin": [RatioPoint("FY2023", 0.15), RatioPoint("FY2024", 0.20)],
            "net_margin": [RatioPoint("FY2023", 0.10), RatioPoint("FY2024", 0.15)],
            "roe": [RatioPoint("FY2023", 0.10), RatioPoint("FY2024", 0.20)],
        }
        score = score_profitability(ratios)
        assert score == 20

    def test_low_score(self):
        ratios = {
            "gross_margin": [RatioPoint("FY2023", 0.40), RatioPoint("FY2024", 0.30)],
            "operating_margin": [RatioPoint("FY2023", 0.20), RatioPoint("FY2024", 0.15)],
            "net_margin": [RatioPoint("FY2023", 0.15), RatioPoint("FY2024", 0.10)],
            "roe": [RatioPoint("FY2023", 0.03), RatioPoint("FY2024", 0.02)],
        }
        score = score_profitability(ratios)
        assert score == 0

    def test_single_period(self):
        ratios = {
            "gross_margin": [RatioPoint("FY2024", 0.44)],
            "operating_margin": [RatioPoint("FY2024", 0.20)],
            "net_margin": [RatioPoint("FY2024", 0.18)],
            "roe": [RatioPoint("FY2024", 0.25)],
        }
        score = score_profitability(ratios)
        assert score > 0

    def test_empty(self):
        score = score_profitability({})
        assert score >= 0


class TestScoreLiquidity:
    def test_max_score(self):
        ratios = {
            "current_ratio": [RatioPoint("FY2024", 3.0)],
            "quick_ratio": [RatioPoint("FY2024", 2.0)],
            "operating_cf_ratio": [RatioPoint("FY2024", 0.6)],
            "working_capital": [RatioPoint("FY2023", 10000), RatioPoint("FY2024", 20000)],
        }
        score = score_liquidity(ratios)
        assert score == 20

    def test_low_score(self):
        ratios = {
            "current_ratio": [RatioPoint("FY2024", 0.5)],
            "quick_ratio": [RatioPoint("FY2024", 0.2)],
            "operating_cf_ratio": [RatioPoint("FY2024", 0.1)],
            "working_capital": [RatioPoint("FY2023", 20000), RatioPoint("FY2024", 10000)],
        }
        score = score_liquidity(ratios)
        assert score == 0

    def test_empty(self):
        score = score_liquidity({})
        assert score >= 0


class TestScoreSolvency:
    def test_max_score(self):
        ratios = {
            "debt_to_equity": [RatioPoint("FY2024", 0.3)],
            "interest_coverage": [RatioPoint("FY2024", 15.0)],
        }
        score = score_solvency(ratios)
        assert score == 16

    def test_low_score(self):
        ratios = {
            "debt_to_equity": [RatioPoint("FY2024", 5.0)],
            "interest_coverage": [RatioPoint("FY2024", 0.5)],
        }
        score = score_solvency(ratios)
        assert score == 0

    def test_empty(self):
        score = score_solvency({})
        assert score >= 0


class TestScoreEfficiency:
    def test_positive(self):
        ratios = {
            "asset_turnover": [RatioPoint("FY2023", 0.5), RatioPoint("FY2024", 0.6)],
            "days_sales_outstanding": [RatioPoint("FY2023", 60), RatioPoint("FY2024", 50)],
            "inventory_turnover": [RatioPoint("FY2023", 5), RatioPoint("FY2024", 6)],
        }
        score = score_efficiency(ratios)
        assert score >= 15

    def test_negative(self):
        ratios = {
            "asset_turnover": [RatioPoint("FY2023", 0.6), RatioPoint("FY2024", 0.5)],
            "days_sales_outstanding": [RatioPoint("FY2023", 50), RatioPoint("FY2024", 60)],
            "inventory_turnover": [RatioPoint("FY2023", 6), RatioPoint("FY2024", 5)],
        }
        score = score_efficiency(ratios)
        assert score <= 10

    def test_empty(self):
        score = score_efficiency({})
        assert score >= 0


class TestScoreCashFlowQuality:
    def test_max_score(self):
        ratios = {
            "cf_to_ni": [RatioPoint("FY2024", 2.0)],
            "fcf_margin": [RatioPoint("FY2023", 0.10), RatioPoint("FY2024", 0.20)],
            "fcf": [
                RatioPoint("FY2020", 100),
                RatioPoint("FY2021", 150),
                RatioPoint("FY2022", 200),
                RatioPoint("FY2023", 250),
                RatioPoint("FY2024", 300),
            ],
        }
        score = score_cash_flow_quality(ratios)
        assert score == 16

    def test_low_score(self):
        ratios = {
            "cf_to_ni": [RatioPoint("FY2024", 0.3)],
            "fcf_margin": [RatioPoint("FY2023", 0.10), RatioPoint("FY2024", 0.05)],
            "fcf": [RatioPoint("FY2024", -100)],
        }
        score = score_cash_flow_quality(ratios)
        assert score <= 10

    def test_empty(self):
        score = score_cash_flow_quality({})
        assert score >= 0


class TestComputeScorecard:
    def test_full_scorecard(self):
        ratios = {
            "profitability": {
                "gross_margin": [RatioPoint("FY2024", 0.44)],
                "operating_margin": [RatioPoint("FY2024", 0.20)],
                "net_margin": [RatioPoint("FY2024", 0.18)],
                "roe": [RatioPoint("FY2024", 0.22)],
            },
            "liquidity": {
                "current_ratio": [RatioPoint("FY2024", 1.71)],
                "quick_ratio": [RatioPoint("FY2024", 1.49)],
                "operating_cf_ratio": [RatioPoint("FY2024", 0.74)],
                "working_capital": [RatioPoint("FY2024", 25000)],
            },
            "solvency": {
                "debt_to_equity": [RatioPoint("FY2024", 1.5)],
                "interest_coverage": [RatioPoint("FY2024", 12.0)],
            },
            "efficiency": {
                "asset_turnover": [RatioPoint("FY2024", 0.5)],
                "days_sales_outstanding": [RatioPoint("FY2024", 55.0)],
                "inventory_turnover": [RatioPoint("FY2024", 6.0)],
            },
            "cash_flow_quality": {
                "cf_to_ni": [RatioPoint("FY2024", 1.5)],
                "fcf_margin": [RatioPoint("FY2024", 0.22)],
                "fcf": [
                    RatioPoint("FY2020", 100),
                    RatioPoint("FY2021", 150),
                    RatioPoint("FY2022", 200),
                    RatioPoint("FY2023", 250),
                    RatioPoint("FY2024", 300),
                ],
            },
        }
        card = compute_scorecard(ratios)
        assert 0 <= card.total <= 100
        assert 0 <= card.profitability <= 20
        assert 0 <= card.liquidity <= 20
        assert 0 <= card.solvency <= 20
        assert 0 <= card.efficiency <= 20
        assert 0 <= card.cash_flow_quality <= 20
        assert card.assessment in ("Strong", "Adequate", "Concerning", "Critical")

    def test_assessment_strong(self):
        ratios = {
            "profitability": {
                "gross_margin": [RatioPoint("FY2023", 0.4), RatioPoint("FY2024", 0.5)],
                "operating_margin": [RatioPoint("FY2023", 0.2), RatioPoint("FY2024", 0.3)],
                "net_margin": [RatioPoint("FY2023", 0.15), RatioPoint("FY2024", 0.2)],
                "roe": [RatioPoint("FY2023", 0.2), RatioPoint("FY2024", 0.3)],
            },
            "liquidity": {
                "current_ratio": [RatioPoint("FY2024", 3.0)],
                "quick_ratio": [RatioPoint("FY2024", 2.0)],
                "operating_cf_ratio": [RatioPoint("FY2024", 0.6)],
                "working_capital": [RatioPoint("FY2023", 10000), RatioPoint("FY2024", 20000)],
            },
            "solvency": {
                "debt_to_equity": [RatioPoint("FY2024", 0.3)],
                "interest_coverage": [RatioPoint("FY2024", 15.0)],
            },
            "efficiency": {
                "asset_turnover": [RatioPoint("FY2023", 0.5), RatioPoint("FY2024", 0.6)],
                "days_sales_outstanding": [RatioPoint("FY2023", 60), RatioPoint("FY2024", 50)],
                "inventory_turnover": [RatioPoint("FY2023", 5), RatioPoint("FY2024", 6)],
            },
            "cash_flow_quality": {
                "cf_to_ni": [RatioPoint("FY2024", 2.0)],
                "fcf_margin": [RatioPoint("FY2023", 0.1), RatioPoint("FY2024", 0.2)],
                "fcf": [
                    RatioPoint("FY2022", 100),
                    RatioPoint("FY2023", 200),
                    RatioPoint("FY2024", 300),
                ],
            },
        }
        card = compute_scorecard(ratios)
        assert card.total >= 80
        assert card.assessment == "Strong"

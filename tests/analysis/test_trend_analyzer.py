"""Tests for trend analyzer functions."""

import pytest

from src.analysis.trend_analyzer import (
    analyze_trends,
    classify_margin_trend,
    compute_cagr,
    compute_yoy_growth,
)
from src.models.ratios import RatioPoint


class TestComputeYoyGrowth:
    def test_positive(self):
        values = [100.0, 110.0, 121.0]
        periods = ["FY2022", "FY2023", "FY2024"]
        result = compute_yoy_growth(values, periods)
        assert result[0].value == 0.1
        assert result[1].value == pytest.approx(0.1, abs=0.01)

    def test_negative_growth(self):
        values = [100.0, 90.0, 81.0]
        periods = ["FY2022", "FY2023", "FY2024"]
        result = compute_yoy_growth(values, periods)
        assert result[0].value == -0.1
        assert result[1].value == -0.1

    def test_zero_prev(self):
        values = [0.0, 100.0]
        periods = ["FY2023", "FY2024"]
        result = compute_yoy_growth(values, periods)
        assert result[0].value == 1.0

    def test_both_zero(self):
        values = [0.0, 0.0]
        periods = ["FY2023", "FY2024"]
        result = compute_yoy_growth(values, periods)
        assert result == []

    def test_single_value(self):
        result = compute_yoy_growth([100.0], ["FY2024"])
        assert result == []


class TestComputeCagr:
    def test_normal(self):
        assert compute_cagr(100.0, 133.1, 3) == pytest.approx(0.1, abs=0.001)

    def test_one_year(self):
        assert compute_cagr(100.0, 110.0, 1) == 0.1

    def test_invalid_years(self):
        assert compute_cagr(100.0, 110.0, 0) is None
        assert compute_cagr(100.0, 110.0, -1) is None

    def test_non_positive_start(self):
        assert compute_cagr(0.0, 110.0, 3) is None
        assert compute_cagr(-100.0, 110.0, 3) is None

    def test_declining(self):
        result = compute_cagr(100.0, 50.0, 3)
        assert result == pytest.approx(-0.2064, abs=0.001)


class TestClassifyMarginTrend:
    def test_improving(self):
        assert classify_margin_trend([0.10, 0.12, 0.15, 0.18]) == "improving"

    def test_declining(self):
        assert classify_margin_trend([0.20, 0.17, 0.14, 0.10]) == "declining"

    def test_stable(self):
        assert classify_margin_trend([0.10, 0.1005, 0.1003, 0.1008]) == "stable"

    def test_mixed(self):
        assert classify_margin_trend([0.10, 0.12, 0.11, 0.13]) == "mixed"

    def test_single_value(self):
        assert classify_margin_trend([0.10]) == "mixed"

    def test_empty(self):
        assert classify_margin_trend([]) == "mixed"


class TestAnalyzeTrends:
    def test_computes_all_trends(self):
        parsed_data = {
            "periods": [
                {
                    "fiscal_year": 2024,
                    "statements": {
                        "income_statement": {"revenue": 1200, "net_income": 120},
                        "cash_flow_statement": {"operating_cf": 170},
                    },
                },
                {
                    "fiscal_year": 2023,
                    "statements": {
                        "income_statement": {"revenue": 1100, "net_income": 110},
                        "cash_flow_statement": {"operating_cf": 160},
                    },
                },
                {
                    "fiscal_year": 2022,
                    "statements": {
                        "income_statement": {"revenue": 1000, "net_income": 100},
                        "cash_flow_statement": {"operating_cf": 150},
                    },
                },
            ],
        }
        ratios = {
            "profitability": {
                "net_margin": [
                    RatioPoint("FY2022", 0.10),
                    RatioPoint("FY2023", 0.10),
                    RatioPoint("FY2024", 0.10),
                ],
            },
        }
        result = analyze_trends(parsed_data, ratios)
        assert len(result["revenue_yoy_growth"]) == 2
        assert result["revenue_yoy_growth"][0].value == pytest.approx(0.1, abs=0.01)
        assert result["margin_trend"] == "stable"
        assert result["revenue_cagr_3yr"] is not None

    def test_empty_periods(self):
        result = analyze_trends({"periods": []}, {})
        assert result["revenue_yoy_growth"] == []

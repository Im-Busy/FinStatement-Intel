"""Tests for solvency ratio compute functions."""

from src.analysis.solvency import (
    compute_debt_to_assets,
    compute_debt_to_equity,
    compute_interest_coverage,
    compute_lt_debt_to_equity,
)


class TestComputeDebtToEquity:
    def test_normal(self):
        assert compute_debt_to_equity(120000, 80000) == 1.5

    def test_zero_equity(self):
        assert compute_debt_to_equity(120000, 0) is None

    def test_negative_equity(self):
        assert compute_debt_to_equity(120000, -50000) is None


class TestComputeDebtToAssets:
    def test_normal(self):
        assert compute_debt_to_assets(120000, 200000) == 0.6

    def test_zero_assets(self):
        assert compute_debt_to_assets(120000, 0) is None


class TestComputeInterestCoverage:
    def test_normal(self):
        assert compute_interest_coverage(25000, 2000) == 12.5

    def test_zero_interest(self):
        assert compute_interest_coverage(25000, 0) is None

    def test_negative_coverage(self):
        assert compute_interest_coverage(-5000, 2000) == -2.5


class TestComputeLtDebtToEquity:
    def test_normal(self):
        assert compute_lt_debt_to_equity(50000, 80000) == 0.625

    def test_zero_equity(self):
        assert compute_lt_debt_to_equity(50000, 0) is None

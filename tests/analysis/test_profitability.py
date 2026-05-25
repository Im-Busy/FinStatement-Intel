"""Tests for profitability ratio compute functions."""

from src.analysis.profitability import (
    compute_ebitda_margin,
    compute_gross_margin,
    compute_net_margin,
    compute_operating_margin,
    compute_roa,
    compute_roe,
)


class TestComputeGrossMargin:
    def test_normal(self):
        assert compute_gross_margin(40000, 100000) == 0.4

    def test_zero_revenue(self):
        assert compute_gross_margin(40000, 0) is None

    def test_negative_profit(self):
        assert compute_gross_margin(-5000, 100000) == -0.05


class TestComputeOperatingMargin:
    def test_normal(self):
        assert compute_operating_margin(25000, 100000) == 0.25

    def test_zero_revenue(self):
        assert compute_operating_margin(25000, 0) is None


class TestComputeNetMargin:
    def test_normal(self):
        assert compute_net_margin(19000, 100000) == 0.19

    def test_zero_revenue(self):
        assert compute_net_margin(19000, 0) is None

    def test_negative_income(self):
        assert compute_net_margin(-10000, 100000) == -0.1


class TestComputeRoa:
    def test_normal(self):
        assert compute_roa(19000, 200000) == 0.095

    def test_zero_assets(self):
        assert compute_roa(19000, 0) is None


class TestComputeRoe:
    def test_normal(self):
        assert compute_roe(19000, 80000) == 0.2375

    def test_zero_equity(self):
        assert compute_roe(19000, 0) is None

    def test_negative_equity(self):
        assert compute_roe(19000, -50000) is None


class TestComputeEbitdaMargin:
    def test_normal(self):
        assert compute_ebitda_margin(30000, 100000) == 0.3

    def test_zero_revenue(self):
        assert compute_ebitda_margin(30000, 0) is None

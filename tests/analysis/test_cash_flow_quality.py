"""Tests for cash flow quality compute functions."""

import pytest

from src.analysis.cash_flow_quality import (
    compute_cf_to_ni,
    compute_fcf,
    compute_fcf_margin,
    compute_fcf_to_ni,
)


class TestComputeFcf:
    def test_normal(self):
        assert compute_fcf(28000, -10000) == 18000.0

    def test_positive_capex(self):
        assert compute_fcf(28000, 10000) == 18000.0

    def test_zero(self):
        assert compute_fcf(0, 0) == 0.0


class TestComputeFcfMargin:
    def test_normal(self):
        assert compute_fcf_margin(18000, 100000) == 0.18

    def test_zero_revenue(self):
        assert compute_fcf_margin(18000, 0) is None

    def test_negative_fcf(self):
        assert compute_fcf_margin(-10000, 100000) == -0.1


class TestComputeCfToNi:
    def test_normal(self):
        assert compute_cf_to_ni(28000, 19000) == pytest.approx(1.4737, abs=0.0001)

    def test_zero_ni(self):
        assert compute_cf_to_ni(28000, 0) is None

    def test_negative_ni(self):
        assert compute_cf_to_ni(28000, -5000) == -5.6


class TestComputeFcfToNi:
    def test_normal(self):
        assert compute_fcf_to_ni(18000, 19000) == pytest.approx(0.9474, abs=0.0001)

    def test_zero_ni(self):
        assert compute_fcf_to_ni(18000, 0) is None

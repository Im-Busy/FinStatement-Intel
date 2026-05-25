"""Tests for liquidity ratio compute functions."""

import pytest

from src.analysis.liquidity import (
    compute_current_ratio,
    compute_operating_cf_ratio,
    compute_quick_ratio,
    compute_working_capital,
)


class TestComputeCurrentRatio:
    def test_normal(self):
        assert compute_current_ratio(60000, 35000) == pytest.approx(1.7143, abs=0.0001)

    def test_zero_liabilities(self):
        assert compute_current_ratio(60000, 0) is None

    def test_negative_ratio(self):
        result = compute_current_ratio(10000, 50000)
        assert result == 0.2


class TestComputeQuickRatio:
    def test_normal(self):
        result = compute_quick_ratio(60000, 8000, 35000)
        assert pytest.approx(result, abs=0.0001) == 1.4857

    def test_zero_liabilities(self):
        assert compute_quick_ratio(60000, 8000, 0) is None

    def test_no_inventory(self):
        result = compute_quick_ratio(60000, 0, 35000)
        assert pytest.approx(result, abs=0.0001) == 1.7143


class TestComputeWorkingCapital:
    def test_positive(self):
        assert compute_working_capital(60000, 35000) == 25000.0

    def test_negative(self):
        assert compute_working_capital(30000, 50000) == -20000.0

    def test_zero(self):
        assert compute_working_capital(50000, 50000) == 0.0


class TestComputeOperatingCfRatio:
    def test_normal(self):
        assert compute_operating_cf_ratio(28000, 35000) == 0.8

    def test_zero_cl(self):
        assert compute_operating_cf_ratio(28000, 0) is None

    def test_negative_ocf(self):
        assert compute_operating_cf_ratio(-10000, 35000) == pytest.approx(-0.2857, abs=0.0001)

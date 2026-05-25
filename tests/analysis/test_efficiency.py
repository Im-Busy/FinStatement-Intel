"""Tests for efficiency ratio compute functions."""

import pytest

from src.analysis.efficiency import (
    compute_asset_turnover,
    compute_days_sales_outstanding,
    compute_inventory_turnover,
    compute_receivables_turnover,
)


class TestComputeAssetTurnover:
    def test_normal(self):
        assert compute_asset_turnover(100000, 200000) == 0.5

    def test_zero_assets(self):
        assert compute_asset_turnover(100000, 0) is None


class TestComputeReceivablesTurnover:
    def test_normal(self):
        assert compute_receivables_turnover(100000, 15000) == pytest.approx(6.6667, abs=0.001)

    def test_zero_ar(self):
        assert compute_receivables_turnover(100000, 0) is None


class TestComputeInventoryTurnover:
    def test_normal(self):
        assert compute_inventory_turnover(60000, 8000) == 7.5

    def test_zero_inventory(self):
        assert compute_inventory_turnover(60000, 0) is None


class TestComputeDaysSalesOutstanding:
    def test_normal(self):
        assert compute_days_sales_outstanding(6.6667) == pytest.approx(54.7, abs=0.1)

    def test_none_turnover(self):
        assert compute_days_sales_outstanding(None) is None

    def test_zero_turnover(self):
        assert compute_days_sales_outstanding(0) is None

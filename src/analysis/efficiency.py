"""Efficiency ratios — asset/recievables/inventory turnover, days sales outstanding."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def compute_asset_turnover(revenue: float, total_assets: float) -> float | None:
    """Asset Turnover = Revenue / Total Assets."""
    if total_assets == 0:
        return None
    return round(revenue / total_assets, 4)


def compute_receivables_turnover(revenue: float, accounts_receivable: float) -> float | None:
    """Receivables Turnover = Revenue / Accounts Receivable."""
    if accounts_receivable == 0:
        return None
    return round(revenue / accounts_receivable, 4)


def compute_inventory_turnover(cogs: float, inventory: float) -> float | None:
    """Inventory Turnover = COGS / Inventory."""
    if inventory == 0:
        return None
    return round(cogs / inventory, 4)


def compute_days_sales_outstanding(receivables_turnover: float | None) -> float | None:
    """DSO = 365 / Receivables Turnover."""
    if receivables_turnover is None or receivables_turnover == 0:
        return None
    return round(365 / receivables_turnover, 1)

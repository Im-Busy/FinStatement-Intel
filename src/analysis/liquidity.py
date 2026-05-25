"""Liquidity ratios — current ratio, quick ratio, working capital, operating CF ratio."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def compute_current_ratio(current_assets: float, current_liabilities: float) -> float | None:
    """Current Ratio = Current Assets / Current Liabilities."""
    if current_liabilities == 0:
        return None
    return round(current_assets / current_liabilities, 4)


def compute_quick_ratio(
    current_assets: float,
    inventory: float,
    current_liabilities: float,
) -> float | None:
    """Quick Ratio = (Current Assets - Inventory) / Current Liabilities."""
    if current_liabilities == 0:
        return None
    return round((current_assets - inventory) / current_liabilities, 4)


def compute_working_capital(current_assets: float, current_liabilities: float) -> float:
    """Working Capital = Current Assets - Current Liabilities."""
    return round(current_assets - current_liabilities, 2)


def compute_operating_cf_ratio(operating_cf: float, current_liabilities: float) -> float | None:
    """Operating CF Ratio = Operating CF / Current Liabilities."""
    if current_liabilities == 0:
        return None
    return round(operating_cf / current_liabilities, 4)

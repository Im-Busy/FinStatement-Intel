"""Profitability ratios — gross/operating/net margin, ROA, ROE, EBITDA margin."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def compute_gross_margin(gross_profit: float, revenue: float) -> float | None:
    """Gross Margin = Gross Profit / Revenue."""
    if revenue == 0:
        return None
    return round(gross_profit / revenue, 4)


def compute_operating_margin(operating_income: float, revenue: float) -> float | None:
    """Operating Margin = Operating Income / Revenue."""
    if revenue == 0:
        return None
    return round(operating_income / revenue, 4)


def compute_net_margin(net_income: float, revenue: float) -> float | None:
    """Net Margin = Net Income / Revenue."""
    if revenue == 0:
        return None
    return round(net_income / revenue, 4)


def compute_roa(net_income: float, total_assets: float) -> float | None:
    """ROA = Net Income / Total Assets."""
    if total_assets == 0:
        return None
    return round(net_income / total_assets, 4)


def compute_roe(net_income: float, total_equity: float) -> float | None:
    """ROE = Net Income / Total Equity. Returns None if equity ≤ 0."""
    if total_equity <= 0:
        return None
    return round(net_income / total_equity, 4)


def compute_ebitda_margin(ebitda: float, revenue: float) -> float | None:
    """EBITDA Margin = EBITDA / Revenue."""
    if revenue == 0:
        return None
    return round(ebitda / revenue, 4)

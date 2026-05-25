"""Solvency ratios — debt-to-equity, debt-to-assets, interest coverage, LT debt-to-equity."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def compute_debt_to_equity(total_liabilities: float, total_equity: float) -> float | None:
    """Debt-to-Equity = Total Liabilities / Total Equity. Returns None if equity ≤ 0."""
    if total_equity <= 0:
        return None
    return round(total_liabilities / total_equity, 4)


def compute_debt_to_assets(total_liabilities: float, total_assets: float) -> float | None:
    """Debt-to-Assets = Total Liabilities / Total Assets."""
    if total_assets == 0:
        return None
    return round(total_liabilities / total_assets, 4)


def compute_interest_coverage(operating_income: float, interest_expense: float) -> float | None:
    """Interest Coverage = Operating Income / Interest Expense."""
    if interest_expense == 0:
        return None
    return round(operating_income / interest_expense, 4)


def compute_lt_debt_to_equity(long_term_debt: float, total_equity: float) -> float | None:
    """LT Debt-to-Equity = Long-Term Debt / Total Equity."""
    if total_equity <= 0:
        return None
    return round(long_term_debt / total_equity, 4)

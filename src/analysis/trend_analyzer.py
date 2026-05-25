"""Trend analyzer — YoY growth, CAGR, margin trend classification."""

from __future__ import annotations

import logging
from typing import Any

from src.config import MARGIN_STABLE_BAND
from src.models.ratios import RatioPoint

logger = logging.getLogger(__name__)


def compute_yoy_growth(
    values: list[float],
    periods: list[str],
) -> list[RatioPoint]:
    """Compute year-over-year growth: (V_t - V_{t-1}) / |V_{t-1}|.

    Args:
        values: List of values in chronological order (oldest first).
        periods: Corresponding period labels.

    Returns:
        List of RatioPoint for each pair where prev value is non-zero.
    """
    result: list[RatioPoint] = []
    for i in range(1, len(values)):
        prev = values[i - 1]
        curr = values[i]
        if abs(prev) > 0:
            growth = round((curr - prev) / abs(prev), 4)
            result.append(RatioPoint(periods[i], growth, "%"))
        elif abs(curr) > 0:
            result.append(RatioPoint(periods[i], 1.0, "%"))
    return result


def compute_cagr(
    start_value: float,
    end_value: float,
    num_years: int,
) -> float | None:
    """CAGR = (end_value / start_value)^(1/num_years) - 1.

    Args:
        start_value: Value at period start.
        end_value: Value at period end.
        num_years: Number of years between values.

    Returns:
        CAGR as float or None if invalid inputs.
    """
    if num_years <= 0:
        return None
    if start_value <= 0:
        return None
    return round((end_value / start_value) ** (1.0 / num_years) - 1, 4)


def classify_margin_trend(margins: list[float]) -> str:
    """Classify margin direction across periods.

    Compares last 2 periods to prior periods.

    Returns:
        "improving" | "stable" | "declining" | "mixed"
    """
    if len(margins) < 2:
        return "mixed"

    diffs = [margins[i] - margins[i - 1] for i in range(1, len(margins))]
    if not diffs:
        return "mixed"

    if all(d > MARGIN_STABLE_BAND for d in diffs):
        return "improving"
    if all(d < -MARGIN_STABLE_BAND for d in diffs):
        return "declining"
    if all(abs(d) <= MARGIN_STABLE_BAND for d in diffs):
        return "stable"
    return "mixed"


def analyze_trends(
    parsed_data: dict[str, Any],
    ratios: dict[str, Any],
) -> dict[str, Any]:
    """Run all trend analyses.

    Returns:
        Dict with revenue/net_income/ocf/fcf YoY growth, CAGRs, margin trend.
    """
    periods = parsed_data.get("periods", [])
    labels = [f"FY{p.get('fiscal_year', '')}" for p in periods]

    revenues = []
    net_incomes = []
    operating_cfs = []

    for p in periods:
        stmts = p.get("statements", {})
        revenues.append(stmts.get("income_statement", {}).get("revenue", 0))
        net_incomes.append(stmts.get("income_statement", {}).get("net_income", 0))
        operating_cfs.append(stmts.get("cash_flow_statement", {}).get("operating_cf", 0))

    net_margins = []
    for rp in ratios.get("profitability", {}).get("net_margin", []):
        if rp.value != 0.0 or (net_margins and rp.value == 0.0):
            net_margins.append(rp.value)
    if not net_margins and revenues and net_incomes:
        net_margins = [round(n / r, 4) if r else 0.0 for r, n in zip(revenues, net_incomes)]

    rev_3yr = (
        compute_cagr(revenues[-1], revenues[0], min(len(revenues) - 1, 3))
        if len(revenues) >= 3
        else None
    )
    rev_5yr = (
        compute_cagr(revenues[-1], revenues[0], min(len(revenues) - 1, 5))
        if len(revenues) >= 5
        else None
    )

    revenues_chrono = list(reversed(revenues))
    net_incomes_chrono = list(reversed(net_incomes))
    operating_cfs_chrono = list(reversed(operating_cfs))
    labels_chrono = list(reversed(labels))

    return {
        "revenue_yoy_growth": compute_yoy_growth(revenues_chrono, labels_chrono),
        "net_income_yoy_growth": compute_yoy_growth(net_incomes_chrono, labels_chrono),
        "operating_cf_yoy_growth": compute_yoy_growth(operating_cfs_chrono, labels_chrono),
        "revenue_cagr_3yr": rev_3yr,
        "revenue_cagr_5yr": rev_5yr,
        "margin_trend": classify_margin_trend(net_margins),
    }

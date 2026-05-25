"""Financial health scorer — 5-dimension composite score (0-100)."""

from __future__ import annotations

from typing import Any

from src.models.ratios import RatioPoint
from src.models.report_model import Scorecard


def _latest_value(points: list[RatioPoint]) -> float:
    return points[-1].value if points else 0.0


def _trend_direction(points: list[RatioPoint]) -> str:
    if len(points) < 2:
        return "stable"
    diffs = [points[i].value - points[i - 1].value for i in range(1, len(points))]
    if all(d > 0.01 for d in diffs):
        return "improving"
    if all(d < -0.01 for d in diffs):
        return "declining"
    if all(abs(d) <= 0.01 for d in diffs):
        return "stable"
    return "mixed"


def score_profitability(ratios: dict[str, Any]) -> int:
    """Score profitability 0-20."""
    gm = ratios.get("gross_margin", [])
    om = ratios.get("operating_margin", [])
    nm = ratios.get("net_margin", [])
    roe = ratios.get("roe", [])

    score = 0
    for series in [gm, om, nm]:
        trend = _trend_direction(series)
        if trend == "improving":
            score += 5
        elif trend == "stable":
            score += 3
        elif trend == "declining":
            score += 0
        else:
            score += 2

    roe_val = _latest_value(roe)
    if roe_val > 0.15:
        score += 5
    elif roe_val > 0.10:
        score += 3
    elif roe_val > 0.05:
        score += 1

    return min(score, 20)


def score_liquidity(ratios: dict[str, Any]) -> int:
    """Score liquidity 0-20."""
    cr = _latest_value(ratios.get("current_ratio", []))
    qr = _latest_value(ratios.get("quick_ratio", []))
    ocfr = _latest_value(ratios.get("operating_cf_ratio", []))
    wc_trend = _trend_direction(ratios.get("working_capital", []))

    score = 0
    if cr > 2.0:
        score += 7
    elif cr > 1.5:
        score += 5
    elif cr > 1.0:
        score += 3

    if qr > 1.0:
        score += 5
    elif qr > 0.5:
        score += 3

    if ocfr > 0.5:
        score += 4
    elif ocfr > 0.2:
        score += 2

    if wc_trend == "improving":
        score += 4
    elif wc_trend == "stable":
        score += 2

    return min(score, 20)


def score_solvency(ratios: dict[str, Any]) -> int:
    """Score solvency 0-20."""
    de = _latest_value(ratios.get("debt_to_equity", []))
    ic = _latest_value(ratios.get("interest_coverage", []))

    score = 0
    if de < 0.5:
        score += 8
    elif de < 1.0:
        score += 6
    elif de < 2.0:
        score += 3

    if ic > 10:
        score += 8
    elif ic > 5:
        score += 6
    elif ic > 2:
        score += 3
    elif ic > 1.0:
        score += 1

    return min(score, 20)


def score_efficiency(ratios: dict[str, Any]) -> int:
    """Score efficiency 0-20."""
    at = _trend_direction(ratios.get("asset_turnover", []))
    dso_trend = _trend_direction(ratios.get("days_sales_outstanding", []))
    it = _trend_direction(ratios.get("inventory_turnover", []))

    score = 0
    if at == "improving":
        score += 6
    elif at == "stable":
        score += 4
    elif at == "declining":
        score += 2

    if dso_trend == "declining":
        score += 5
    elif dso_trend == "stable":
        score += 3
    elif dso_trend == "improving":
        score += 1

    if it == "improving":
        score += 5
    elif it == "stable":
        score += 3
    elif it == "declining":
        score += 1

    return min(score, 20)


def score_cash_flow_quality(ratios: dict[str, Any]) -> int:
    """Score cash flow quality 0-20."""
    cf_ni = _latest_value(ratios.get("cf_to_ni", []))
    fcfm_trend = _trend_direction(ratios.get("fcf_margin", []))
    fcf_vals = ratios.get("fcf", [])

    score = 0
    if cf_ni > 1.5:
        score += 6
    elif cf_ni > 1.0:
        score += 4
    elif cf_ni > 0.5:
        score += 2

    if fcfm_trend == "improving":
        score += 6
    elif fcfm_trend == "stable":
        score += 4
    elif fcfm_trend == "declining":
        score += 2

    positive_years = sum(1 for p in fcf_vals if p.value > 0)
    if positive_years >= 5:
        score += 4
    elif positive_years >= 3:
        score += 2

    return min(score, 20)


def compute_scorecard(ratios: dict[str, Any]) -> Scorecard:
    """Compute full 5-dimension scorecard.

    Assessment scale:
        80-100: Strong
        60-79: Adequate
        40-59: Concerning
        0-39: Critical
    """
    p = score_profitability(ratios.get("profitability", {}))
    liq = score_liquidity(ratios.get("liquidity", {}))
    s = score_solvency(ratios.get("solvency", {}))
    e = score_efficiency(ratios.get("efficiency", {}))
    c = score_cash_flow_quality(ratios.get("cash_flow_quality", {}))

    total = p + liq + s + e + c
    if total >= 80:
        assessment = "Strong"
    elif total >= 60:
        assessment = "Adequate"
    elif total >= 40:
        assessment = "Concerning"
    else:
        assessment = "Critical"

    return Scorecard(
        profitability=p,
        liquidity=liq,
        solvency=s,
        efficiency=e,
        cash_flow_quality=c,
        total=total,
        assessment=assessment,
    )

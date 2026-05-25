"""Red flag detector — 12 pattern-based checks with severity classification."""

from __future__ import annotations

import logging
from typing import Any

from src.models.enums import Severity
from src.models.ratios import RatioPoint
from src.models.red_flag import RedFlag

logger = logging.getLogger(__name__)


def _ratio_values(points: list[RatioPoint]) -> list[float]:
    return [p.value for p in points]


def detect_earnings_quality_concern(
    cf_to_ni_series: list[float],
    periods: list[str],
) -> RedFlag | None:
    """Flag if CF/NI < 0.5 in any period."""
    for i, val in enumerate(cf_to_ni_series):
        if val < 0.5:
            return RedFlag(
                type="earnings_quality_concern",
                severity=Severity.CRITICAL,
                description=f"CF-to-NI ratio of {val:.2f} is below 0.5 threshold — earnings quality concern",
                periods_affected=[periods[i]] if i < len(periods) else [],
                current_value=val,
                threshold=0.5,
            )
    return None


def detect_liquidity_crisis(
    current_ratios: list[float],
    periods: list[str],
) -> RedFlag | None:
    """Flag if Current Ratio < 1.0 in any period."""
    for i, val in enumerate(current_ratios):
        if val < 1.0:
            return RedFlag(
                type="liquidity_crisis_risk",
                severity=Severity.CRITICAL,
                description=f"Current ratio of {val:.2f} below 1.0 — liquidity crisis risk",
                periods_affected=[periods[i]] if i < len(periods) else [],
                current_value=val,
                threshold=1.0,
            )
    return None


def detect_excessive_leverage(
    de_ratios: list[float],
    periods: list[str],
    threshold: float = 2.0,
) -> RedFlag | None:
    """Flag if D/E > threshold."""
    affected: list[str] = []
    max_val = 0.0
    for i, val in enumerate(de_ratios):
        if val <= 0:
            continue
        if val > threshold:
            if i < len(periods):
                affected.append(periods[i])
            max_val = max(max_val, val)

    if not affected:
        return None
    return RedFlag(
        type="excessive_leverage",
        severity=Severity.WARNING,
        description=f"D/E ratio of {max_val:.2f} exceeds {threshold} threshold",
        periods_affected=affected,
        current_value=max_val,
        threshold=threshold,
    )


def detect_sustained_negative_ocf(
    ocf_values: list[float],
    periods: list[str],
) -> RedFlag | None:
    """Flag if Operating CF < 0 for 3+ consecutive periods."""
    max_consecutive = 0
    current_streak = 0
    for val in ocf_values:
        if val < 0:
            current_streak += 1
            max_consecutive = max(max_consecutive, current_streak)
        else:
            current_streak = 0

    if max_consecutive >= 3:
        return RedFlag(
            type="sustained_negative_ocf",
            severity=Severity.CRITICAL,
            description=f"Operating cash flow negative for {max_consecutive} consecutive periods — major concern",
            periods_affected=periods,
        )
    return None


def detect_demand_problem(
    inventory_growth: list[float],
    revenue_growth: list[float],
    periods: list[str],
) -> RedFlag | None:
    """Flag if Inventory growth > Revenue growth."""
    if not inventory_growth or not revenue_growth:
        return None
    inv_g = sum(inventory_growth) / len(inventory_growth)
    rev_g = sum(revenue_growth) / len(revenue_growth)
    if inv_g > rev_g:
        return RedFlag(
            type="demand_problem",
            severity=Severity.WARNING,
            description=f"Inventory growth ({inv_g:.2%}) exceeds revenue growth ({rev_g:.2%}) — potential demand issue",
            periods_affected=periods,
        )
    return None


def detect_acquisition_risk(
    goodwill: float,
    equity: float,
    period: str,
) -> RedFlag | None:
    """Flag if Goodwill > 50% of Equity."""
    if equity <= 0 or goodwill <= 0:
        return None
    ratio = goodwill / equity
    if ratio > 0.5:
        return RedFlag(
            type="acquisition_risk",
            severity=Severity.WARNING,
            description=f"Goodwill ({goodwill:,.0f}) is {ratio:.1%} of equity — acquisition risk",
            periods_affected=[period],
            current_value=ratio,
            threshold=0.5,
        )
    return None


def detect_debt_service_concern(
    interest_coverage: list[float],
    periods: list[str],
) -> RedFlag | None:
    """Flag if Interest Coverage < 1.5."""
    for i, val in enumerate(interest_coverage):
        if 1.0 <= val < 1.5:
            return RedFlag(
                type="debt_service_concern",
                severity=Severity.WARNING,
                description=f"Interest coverage of {val:.2f} below 1.5 — debt service concern",
                periods_affected=[periods[i]] if i < len(periods) else [],
                current_value=val,
                threshold=1.5,
            )
    return None


def detect_cannot_cover_interest(
    interest_coverage: list[float],
    periods: list[str],
) -> RedFlag | None:
    """Flag if Interest Coverage < 1.0."""
    for i, val in enumerate(interest_coverage):
        if val <= 0:
            continue
        if val < 1.0:
            return RedFlag(
                type="cannot_cover_interest",
                severity=Severity.CRITICAL,
                description=f"Interest coverage of {val:.2f} below 1.0 — cannot cover interest from operations",
                periods_affected=[periods[i]] if i < len(periods) else [],
                current_value=val,
                threshold=1.0,
            )
    return None


def detect_negative_equity(
    equity_values: list[float],
    periods: list[str],
) -> RedFlag | None:
    """Flag if Total Equity < 0 in any period."""
    for i, val in enumerate(equity_values):
        if val < 0:
            return RedFlag(
                type="negative_equity",
                severity=Severity.CRITICAL,
                description=f"Negative equity of {val:,.0f} — insolvency risk",
                periods_affected=[periods[i]] if i < len(periods) else [],
                current_value=val,
            )
    return None


def detect_sustained_margin_decline(
    margins: list[float],
    periods: list[str],
) -> RedFlag | None:
    """Flag if 3+ consecutive years of declining margins."""
    streak = 0
    for i in range(1, len(margins)):
        if margins[i] < margins[i - 1]:
            streak += 1
        else:
            streak = 0
    if streak >= 3:
        return RedFlag(
            type="sustained_margin_decline",
            severity=Severity.WARNING,
            description=f"Margins have declined for {streak} consecutive periods",
            periods_affected=periods,
        )
    return None


def detect_cash_burn(
    fcf_values: list[float],
    periods: list[str],
) -> RedFlag | None:
    """Flag if negative FCF for 3+ consecutive periods."""
    streak = 0
    for val in fcf_values:
        if val < 0:
            streak += 1
        else:
            streak = 0
    if streak >= 3:
        return RedFlag(
            type="cash_burn",
            severity=Severity.WARNING,
            description=f"Negative free cash flow for {streak} consecutive periods — cash burn",
            periods_affected=periods,
        )
    return None


def detect_all_red_flags(
    periods_data: list[dict[str, Any]],
    ratios: dict[str, Any],
) -> list[RedFlag]:
    """Run all 12 red flag checks."""
    flags: list[RedFlag] = []
    labels = [f"FY{p.get('fiscal_year', '')}" for p in periods_data]

    cf_ni = _ratio_values(ratios.get("cash_flow_quality", {}).get("cf_to_ni", []))
    cr = _ratio_values(ratios.get("liquidity", {}).get("current_ratio", []))
    de = _ratio_values(ratios.get("solvency", {}).get("debt_to_equity", []))
    ic = _ratio_values(ratios.get("solvency", {}).get("interest_coverage", []))
    fcf_vals = _ratio_values(ratios.get("cash_flow_quality", {}).get("fcf", []))
    nm = _ratio_values(ratios.get("profitability", {}).get("net_margin", []))

    ocf_vals: list[float] = []
    eq_vals: list[float] = []
    inv_vals: list[float] = []
    rev_vals: list[float] = []
    for p in periods_data:
        stmts = p.get("statements", {})
        ocf_vals.append(stmts.get("cash_flow_statement", {}).get("operating_cf", 0))
        eq_vals.append(stmts.get("balance_sheet", {}).get("total_equity", 0))
        inv_vals.append(stmts.get("balance_sheet", {}).get("inventory", 0))
        rev_vals.append(stmts.get("income_statement", {}).get("revenue", 0))

    checks: list[RedFlag | None] = [
        detect_earnings_quality_concern(cf_ni, labels),
        detect_liquidity_crisis(cr, labels),
        detect_excessive_leverage(de, labels),
        detect_sustained_negative_ocf(ocf_vals, labels),
        detect_cannot_cover_interest(ic, labels),
        detect_debt_service_concern(ic, labels),
        detect_negative_equity(eq_vals, labels),
        detect_cash_burn(fcf_vals, labels),
        detect_sustained_margin_decline(nm, labels),
    ]

    inv_growth = _compute_growth(inv_vals)
    rev_growth = _compute_growth(rev_vals)
    if inv_growth and rev_growth:
        checks.append(detect_demand_problem(inv_growth, rev_growth, labels))

    if periods_data:
        p = periods_data[-1]
        stmts = p.get("statements", {})
        bs = stmts.get("balance_sheet", {})
        checks.append(
            detect_acquisition_risk(
                bs.get("goodwill", 0),
                bs.get("total_equity", 0),
                labels[-1] if labels else "",
            )
        )

    for flag in checks:
        if flag is not None:
            flags.append(flag)

    flags.sort(key=lambda f: 0 if f.severity == Severity.CRITICAL else 1)
    return flags


def _compute_growth(values: list[float]) -> list[float]:
    if len(values) < 2:
        return []
    result: list[float] = []
    for i in range(1, len(values)):
        if abs(values[i - 1]) > 0:
            result.append((values[i] - values[i - 1]) / abs(values[i - 1]))
        else:
            result.append(0.0)
    return result

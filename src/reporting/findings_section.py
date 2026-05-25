"""Findings section — synthesizes per-statement analysis narrative."""

from __future__ import annotations

from typing import Any


def build_findings(analyzed_data: dict[str, Any]) -> dict[str, str]:
    """Build per-statement findings narrative.

    Args:
        analyzed_data: Analyzed data with ratios, trends, periods.

    Returns:
        Dict with income_statement, balance_sheet, cash_flow_statement keys.
    """
    ratios = analyzed_data.get("ratios", {})
    trends = analyzed_data.get("trends", {})

    is_text = _build_is_findings(ratios, trends)
    bs_text = _build_bs_findings(ratios, trends, analyzed_data)
    cfs_text = _build_cfs_findings(ratios, trends)

    return {
        "income_statement": is_text,
        "balance_sheet": bs_text,
        "cash_flow_statement": cfs_text,
    }


def _latest_valid(points: list[dict]) -> dict | None:
    for p in reversed(points):
        if abs(p.get("value", 0)) > 0.0001:
            return p
    return points[0] if points else None


def _build_is_findings(ratios: dict, trends: dict) -> str:
    parts: list[str] = []
    rev_growth = trends.get("revenue_yoy_growth", [])
    if rev_growth:
        latest = rev_growth[-1]["value"]
        parts.append(f"Revenue {_growth_text(latest)} YoY")

    gm = ratios.get("profitability", {}).get("gross_margin", [])
    if gm:
        lv = _latest_valid(gm)
        parts.append(f"Gross margin at {lv['value']:.1%}")

    nm = ratios.get("profitability", {}).get("net_margin", [])
    if nm:
        lv = _latest_valid(nm)
        parts.append(f"Net margin at {lv['value']:.1%}")

    return ". ".join(parts) + "." if parts else "Income statement data not available."


def _build_bs_findings(ratios: dict, trends: dict, analyzed_data: dict) -> str:
    parts: list[str] = []
    cr = ratios.get("liquidity", {}).get("current_ratio", [])
    if cr:
        lv = _latest_valid(cr)
        val = lv["value"]
        status = "healthy" if val > 1.5 else "adequate" if val > 1.0 else "concerning"
        parts.append(f"Current ratio of {val:.2f} ({status})")

    de = ratios.get("solvency", {}).get("debt_to_equity", [])
    if de:
        lv = _latest_valid(de)
        parts.append(f"Debt-to-equity at {lv['value']:.2f}")

    return ". ".join(parts) + "." if parts else "Balance sheet data not available."


def _build_cfs_findings(ratios: dict, trends: dict) -> str:
    parts: list[str] = []
    cf_ni = ratios.get("cash_flow_quality", {}).get("cf_to_ni", [])
    if cf_ni:
        lv = _latest_valid(cf_ni)
        val = lv["value"]
        quality = "strong" if val > 1.2 else "adequate" if val > 0.8 else "concerning"
        parts.append(f"CF-to-NI ratio of {val:.2f} ({quality} earnings quality)")

    fcf = ratios.get("cash_flow_quality", {}).get("fcf", [])
    if fcf:
        lv = _latest_valid(fcf)
        parts.append(f"Free cash flow of {lv['value']:,.0f}")

    ocf_growth = trends.get("operating_cf_yoy_growth", [])
    if ocf_growth:
        parts.append(f"Operating CF {_growth_text(ocf_growth[-1]['value'])} YoY")

    return ". ".join(parts) + "." if parts else "Cash flow data not available."


def _growth_text(growth: float) -> str:
    if growth > 0.05:
        return f"grew {growth:.1%}"
    if growth < -0.05:
        return f"declined {growth:.1%}"
    return f"was flat ({growth:.1%})"

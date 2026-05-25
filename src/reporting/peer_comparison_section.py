"""Peer comparison report section — benchmarks company ratios against industry peers."""

from __future__ import annotations

from typing import Any


def build_peer_comparison_section(peer_comparison: dict[str, Any]) -> str:
    """Build the peer comparison analysis text.

    Args:
        peer_comparison: The peer_comparison dict from analyzed data.

    Returns:
        Human-readable peer comparison text.
    """
    peer_group = peer_comparison.get("peer_group", "unknown")
    peer_tickers = peer_comparison.get("peer_tickers", [])
    peers_loaded = peer_comparison.get("peers_loaded", 0)
    comparisons = peer_comparison.get("comparisons", {})

    if peer_group == "unknown" and not peers_loaded:
        return "No peer group data available for benchmarking."

    lines = []
    peer_label = ", ".join(peer_tickers[:5])
    if len(peer_tickers) > 5:
        peer_label += f" and {len(peer_tickers) - 5} more"

    lines.append(
        f"**Peer Group:** {peer_group} ({peers_loaded}/{len(peer_tickers)} peers loaded: {peer_label})"
    )
    lines.append("")

    if not comparisons:
        lines.append("Insufficient peer data for detailed ratio comparison.")
        return "\n".join(lines)

    above_peer: list[str] = []
    below_peer: list[str] = []
    in_line: list[str] = []

    for name, comp in sorted(comparisons.items()):
        assessment = comp.get("assessment", "")
        company_val = comp.get("company_value", 0)
        peer_median = comp.get("peer_median", 0)
        diff_pct = comp.get("diff_pct", 0)

        direction = "+" if diff_pct >= 0 else ""
        detail = f"{_friendly_name(name)}: {_fmt_val(name, company_val)} vs peer median {_fmt_val(name, peer_median)} ({direction}{diff_pct:.1%})"

        if assessment == "above_peer":
            above_peer.append(detail)
        elif assessment == "below_peer":
            below_peer.append(detail)
        else:
            in_line.append(detail)

    if above_peer:
        lines.append("**Above Peer Median:**")
        for item in above_peer:
            lines.append(f"- {item}")
        lines.append("")

    if in_line:
        lines.append("**In-Line with Peers:**")
        for item in in_line:
            lines.append(f"- {item}")
        lines.append("")

    if below_peer:
        lines.append("**Below Peer Median:**")
        for item in below_peer:
            lines.append(f"- {item}")
        lines.append("")

    return "\n".join(lines)


_FRIENDLY_NAMES: dict[str, str] = {
    "gross_margin": "Gross Margin",
    "operating_margin": "Operating Margin",
    "net_margin": "Net Margin",
    "roa": "ROA",
    "roe": "ROE",
    "ebitda_margin": "EBITDA Margin",
    "current_ratio": "Current Ratio",
    "quick_ratio": "Quick Ratio",
    "working_capital": "Working Capital",
    "operating_cf_ratio": "Operating CF Ratio",
    "debt_to_equity": "Debt-to-Equity",
    "debt_to_assets": "Debt-to-Assets",
    "interest_coverage": "Interest Coverage",
    "lt_debt_to_equity": "LT Debt-to-Equity",
    "asset_turnover": "Asset Turnover",
    "receivables_turnover": "Receivables Turnover",
    "inventory_turnover": "Inventory Turnover",
    "days_sales_outstanding": "Days Sales Outstanding",
    "fcf": "Free Cash Flow",
    "fcf_margin": "FCF Margin",
    "cf_to_ni": "CF-to-NI",
    "fcf_to_ni": "FCF-to-NI",
}

_RATIO_FORMATS: set[str] = {"days_sales_outstanding"}


def _friendly_name(key: str) -> str:
    return _FRIENDLY_NAMES.get(key, key)


def _fmt_val(key: str, val: float) -> str:
    if key in _RATIO_FORMATS:
        return f"{val:.1f} days"
    if key == "working_capital" or key == "fcf":
        return f"${val:,.0f}M"
    if abs(val) < 1:
        return f"{val:.1%}"
    return f"{val:.2f}x"

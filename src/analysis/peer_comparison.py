"""Peer group comparison engine — ratio benchmarking against industry peers.

Computes peer-group median ratios for a ticker using cached EDGAR data
from the samples directory. Falls back gracefully if peer data is unavailable.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from src.config import DATA_DIR

logger = logging.getLogger(__name__)

PEER_GROUPS_PATH = DATA_DIR / "peer_groups.json"
SAMPLES_DIR = DATA_DIR / "samples"

_RATIO_CATEGORIES = [
    (
        "profitability",
        ["gross_margin", "operating_margin", "net_margin", "roa", "roe", "ebitda_margin"],
    ),
    ("liquidity", ["current_ratio", "quick_ratio", "working_capital", "operating_cf_ratio"]),
    ("solvency", ["debt_to_equity", "debt_to_assets", "interest_coverage", "lt_debt_to_equity"]),
    (
        "efficiency",
        ["asset_turnover", "receivables_turnover", "inventory_turnover", "days_sales_outstanding"],
    ),
    ("cash_flow_quality", ["fcf", "fcf_margin", "cf_to_ni", "fcf_to_ni"]),
]


def _load_peer_tickers(ticker: str) -> list[str]:
    """Find which peer group a ticker belongs to.

    Returns all other tickers in the same group, sorted alphabetically.
    Returns empty list if ticker is not in any known group.
    """
    if not PEER_GROUPS_PATH.exists():
        return []

    groups = json.loads(PEER_GROUPS_PATH.read_text())
    for group_name, group_data in groups.items():
        peers = group_data.get("peers", [])
        if ticker.upper() in [p.upper() for p in peers]:
            return sorted(p.upper() for p in peers if p.upper() != ticker.upper())

    return []


def _parse_single_ratio(ratio_data: Any) -> float | None:
    """Extract the most recent value from a ratio data structure.

    Handles both the serialized form [{"period":"FY2024","value":0.4}] and the raw Period list.
    """
    if isinstance(ratio_data, list) and ratio_data:
        first = ratio_data[0]
        if isinstance(first, dict):
            return first.get("value")
        if hasattr(first, "value"):
            return first.value
    return None


def _load_peer_ratios(peer_ticker: str) -> dict[str, dict[str, float]] | None:
    """Load cached ratios for a peer ticker from local sample data.

    Returns dict of category -> {ratio_name: latest_value} or None.
    """
    sample_path = SAMPLES_DIR / f"{peer_ticker.lower()}_2020_2024.json"
    if not sample_path.exists():
        return None

    try:
        data = json.loads(sample_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None

    periods = data.get("periods", [])
    if not periods:
        return None

    from src.analysis.ratio_calculator import compute_all_ratios
    from src.parsing.parser import parse_financial_data

    try:
        parsed = parse_financial_data(data)
        if not parsed.get("periods"):
            return None
    except Exception as e:
        logger.debug("Failed to parse peer data for %s: %s", peer_ticker, e)
        return None

    try:
        raw_ratios = compute_all_ratios(parsed.get("periods", []))
    except Exception as e:
        logger.debug("Failed to compute peer ratios for %s: %s", peer_ticker, e)
        return None

    result: dict[str, dict[str, float]] = {}
    for category, metric_names in _RATIO_CATEGORIES:
        category_data = getattr(raw_ratios, category, None)
        if category_data is None:
            continue
        result[category] = {}
        for name in metric_names:
            points = getattr(category_data, name, [])
            if points:
                result[category][name] = points[-1].value
    return result


def _compute_median(values: list[float]) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    if n % 2 == 0:
        return (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2.0
    return sorted_vals[n // 2]


def compute_peer_benchmarks(ticker: str) -> dict[str, Any]:
    """Compute peer-group median ratios for benchmarking.

    Args:
        ticker: Stock ticker symbol.

    Returns:
        Dict with:
            peer_group: str (group name or "unknown")
            peer_tickers: list[str]
            medians: dict of category -> {ratio_name: median_value}
    """
    peer_tickers = _load_peer_tickers(ticker)
    if not peer_tickers:
        return {
            "peer_group": "unknown",
            "peer_tickers": [],
            "medians": {},
        }

    group_name = "unknown"
    if PEER_GROUPS_PATH.exists():
        groups = json.loads(PEER_GROUPS_PATH.read_text())
        for name, gd in groups.items():
            if ticker.upper() in [p.upper() for p in gd.get("peers", [])]:
                group_name = name
                break

    logger.info("Computing peer benchmarks for %s (%d peers)", ticker, len(peer_tickers))

    all_peer_values: dict[str, dict[str, list[float]]] = {}
    loaded = 0
    for pt in peer_tickers:
        ratios = _load_peer_ratios(pt)
        if ratios is None:
            continue
        loaded += 1
        for category, metrics in ratios.items():
            if category not in all_peer_values:
                all_peer_values[category] = {}
            for name, value in metrics.items():
                if name not in all_peer_values[category]:
                    all_peer_values[category][name] = []
                all_peer_values[category][name].append(value)

    medians: dict[str, dict[str, float]] = {}
    for category, metrics in all_peer_values.items():
        medians[category] = {}
        for name, values in metrics.items():
            medians[category][name] = _compute_median(values)

    logger.info("Peer benchmarks computed from %d peers for %s", loaded, ticker)

    return {
        "peer_group": group_name,
        "peer_tickers": peer_tickers,
        "peers_loaded": loaded,
        "medians": medians,
    }


def compare_to_peers(
    company_ratios: dict[str, Any],
    peer_benchmarks: dict[str, Any],
) -> dict[str, Any]:
    """Compare company ratios to peer medians.

    Args:
        company_ratios: Serialized ratios dict (from analyzer output).
        peer_benchmarks: Output of compute_peer_benchmarks.

    Returns:
        Dict with per-ratio comparisons:
            {ratio_name: {company_value, peer_median, percentile, assessment}}
    """
    medians = peer_benchmarks.get("medians", {})
    comparisons: dict[str, dict[str, Any]] = {}

    for category, metric_names in _RATIO_CATEGORIES:
        cat_medians = medians.get(category, {})
        cat_ratios = company_ratios.get(category, {})
        for name in metric_names:
            company_series = cat_ratios.get(name, [])
            peer_median = cat_medians.get(name)

            if not company_series or peer_median is None:
                continue

            company_value = (
                company_series[-1].get("value")
                if isinstance(company_series, list) and company_series
                else None
            )
            if company_value is None:
                continue

            diff_pct = (company_value - peer_median) / abs(peer_median) if peer_median != 0 else 0

            if abs(diff_pct) < 0.10:
                assessment = "in-line"
            elif diff_pct > 0:
                assessment = "above_peer" if _higher_is_better(name) else "below_peer"
            else:
                assessment = "below_peer" if _higher_is_better(name) else "above_peer"

            comparisons[name] = {
                "company_value": company_value,
                "peer_median": peer_median,
                "diff_pct": round(diff_pct, 4),
                "assessment": assessment,
            }

    return comparisons


_HIGHER_IS_BETTER = {
    "gross_margin",
    "operating_margin",
    "net_margin",
    "roa",
    "roe",
    "ebitda_margin",
    "current_ratio",
    "quick_ratio",
    "operating_cf_ratio",
    "interest_coverage",
    "asset_turnover",
    "receivables_turnover",
    "inventory_turnover",
    "fcf",
    "fcf_margin",
    "cf_to_ni",
    "fcf_to_ni",
    "working_capital",
}


_LOWER_IS_BETTER = {
    "debt_to_equity",
    "debt_to_assets",
    "lt_debt_to_equity",
    "days_sales_outstanding",
}


def _higher_is_better(ratio_name: str) -> bool:
    return ratio_name in _HIGHER_IS_BETTER

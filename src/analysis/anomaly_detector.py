"""Anomaly detector — detect year-over-year volatility spikes > 20%."""

from __future__ import annotations

from typing import Any

from src.config import VOLATILITY_THRESHOLD


def detect_volatility_spikes(
    values: list[float],
    periods: list[str],
    item_name: str,
    threshold: float = VOLATILITY_THRESHOLD,
) -> list[dict[str, Any]]:
    """Detect items with >threshold YoY change.

    Args:
        values: Chronological values (oldest first).
        periods: Corresponding period labels.
        item_name: Name of the line item being checked.
        threshold: Volatility threshold as decimal (default 0.20 = 20%).

    Returns:
        List of anomaly dicts with item, period, prev_value, curr_value, change_pct.
    """
    anomalies: list[dict[str, Any]] = []
    for i in range(1, len(values)):
        prev = values[i - 1]
        curr = values[i]
        if abs(prev) < 1:
            continue
        change = (curr - prev) / abs(prev)
        if abs(change) > threshold:
            anomalies.append(
                {
                    "item": item_name,
                    "period": periods[i] if i < len(periods) else "",
                    "prev_value": prev,
                    "curr_value": curr,
                    "change_pct": round(change, 4),
                }
            )
    return anomalies


def detect_anomalies(periods: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Run anomaly detection on key line items across all periods.

    Returns:
        Sorted list of anomaly dicts by absolute change descending.
    """
    labels = [f"FY{p.get('fiscal_year', '')}" for p in periods]
    labels_chrono = list(reversed(labels))

    items_to_check = [
        ("revenue", "income_statement"),
        ("net_income", "income_statement"),
        ("operating_cf", "cash_flow_statement"),
        ("total_assets", "balance_sheet"),
        ("total_liabilities", "balance_sheet"),
    ]

    all_anomalies: list[dict[str, Any]] = []
    for item_name, stmt_type in items_to_check:
        values: list[float] = []
        for p in periods:
            stmts = p.get("statements", {})
            values.append(stmts.get(stmt_type, {}).get(item_name, 0))

        anomalies = detect_volatility_spikes(list(reversed(values)), labels_chrono, item_name)
        all_anomalies.extend(anomalies)

    all_anomalies.sort(key=lambda a: abs(a["change_pct"]), reverse=True)
    return all_anomalies

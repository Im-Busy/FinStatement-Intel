"""Compute financial ratios, analyze trends, detect anomalies and red flags.

Covers 5 ratio categories: profitability, liquidity, solvency,
efficiency, and cash flow quality.
"""

from __future__ import annotations

import logging
from typing import Any

from src.analysis.anomaly_detector import detect_anomalies
from src.analysis.cross_validator import run_cross_validation
from src.analysis.ratio_calculator import compute_all_ratios
from src.analysis.red_flag_detector import detect_all_red_flags
from src.analysis.scorer import compute_scorecard
from src.analysis.trend_analyzer import analyze_trends

logger = logging.getLogger(__name__)


def analyze_financial_data(parsed_data: dict[str, Any]) -> dict[str, Any]:
    """Analyze parsed financial statements for ratios, trends, and quality.

    Args:
        parsed_data: JSON from the parser agent.

    Returns:
        Analysis result JSON with ratios, trends, and red flags.
    """
    logger.info(
        "Analyzing financial data for %s",
        parsed_data.get("company", {}).get("ticker", "unknown"),
    )

    periods = parsed_data.get("periods", [])
    if not periods:
        return {
            "status": "WARNING",
            "message": "No period data to analyze",
            "company": parsed_data.get("company", {}),
            "periods_analyzed": 0,
            "analysis_period": "",
            "ratios": {},
            "trends": {},
            "red_flags": [],
            "cross_validation": [],
            "anomalies": [],
            "scorecard": {
                "profitability": 0,
                "liquidity": 0,
                "solvency": 0,
                "efficiency": 0,
                "cash_flow_quality": 0,
                "total": 0,
                "assessment": "N/A",
            },
            "peer_comparison": {
                "peer_group": "unknown",
                "peer_tickers": [],
                "peers_loaded": 0,
                "comparisons": {},
            },
        }

    ratios = compute_all_ratios(periods)
    trends = analyze_trends(parsed_data, ratios)
    red_flags = detect_all_red_flags(periods, ratios)
    cross_validation = run_cross_validation(periods)
    anomalies = detect_anomalies(periods)
    scorecard = compute_scorecard(ratios)

    ticker = parsed_data.get("company", {}).get("ticker", "")
    peer_benchmarks = {}
    peer_comparison = {}
    if ticker:
        try:
            from src.analysis.peer_comparison import compare_to_peers, compute_peer_benchmarks

            peer_benchmarks = compute_peer_benchmarks(ticker)
            serialized_ratios = _serialize_ratios(ratios)
            peer_comparison = compare_to_peers(serialized_ratios, peer_benchmarks)
        except Exception as e:
            logger.debug("Peer comparison unavailable for %s: %s", ticker, e)

    is_warning = parsed_data.get("status") == "WARNING"

    return {
        "status": "WARNING" if is_warning else "SUCCESS",
        "company": parsed_data.get("company", {}),
        "periods_analyzed": len(periods),
        "analysis_period": f"FY{periods[0].get('fiscal_year', '')}-FY{periods[-1].get('fiscal_year', '')}",
        "ratios": _serialize_ratios(ratios),
        "trends": _serialize_trends(trends),
        "cross_validation": _serialize_cross_validations(cross_validation),
        "red_flags": _serialize_red_flags(red_flags),
        "anomalies": anomalies,
        "scorecard": {
            "profitability": scorecard.profitability,
            "liquidity": scorecard.liquidity,
            "solvency": scorecard.solvency,
            "efficiency": scorecard.efficiency,
            "cash_flow_quality": scorecard.cash_flow_quality,
            "total": scorecard.total,
            "assessment": scorecard.assessment,
        },
        "peer_comparison": {
            "peer_group": peer_benchmarks.get("peer_group", "unknown"),
            "peer_tickers": peer_benchmarks.get("peer_tickers", []),
            "peers_loaded": peer_benchmarks.get("peers_loaded", 0),
            "comparisons": peer_comparison,
        },
    }


def _serialize_ratios(ratios: dict) -> dict:
    result: dict[str, dict] = {}
    for category, metrics in ratios.items():
        result[category] = {}
        for name, points in metrics.items():
            result[category][name] = [
                {"period": p.period, "value": p.value, "unit": p.unit} for p in points
            ]
    return result


def _serialize_trends(trends: dict) -> dict:
    result: dict[str, Any] = {}
    for key, val in trends.items():
        if isinstance(val, list):
            result[key] = [{"period": p.period, "value": p.value} for p in val]
        else:
            result[key] = val
    return result


def _serialize_cross_validations(validations: list) -> list:
    return [
        {
            "check_name": v.check_name,
            "result": v.result,
            "detail": v.detail,
            "periods_evaluated": v.periods_evaluated,
        }
        for v in validations
    ]


def _serialize_red_flags(flags: list) -> list:
    return [
        {
            "type": f.type,
            "severity": f.severity.value,
            "description": f.description,
            "periods_affected": f.periods_affected,
            "current_value": f.current_value,
            "threshold": f.threshold,
            "historical_context": f.historical_context,
        }
        for f in flags
    ]

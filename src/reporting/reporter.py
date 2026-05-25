"""Generate comprehensive financial analysis reports.

Produces structured reports with executive summary, financial health
scorecard, detailed findings, red flags, strengths, and recommendations.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from src.reporting.executive_summary import generate_executive_summary
from src.reporting.findings_section import build_findings
from src.reporting.peer_comparison_section import build_peer_comparison_section
from src.reporting.ratio_section import build_ratio_analysis
from src.reporting.recommendations import build_recommendations
from src.reporting.red_flags_section import build_red_flags_section
from src.reporting.scorecard_builder import build_scorecard
from src.reporting.strengths_section import build_strengths

logger = logging.getLogger(__name__)


def generate_report(analyzed_data: dict[str, Any]) -> dict[str, Any]:
    """Generate a financial analysis report from analyzed data.

    Args:
        analyzed_data: JSON from the analyzer agent.

    Returns:
        Report JSON with executive summary, scorecard, and findings.
    """
    logger.info(
        "Generating analysis report for %s",
        analyzed_data.get("company", {}).get("ticker", "unknown"),
    )

    if analyzed_data.get("status") == "ERROR":
        return {
            "status": "ERROR",
            "message": "Cannot generate report: analysis data contains errors",
            "report": {},
        }

    company = analyzed_data.get("company", {})
    ratios = analyzed_data.get("ratios", {})
    scorecard = analyzed_data.get("scorecard", {})
    red_flags = analyzed_data.get("red_flags", [])
    trends = analyzed_data.get("trends", {})
    cross_validation = analyzed_data.get("cross_validation", [])
    peer_comparison = analyzed_data.get("peer_comparison", {})

    exec_summary = generate_executive_summary(analyzed_data)
    scorecard_data = build_scorecard(scorecard)
    findings = build_findings(analyzed_data)
    ratio_text = build_ratio_analysis(ratios, trends)
    formatted_flags = build_red_flags_section(red_flags)
    strengths = build_strengths(ratios, cross_validation)
    recommendations = build_recommendations(ratios, red_flags, scorecard)
    peer_section = build_peer_comparison_section(peer_comparison)

    return {
        "status": "SUCCESS",
        "report": {
            "company": company,
            "periods_analyzed": analyzed_data.get("analysis_period", ""),
            "generated_at": datetime.now(UTC).isoformat(),
            "executive_summary": exec_summary,
            "scorecard": scorecard_data,
            "detailed_findings": findings,
            "ratio_analysis": ratio_text,
            "red_flags": formatted_flags,
            "strengths": strengths,
            "recommendations": recommendations,
            "cross_validation": cross_validation,
            "peer_comparison": peer_section,
        },
        "html": _render_report_html(
            company,
            analyzed_data,
            exec_summary,
            scorecard_data,
            findings,
            ratio_text,
            formatted_flags,
            strengths,
            recommendations,
            cross_validation,
            peer_section,
        ),
    }


def _render_report_html(
    company: dict[str, Any],
    analyzed_data: dict[str, Any],
    exec_summary: dict[str, Any],
    scorecard_data: dict[str, Any],
    findings: dict[str, str],
    ratio_text: str,
    formatted_flags: list[dict[str, Any]],
    strengths: list[str],
    recommendations: list[str],
    cross_validation: Any,
    peer_section: str = "",
) -> str:
    """Render the report as an HTML string using the html_renderer."""
    from src.reporting.html_renderer import render_html

    report_data = {
        "report": {
            "company": company,
            "periods_analyzed": analyzed_data.get("analysis_period", ""),
            "generated_at": analyzed_data.get("generated_at", ""),
            "executive_summary": exec_summary,
            "scorecard": scorecard_data,
            "detailed_findings": findings,
            "ratio_analysis": ratio_text,
            "red_flags": formatted_flags,
            "strengths": strengths,
            "recommendations": recommendations,
            "cross_validation": cross_validation,
            "peer_comparison": peer_section,
        },
    }
    return render_html(report_data)

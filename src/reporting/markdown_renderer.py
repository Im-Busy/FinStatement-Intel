"""Markdown renderer — converts report data to formatted Markdown document."""

from __future__ import annotations

from typing import Any


def render_markdown(report_data: dict[str, Any]) -> str:
    """Render the analysis report as a Markdown document.

    Args:
        report_data: Complete report JSON from the reporter.

    Returns:
        Formatted Markdown string.
    """
    company = report_data.get("company", {})
    lines: list[str] = []

    lines.append(
        f"# Financial Statement Analysis: {company.get('name', company.get('ticker', 'Unknown'))}"
    )
    lines.append("")
    lines.append(f"**Ticker:** {company.get('ticker', 'N/A')}  ")
    lines.append(f"**Periods Analyzed:** {report_data.get('periods_analyzed', 'N/A')}  ")
    lines.append(f"**Generated:** {report_data.get('generated_at', 'N/A')}  ")
    lines.append("")

    es = report_data.get("executive_summary", {})
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"**Overall Assessment:** {es.get('overall_assessment', 'N/A')}")
    lines.append("")
    lines.append("### Top Findings")
    lines.append("")
    for finding in es.get("top_findings", []):
        lines.append(f"- {finding}")
    lines.append("")

    sc = report_data.get("scorecard", {})
    lines.append("## Financial Health Scorecard")
    lines.append("")
    lines.append("| Dimension | Score | Max |")
    lines.append("|-----------|-------|-----|")
    for dim in ["profitability", "liquidity", "solvency", "efficiency", "cash_flow_quality"]:
        lines.append(f"| {dim.replace('_', ' ').title()} | {sc.get(dim, 0)} | 20 |")
    lines.append(f"| **Total** | **{sc.get('total', 0)}** | **100** |")
    lines.append(f"| **Assessment** | **{sc.get('assessment', '')}** | |")
    lines.append("")

    findings = report_data.get("detailed_findings", {})
    lines.append("## Detailed Findings")
    lines.append("")
    for stmt_type, text in findings.items():
        lines.append(f"### {stmt_type.replace('_', ' ').title()}")
        lines.append("")
        lines.append(text)
        lines.append("")

    lines.append("## Ratio Analysis")
    lines.append("")
    lines.append(report_data.get("ratio_analysis", "No ratio analysis data available."))
    lines.append("")

    flags = report_data.get("red_flags", [])
    lines.append("## Red Flags & Risks")
    lines.append("")
    if flags:
        for flag in flags:
            severity = flag.get("severity", "").upper()
            lines.append(f"- **[{severity}]** {flag.get('description', '')}")
            lines.append(f"  - Context: {flag.get('historical_context', 'N/A')}")
            lines.append(f"  - Periods: {', '.join(flag.get('periods_affected', []))}")
            lines.append("")
    else:
        lines.append("No red flags detected.")
    lines.append("")

    strengths = report_data.get("strengths", [])
    lines.append("## Strengths")
    lines.append("")
    for s in strengths:
        lines.append(f"- {s}")
    lines.append("")

    recs = report_data.get("recommendations", [])
    lines.append("## Recommendations")
    lines.append("")
    for i, r in enumerate(recs, 1):
        lines.append(f"{i}. {r}")
    lines.append("")

    return "\n".join(lines)

"""HTML report renderer — converts analyzed report data into a standalone HTML document."""

from __future__ import annotations

from typing import Any


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )


def _render_red_flag_html(flag: dict[str, Any]) -> str:
    severity = flag.get("severity", "info")
    color = {"critical": "#dc3545", "warning": "#ffc107", "info": "#17a2b8"}.get(
        severity, "#6c757d"
    )
    periods = ", ".join(flag.get("periods_affected", []))
    return f"""
    <div class="red-flag" style="border-left: 4px solid {color}; padding: 8px 12px; margin: 8px 0; background: #f8f9fa;">
        <strong style="color: {color};">{severity.upper()}</strong> — {_escape(flag.get("type", ""))}
        <p style="margin: 4px 0 0 0; font-size: 14px;">{_escape(flag.get("description", ""))}</p>
        {'<p style="margin: 2px 0 0 0; font-size: 12px; color: #6c757d;">Periods: ' + _escape(periods) + "</p>" if periods else ""}
    </div>"""


def render_html(report_data: dict[str, Any]) -> str:
    """Render a financial analysis report as a standalone HTML document.

    Args:
        report_data: The analyzed data dict (output of analyze_financial_data).

    Returns:
        HTML string.
    """
    report = report_data.get("report", report_data)
    company = report.get("company", {})
    company_name = company.get("name", "Unknown")
    ticker = company.get("ticker", "")
    periods = report.get("periods_analyzed", "")
    generated = report.get("generated_at", "")

    executive_summary = report.get("executive_summary", {})
    findings = executive_summary.get("top_findings", [])
    assessment = executive_summary.get("overall_assessment", "N/A")

    scorecard = report.get("scorecard", {})
    detailed_findings = report.get("detailed_findings", {})
    ratio_analysis = report.get("ratio_analysis", "")
    red_flags = report.get("red_flags", [])
    strengths = report.get("strengths", [])
    recommendations = report.get("recommendations", [])
    cross_validation = report.get("cross_validation", {})
    peer_comparison = report.get("peer_comparison", "")

    findings_html = ""
    for i, finding in enumerate(findings):
        findings_html += f"<li>{_escape(finding)}</li>"

    scorecard_rows = ""
    dims = [
        ("profitability", "Profitability"),
        ("liquidity", "Liquidity"),
        ("solvency", "Solvency"),
        ("efficiency", "Efficiency"),
        ("cash_flow_quality", "Cash Flow Quality"),
    ]
    for key, label in dims:
        val = scorecard.get(key, 0)
        bar_width = min(val * 5, 100)
        color = "#28a745" if val >= 16 else "#ffc107" if val >= 10 else "#dc3545"
        scorecard_rows += f"""
        <tr>
            <td style="width: 200px;"><strong>{label}</strong></td>
            <td style="width: 80px; text-align: center;">{val}/20</td>
            <td><div style="background: #e9ecef; border-radius: 4px; height: 20px; width: 300px;">
                <div style="background: {color}; border-radius: 4px; height: 20px; width: {bar_width}px;"></div>
            </div></td>
        </tr>"""

    details_sections = ""
    for stmt_key, label in [
        ("income_statement", "Income Statement"),
        ("balance_sheet", "Balance Sheet"),
        ("cash_flow_statement", "Cash Flow Statement"),
    ]:
        content = detailed_findings.get(stmt_key, "")
        if content:
            details_sections += f"""
            <div class="section">
                <h3>{label}</h3>
                <p>{_escape(content)}</p>
            </div>"""

    flags_html = ""
    if red_flags:
        for flag in red_flags:
            flags_html += _render_red_flag_html(flag)
    else:
        flags_html = "<p style='color: #28a745;'>No red flags detected.</p>"

    strengths_html = ""
    for s in strengths:
        strengths_html += f"<li>{_escape(s)}</li>"

    recs_html = ""
    for i, r in enumerate(recommendations, 1):
        recs_html += f"<li>{_escape(r)}</li>"

    cv_sections = ""
    if isinstance(cross_validation, dict):
        for check_name, check_data in cross_validation.items():
            result = (
                check_data.get("result", "N/A") if isinstance(check_data, dict) else str(check_data)
            )
            detail = check_data.get("detail", "") if isinstance(check_data, dict) else ""
            color = {"PASS": "#28a745", "WARN": "#ffc107", "FAIL": "#dc3545"}.get(result, "#6c757d")
            cv_sections += f"""
        <tr>
            <td>{_escape(check_name)}</td>
            <td><span style="color: {color}; font-weight: bold;">{result}</span></td>
            <td style="font-size: 13px;">{_escape(detail)}</td>
        </tr>"""
    elif isinstance(cross_validation, list):
        for item in cross_validation:
            if isinstance(item, dict):
                check_name = item.get("check_name", item.get("type", ""))
                result = item.get("result", "N/A")
                detail = item.get("detail", "")
            else:
                check_name = str(item)
                result = "N/A"
                detail = ""
            color = {"PASS": "#28a745", "WARN": "#ffc107", "FAIL": "#dc3545"}.get(result, "#6c757d")
            cv_sections += f"""
        <tr>
            <td>{_escape(check_name)}</td>
            <td><span style="color: {color}; font-weight: bold;">{result}</span></td>
            <td style="font-size: 13px;">{_escape(detail)}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Financial Analysis — {_escape(company_name)}{" (" + _escape(ticker) + ")" if ticker else ""}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; color: #212529; line-height: 1.6; }}
        h1 {{ font-size: 28px; border-bottom: 2px solid #0d6efd; padding-bottom: 8px; }}
        h2 {{ font-size: 22px; margin-top: 32px; color: #0d6efd; }}
        h3 {{ font-size: 18px; color: #495057; }}
        .meta {{ color: #6c757d; font-size: 14px; margin-bottom: 24px; }}
        .section {{ margin: 16px 0; }}
        table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
        th, td {{ padding: 8px 12px; border: 1px solid #dee2e6; text-align: left; }}
        th {{ background: #f8f9fa; }}
        .assessment {{ font-size: 20px; font-weight: bold; padding: 12px 16px; border-radius: 6px; display: inline-block; }}
        .assessment-Strong {{ background: #d4edda; color: #155724; }}
        .assessment-Adequate {{ background: #fff3cd; color: #856404; }}
        .assessment-Concerning {{ background: #f8d7da; color: #721c24; }}
        .assessment-Critical {{ background: #dc3545; color: #fff; }}
        ul {{ padding-left: 20px; }}
        li {{ margin: 6px 0; }}
    </style>
</head>
<body>
    <h1>Financial Analysis Report</h1>
    <div class="meta">
        <strong>{_escape(company_name)}</strong> ({_escape(ticker)}) — {_escape(periods)}
        {" — Generated: " + _escape(generated) if generated else ""}
    </div>

    <div class="section">
        <h2>Executive Summary</h2>
        <div class="assessment assessment-{assessment}">{assessment}</div>
        <h3>Key Findings</h3>
        <ul>{findings_html}</ul>
    </div>

    <div class="section">
        <h2>Financial Health Scorecard</h2>
        <table>
            <thead><tr><th>Dimension</th><th>Score</th><th></th></tr></thead>
            <tbody>{scorecard_rows}</tbody>
            <tfoot>
                <tr style="background: #e9ecef;">
                    <td><strong>Total</strong></td>
                    <td style="text-align: center;"><strong>{scorecard.get("total", 0)}/100</strong></td>
                    <td><strong>{scorecard.get("assessment", "")}</strong></td>
                </tr>
            </tfoot>
        </table>
    </div>

    <div class="section">
        <h2>Detailed Findings</h2>
        {details_sections}
    </div>

    <div class="section">
        <h2>Ratio Analysis</h2>
        <p>{_escape(ratio_analysis) if ratio_analysis else "See detailed ratio tables below."}</p>
    </div>

    <div class="section">
        <h2>Red Flags &amp; Risks</h2>
        {flags_html}
    </div>

    <div class="section">
        <h2>Cross-Statement Validation</h2>
        <table>
            <thead><tr><th>Check</th><th>Result</th><th>Detail</th></tr></thead>
            <tbody>{cv_sections}</tbody>
        </table>
    </div>

    <div class="section">
        <h2>Peer Comparison</h2>
        <div>{_escape(peer_comparison).replace("\n", "<br>") if peer_comparison else "No peer data available."}</div>
    </div>

    <div class="section">
        <h2>Strengths</h2>
        <ul>{strengths_html}</ul>
    </div>

    <div class="section">
        <h2>Recommendations</h2>
        <ol>{recs_html}</ol>
    </div>

    <hr style="margin-top: 40px;">
    <p style="color: #adb5bd; font-size: 12px; text-align: center;">
        Generated by reading-CFS-IS-BS — Financial Statement Analysis Pipeline
    </p>
</body>
</html>"""

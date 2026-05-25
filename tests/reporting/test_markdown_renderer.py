"""Tests for markdown renderer."""

from src.reporting.markdown_renderer import render_markdown

REPORT_DATA = {
    "company": {"name": "TestCo Inc.", "ticker": "TEST"},
    "periods_analyzed": "FY2022-FY2024",
    "generated_at": "2026-05-25T18:00:00Z",
    "executive_summary": {
        "top_findings": ["Strong cash flow generation", "Healthy margins"],
        "overall_assessment": "Adequate",
    },
    "scorecard": {
        "profitability": 16,
        "liquidity": 14,
        "solvency": 12,
        "efficiency": 15,
        "cash_flow_quality": 17,
        "total": 74,
        "assessment": "Adequate",
    },
    "detailed_findings": {
        "income_statement": "Revenue grew moderately.",
        "balance_sheet": "Assets increased steadily.",
        "cash_flow_statement": "Operating CF remains strong.",
    },
    "ratio_analysis": "Gross margin is healthy. Interest coverage is strong.",
    "red_flags": [
        {
            "type": "excessive_leverage",
            "severity": "warning",
            "description": "D/E ratio 1.50 exceeds threshold",
            "historical_context": "persistent since FY2022",
            "periods_affected": ["FY2022", "FY2023", "FY2024"],
        },
    ],
    "strengths": ["Strong FCF margin", "High earnings quality"],
    "recommendations": ["Monitor D/E ratio", "Review capex adequacy"],
    "cross_validation": [],
}


class TestRenderMarkdown:
    def test_renders_header(self):
        result = render_markdown(REPORT_DATA)
        assert "# Financial Statement Analysis: TestCo Inc." in result

    def test_renders_metadata(self):
        result = render_markdown(REPORT_DATA)
        assert "**Ticker:** TEST" in result
        assert "FY2022-FY2024" in result

    def test_renders_executive_summary(self):
        result = render_markdown(REPORT_DATA)
        assert "## Executive Summary" in result
        assert "Adequate" in result
        assert "Strong cash flow generation" in result

    def test_renders_scorecard_table(self):
        result = render_markdown(REPORT_DATA)
        assert "## Financial Health Scorecard" in result
        assert "| Profitability | 16 | 20 |" in result
        assert "| **Total** | **74** | **100** |" in result

    def test_renders_detailed_findings(self):
        result = render_markdown(REPORT_DATA)
        assert "## Detailed Findings" in result
        assert "### Income Statement" in result
        assert "### Balance Sheet" in result
        assert "### Cash Flow Statement" in result

    def test_renders_ratio_analysis(self):
        result = render_markdown(REPORT_DATA)
        assert "## Ratio Analysis" in result

    def test_renders_red_flags(self):
        result = render_markdown(REPORT_DATA)
        assert "## Red Flags & Risks" in result
        assert "[WARNING]" in result

    def test_renders_no_red_flags(self):
        data = {**REPORT_DATA, "red_flags": []}
        result = render_markdown(data)
        assert "No red flags detected" in result

    def test_renders_strengths(self):
        result = render_markdown(REPORT_DATA)
        assert "## Strengths" in result
        assert "Strong FCF margin" in result

    def test_renders_recommendations(self):
        result = render_markdown(REPORT_DATA)
        assert "## Recommendations" in result
        assert "1. Monitor D/E ratio" in result

    def test_returns_string(self):
        result = render_markdown(REPORT_DATA)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_minimal_data(self):
        data = {"company": {}}
        result = render_markdown(data)
        assert isinstance(result, str)
        assert "# Financial Statement Analysis" in result

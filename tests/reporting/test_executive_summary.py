"""Tests for executive summary generator."""

from src.reporting.executive_summary import generate_executive_summary


class TestGenerateExecutiveSummary:
    def test_no_issues(self):
        data = {
            "red_flags": [],
            "scorecard": {"total": 85, "assessment": "Strong"},
            "trends": {
                "revenue_yoy_growth": [{"period": "FY2024", "value": 0.08}],
            },
            "ratios": {
                "cash_flow_quality": {
                    "cf_to_ni": [{"value": 1.5}, {"value": 1.6}],
                },
            },
        }
        result = generate_executive_summary(data)
        assert result["overall_assessment"] == "Strong"
        assert len(result["top_findings"]) <= 3

    def test_critical_flags_first(self):
        data = {
            "red_flags": [
                {"severity": "critical", "description": "CRITICAL: negative equity"},
                {"severity": "critical", "description": "CRITICAL: can't cover interest"},
                {"severity": "warning", "description": "WARNING: high leverage"},
            ],
            "scorecard": {"total": 20, "assessment": "Critical"},
            "trends": {},
            "ratios": {},
        }
        result = generate_executive_summary(data)
        top = result["top_findings"]
        assert len(top) == 3
        assert "CRITICAL" in top[0]
        assert "CRITICAL" in top[1]

    def test_limit_three_findings(self):
        data = {
            "red_flags": [
                {"severity": "critical", "description": "Flag 1"},
                {"severity": "critical", "description": "Flag 2"},
                {"severity": "warning", "description": "Flag 3"},
                {"severity": "warning", "description": "Flag 4"},
            ],
            "scorecard": {"total": 30, "assessment": "Critical"},
            "trends": {},
            "ratios": {},
        }
        result = generate_executive_summary(data)
        assert len(result["top_findings"]) == 3

    def test_strong_earnings_quality(self):
        data = {
            "red_flags": [],
            "scorecard": {"total": 80, "assessment": "Strong"},
            "trends": {"revenue_yoy_growth": [{"value": 0.03}]},
            "ratios": {
                "cash_flow_quality": {
                    "cf_to_ni": [{"value": 1.5}, {"value": 1.6}],
                },
            },
        }
        result = generate_executive_summary(data)
        findings = " ".join(result["top_findings"])
        assert "Strong earnings quality" in findings or "earnings quality" in findings.lower()

    def test_strong_revenue_growth(self):
        data = {
            "red_flags": [],
            "scorecard": {"total": 80, "assessment": "Strong"},
            "trends": {"revenue_yoy_growth": [{"value": 0.10}, {"value": 0.12}]},
            "ratios": {
                "cash_flow_quality": {
                    "cf_to_ni": [{"value": 0.0}],
                },
            },
        }
        result = generate_executive_summary(data)
        findings = " ".join(result["top_findings"])
        assert "Strong revenue growth" in findings

    def test_declining_revenue(self):
        data = {
            "red_flags": [],
            "scorecard": {"total": 50, "assessment": "Concerning"},
            "trends": {"revenue_yoy_growth": [{"value": -0.10}]},
            "ratios": {
                "cash_flow_quality": {
                    "cf_to_ni": [{"value": 0.0}],
                },
            },
        }
        result = generate_executive_summary(data)
        findings = " ".join(result["top_findings"])
        assert "Revenue declining" in findings

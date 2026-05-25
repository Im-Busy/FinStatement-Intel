"""Tests for red flags section builder."""

from src.reporting.red_flags_section import build_red_flags_section


class TestBuildRedFlagsSection:
    def test_sorted_critical_first(self):
        flags = [
            {"type": "warning", "severity": "warning", "description": "Warning flag"},
            {"type": "critical", "severity": "critical", "description": "Critical flag"},
        ]
        result = build_red_flags_section(flags)
        assert result[0]["severity"] == "critical"
        assert result[1]["severity"] == "warning"

    def test_persistent_context(self):
        flags = [
            {
                "type": "excessive_leverage",
                "severity": "warning",
                "description": "High leverage",
                "periods_affected": ["FY2020", "FY2021", "FY2022", "FY2023", "FY2024"],
            },
        ]
        result = build_red_flags_section(flags)
        assert "persistent since FY2020" in result[0]["historical_context"]

    def test_new_context(self):
        flags = [
            {
                "type": "liquidity_crisis_risk",
                "severity": "critical",
                "description": "Liquidity at risk",
                "periods_affected": ["FY2024"],
            },
        ]
        result = build_red_flags_section(flags)
        assert "new in FY2024" in result[0]["historical_context"]

    def test_ongoing_context(self):
        flags = [
            {
                "type": "demand_problem",
                "severity": "warning",
                "description": "Demand issue",
                "periods_affected": ["FY2023", "FY2024"],
            },
        ]
        result = build_red_flags_section(flags)
        assert "ongoing" in result[0]["historical_context"]

    def test_preserved_context(self):
        flags = [
            {
                "type": "excessive_leverage",
                "severity": "warning",
                "description": "High leverage",
                "historical_context": "Since inception",
                "periods_affected": [],
            },
        ]
        result = build_red_flags_section(flags)
        assert result[0]["historical_context"] == "Since inception"

    def test_empty(self):
        result = build_red_flags_section([])
        assert result == []

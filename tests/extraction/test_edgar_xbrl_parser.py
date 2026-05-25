"""Tests for XBRL company facts parser."""

from src.extraction.edgar_xbrl_parser import (
    classify_concept,
    extract_fact_values,
    parse_company_facts,
)
from src.models.enums import StatementType

SINGLE_FACT = {
    "label": "Revenues",
    "units": {
        "USD": [
            {"fy": 2024, "fp": "FY", "end": "2024-09-30", "val": 100000, "form": "10-K"},
            {"fy": 2023, "fp": "FY", "end": "2023-09-30", "val": 95000, "form": "10-K"},
            {"fy": 2022, "fp": "FY", "end": "2022-09-30", "val": 90000, "form": "10-K"},
            {"fy": 2021, "fp": "FY", "end": "2021-09-30", "val": 85000, "form": "10-K"},
            {"fy": 2020, "fp": "FY", "end": "2020-09-30", "val": 80000, "form": "10-K"},
        ]
    },
}

FACTS_FULL = {
    "cik": 320193,
    "entityName": "Apple Inc.",
    "facts": {
        "us-gaap": {
            "Revenues": {
                "label": "Revenues",
                "units": {
                    "USD": [
                        {
                            "fy": 2024,
                            "fp": "FY",
                            "end": "2024-09-30",
                            "val": 391035,
                            "form": "10-K",
                        },
                        {
                            "fy": 2023,
                            "fp": "FY",
                            "end": "2023-09-30",
                            "val": 383285,
                            "form": "10-K",
                        },
                    ]
                },
            },
            "Assets": {
                "label": "Assets",
                "units": {
                    "USD": [
                        {
                            "fy": 2024,
                            "fp": "FY",
                            "end": "2024-09-30",
                            "val": 364980,
                            "form": "10-K",
                        },
                    ]
                },
            },
            "NetCashProvidedByUsedInOperatingActivities": {
                "label": "Operating CF",
                "units": {
                    "USD": [
                        {
                            "fy": 2024,
                            "fp": "FY",
                            "end": "2024-09-30",
                            "val": 118254,
                            "form": "10-K",
                        },
                    ]
                },
            },
        }
    },
}


class TestClassifyConcept:
    def test_is_concept(self):
        assert classify_concept("Revenues") == StatementType.INCOME_STATEMENT

    def test_bs_concept(self):
        assert classify_concept("Assets") == StatementType.BALANCE_SHEET

    def test_cfs_concept(self):
        assert (
            classify_concept("NetCashProvidedByUsedInOperatingActivities")
            == StatementType.CASH_FLOW_STATEMENT
        )

    def test_unknown_concept(self):
        assert classify_concept("SomeWeirdThing") is None


class TestExtractFactValues:
    def test_extracts_all_periods(self):
        values = extract_fact_values(SINGLE_FACT, periods=10)
        assert len(values) == 5

    def test_limits_periods(self):
        values = extract_fact_values(SINGLE_FACT, periods=3)
        assert len(values) == 3

    def test_sorted_descending(self):
        values = extract_fact_values(SINGLE_FACT, periods=5)
        years = [v["fiscal_year"] for v in values]
        assert years == [2024, 2023, 2022, 2021, 2020]

    def test_has_correct_keys(self):
        values = extract_fact_values(SINGLE_FACT, periods=1)
        assert set(values[0].keys()) == {"fiscal_year", "end_date", "value", "unit"}


class TestParseCompanyFacts:
    def test_parses_successfully(self):
        result = parse_company_facts(FACTS_FULL, periods=3)
        assert result["status"] == "SUCCESS"
        assert result["company"]["name"] == "Apple Inc."
        assert result["company"]["ticker"] == ""

    def test_has_periods(self):
        result = parse_company_facts(FACTS_FULL, periods=3)
        assert len(result["periods"]) > 0

    def test_periods_have_statements(self):
        result = parse_company_facts(FACTS_FULL, periods=2)
        for period in result["periods"]:
            assert "IS" in period["statements"]
            assert "BS" in period["statements"]
            assert "CFS" in period["statements"]

    def test_empty_facts(self):
        result = parse_company_facts({"facts": {}}, periods=5)
        assert result["status"] == "SUCCESS"
        assert len(result["periods"]) == 0

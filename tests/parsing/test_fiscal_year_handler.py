"""Tests for fiscal year handler."""

from datetime import date

from src.models.enums import PeriodType
from src.parsing.fiscal_year_handler import (
    detect_fiscal_year_end,
    generate_period_label,
    parse_end_date,
    sort_periods_chronologically,
)


class TestParseEndDate:
    def test_iso_format(self):
        d = parse_end_date("2024-09-30")
        assert d == date(2024, 9, 30)

    def test_us_format(self):
        d = parse_end_date("09/30/2024")
        assert d == date(2024, 9, 30)

    def test_empty(self):
        assert parse_end_date("") is None

    def test_invalid(self):
        assert parse_end_date("not a date") is None


class TestSortPeriods:
    def test_sorts_descending(self):
        periods = [
            {"end_date": "2022-12-31"},
            {"end_date": "2024-12-31"},
            {"end_date": "2023-12-31"},
        ]
        sorted_ = sort_periods_chronologically(periods)
        assert sorted_[0]["end_date"] == "2024-12-31"
        assert sorted_[2]["end_date"] == "2022-12-31"


class TestGeneratePeriodLabel:
    def test_annual(self):
        assert generate_period_label(2024, PeriodType.ANNUAL) == "FY2024"

    def test_quarterly(self):
        assert generate_period_label(2024, PeriodType.QUARTERLY, 3) == "Q3 FY2024"


class TestDetectFiscalYearEnd:
    def test_september_end(self):
        periods = [
            {"end_date": "2024-09-30"},
            {"end_date": "2023-09-30"},
            {"end_date": "2022-09-30"},
        ]
        assert detect_fiscal_year_end(periods) == "09-30"

    def test_december_default(self):
        periods = [{"end_date": ""}]
        assert detect_fiscal_year_end(periods) == "12-31"

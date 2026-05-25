"""Tests for unit detector and value parsing utilities."""

from src.extraction.unit_detector import (
    convert_unit,
    detect_unit,
    parse_value,
)


class TestDetectUnit:
    def test_defaults(self):
        unit, currency = detect_unit([])
        assert unit == "actual"
        assert currency == "USD"

    def test_millions(self):
        unit, _ = detect_unit(["Values (in millions except per share data)"])
        assert unit == "millions"

    def test_thousands(self):
        unit, _ = detect_unit(["All amounts in thousands"])
        assert unit == "thousands"

    def test_billions(self):
        unit, _ = detect_unit(["In Billions of USD"])
        assert unit == "billions"

    def test_currency_dollar(self):
        _, currency = detect_unit(["$1,234"])
        assert currency == "USD"

    def test_currency_euro(self):
        _, currency = detect_unit(["€500 million"])
        assert currency == "EUR"

    def test_currency_yen(self):
        _, currency = detect_unit(["¥10,000"])
        assert currency == "JPY"

    def test_multi_block(self):
        unit, currency = detect_unit(
            [
                "CONSOLIDATED STATEMENTS",
                "(in millions, except per share data)",
                "$ value",
            ]
        )
        assert unit == "millions"
        assert currency == "USD"


class TestParseValue:
    def test_plain_number(self):
        assert parse_value("1234.5") == 1234.5

    def test_with_commas(self):
        assert parse_value("1,234,567.89") == 1234567.89

    def test_parenthetical_negative(self):
        assert parse_value("(1234.5)") == -1234.5

    def test_parenthetical_negative_disabled(self):
        assert parse_value("(1234.5)", is_parenthetical_negative=False) == 1234.5

    def test_dash(self):
        assert parse_value("—") == 0.0
        assert parse_value("-") == 0.0

    def test_already_numeric(self):
        assert parse_value(1000) == 1000.0
        assert parse_value(3.14) == 3.14

    def test_empty_string(self):
        assert parse_value("") == 0.0

    def test_none(self):
        assert parse_value(None) == 0.0

    def test_negative_dollar(self):
        assert parse_value("-$1,234.56") == -1234.56


class TestConvertUnit:
    def test_thousands_to_millions(self):
        result = convert_unit(1000000, "thousands", "millions")
        assert result == 1000.0

    def test_millions_to_millions(self):
        result = convert_unit(500, "millions", "millions")
        assert result == 500.0

    def test_billions_to_millions(self):
        result = convert_unit(2, "billions", "millions")
        assert result == 2000.0

    def test_actual_to_millions(self):
        result = convert_unit(5000000, "actual", "millions")
        assert abs(result - 5.0) < 0.001

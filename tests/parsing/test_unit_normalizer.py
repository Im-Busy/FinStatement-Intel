"""Tests for unit normalizer — value conversion, period normalization."""

from src.parsing.unit_normalizer import normalize_period, normalize_value


class TestNormalizeValue:
    def test_thousands_to_millions(self):
        assert normalize_value(5000, "thousands", "millions") == 5.0

    def test_millions_same(self):
        assert normalize_value(100, "millions", "millions") == 100.0

    def test_billions_to_millions(self):
        assert normalize_value(2, "billions", "millions") == 2000.0

    def test_actual_to_millions(self):
        result = normalize_value(5000000, "actual", "millions")
        assert abs(result - 5.0) < 0.001

    def test_default_to_unit(self):
        result = normalize_value(1000, "thousands")
        assert result == 1.0


class TestNormalizePeriod:
    def test_normalizes_values(self):
        period = {
            "fiscal_year": 2024,
            "end_date": "2024-09-30",
            "statements": {
                "IS": {
                    "unit": "thousands",
                    "line_items": [
                        {"label": "Revenues", "value": 391035000},
                        {"label": "NetIncomeLoss", "value": 93736000},
                    ],
                },
                "BS": {
                    "unit": "thousands",
                    "line_items": [
                        {"label": "Assets", "value": 364980000},
                    ],
                },
                "CFS": {
                    "unit": "thousands",
                    "line_items": [
                        {"label": "NetCashProvidedByUsedInOperatingActivities", "value": 118254000},
                    ],
                },
            },
        }
        result = normalize_period(period, "millions")
        is_items = result["statements"]["IS"]["line_items"]
        assert abs(is_items[0]["value"] - 391035.0) < 0.01
        assert is_items[0]["original_value"] == 391035000
        assert is_items[0]["original_unit"] == "thousands"

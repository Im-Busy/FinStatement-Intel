"""Tests for label mapper — exact match, fuzzy match, alias matching."""

from src.models.enums import MappingConfidence, StatementType
from src.parsing.label_mapper import (
    fuzzy_match,
    load_mapping_dictionary,
    map_all_line_items,
    map_line_item,
)

MAPPING = {
    "standard": "US GAAP",
    "statement_mappings": {
        "IS": {
            "Revenues": "revenue",
            "NetIncomeLoss": "net_income",
            "OperatingIncomeLoss": "operating_income",
        },
        "BS": {
            "Assets": "total_assets",
            "InventoryNet": "inventory",
        },
        "CFS": {
            "NetCashProvidedByUsedInOperatingActivities": "operating_cf",
        },
    },
    "label_aliases": {
        "revenue": ["revenue", "sales", "turnover", "top line"],
        "net_income": ["net income", "net earnings", "bottom line"],
        "total_assets": ["total assets", "assets"],
    },
}


class TestMapLineItem:
    def test_exact_xbrl_concept(self):
        key, conf = map_line_item("Revenues", StatementType.INCOME_STATEMENT, MAPPING)
        assert key == "revenue"
        assert conf == MappingConfidence.EXACT

    def test_alias_match(self):
        key, conf = map_line_item("sales", StatementType.INCOME_STATEMENT, MAPPING)
        assert key == "revenue"
        assert conf == MappingConfidence.EXACT

    def test_case_insensitive_alias(self):
        key, conf = map_line_item("Bottom Line", StatementType.INCOME_STATEMENT, MAPPING)
        assert key == "net_income"

    def test_unmapped(self):
        key, conf = map_line_item("Totally Unknown Item", StatementType.INCOME_STATEMENT, MAPPING)
        assert key is None
        assert conf == MappingConfidence.UNMAPPED

    def test_empty_label(self):
        key, conf = map_line_item("", StatementType.INCOME_STATEMENT, MAPPING)
        assert key is None
        assert conf == MappingConfidence.UNMAPPED


class TestFuzzyMatch:
    def test_exact(self):
        result = fuzzy_match("revenue", ["revenue", "sales", "turnover"])
        assert result == "revenue"

    def test_close_match(self):
        result = fuzzy_match("revenues", ["revenue", "sales", "turnover"], threshold=0.8)
        assert result == "revenue"

    def test_no_match(self):
        result = fuzzy_match("zzzqwerty", ["revenue", "sales"], threshold=0.85)
        assert result is None


class TestMapAllLineItems:
    def test_maps_correctly(self):
        items = [
            {"label": "Revenues", "value": 100000},
            {"label": "NetIncomeLoss", "value": 20000},
            {"label": "Unknown Thing", "value": 500},
        ]
        result = map_all_line_items(items, StatementType.INCOME_STATEMENT, MAPPING)
        assert len(result) == 3
        assert result[0].standard_key == "revenue"
        assert result[1].standard_key == "net_income"
        assert result[2].standard_key is None


class TestLoadMapping:
    def test_loads_default(self):
        mapping = load_mapping_dictionary("us-gaap")
        assert "statement_mappings" in mapping
        assert "label_aliases" in mapping
        assert "IS" in mapping["statement_mappings"]
        assert "BS" in mapping["statement_mappings"]
        assert "CFS" in mapping["statement_mappings"]

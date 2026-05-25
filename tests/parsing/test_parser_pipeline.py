"""Integration tests for the parser pipeline."""

from src.parsing.parser import parse_financial_data

RAW_DATA = {
    "company": {"name": "Apple Inc.", "ticker": "AAPL"},
    "periods": [
        {
            "type": "annual",
            "fiscal_year": 2024,
            "end_date": "2024-09-30",
            "source": "sec-edgar-xbrl",
            "statements": {
                "IS": {
                    "unit": "thousands",
                    "line_items": [
                        {"label": "Revenues", "value": 391035000},
                        {"label": "CostOfGoodsAndServicesSold", "value": 210352000},
                        {"label": "GrossProfit", "value": 180683000},
                        {"label": "OperatingIncomeLoss", "value": 123071000},
                        {"label": "InterestExpense", "value": 4032000},
                        {"label": "NetIncomeLoss", "value": 93736000},
                    ],
                },
                "BS": {
                    "unit": "thousands",
                    "line_items": [
                        {"label": "Assets", "value": 364980000},
                        {"label": "AssetsCurrent", "value": 152987000},
                        {"label": "CashAndCashEquivalentsAtCarryingValue", "value": 65171000},
                        {"label": "AccountsReceivableNetCurrent", "value": 33410000},
                        {"label": "InventoryNet", "value": 7286000},
                        {"label": "Liabilities", "value": 308030000},
                        {"label": "LiabilitiesCurrent", "value": 176392000},
                        {"label": "LongTermDebtNoncurrent", "value": 85750000},
                        {"label": "StockholdersEquity", "value": 56950000},
                    ],
                },
                "CFS": {
                    "unit": "thousands",
                    "line_items": [
                        {"label": "NetCashProvidedByUsedInOperatingActivities", "value": 118254000},
                        {"label": "NetCashProvidedByUsedInInvestingActivities", "value": -2936000},
                        {
                            "label": "NetCashProvidedByUsedInFinancingActivities",
                            "value": -121983000,
                        },
                        {"label": "PaymentsToAcquirePropertyPlantAndEquipment", "value": -9447000},
                        {"label": "DepreciationDepletionAndAmortization", "value": 11500000},
                        {"label": "PaymentsOfDividends", "value": -15234000},
                    ],
                },
            },
        }
    ],
}


class TestParseFinancialData:
    def test_parses_successfully(self):
        result = parse_financial_data(RAW_DATA)
        assert result["status"] == "SUCCESS"
        assert len(result["periods"]) == 1
        assert result["accounting_standard"] == "US GAAP"
        assert result["unit"] == "millions"

    def test_has_income_statement(self):
        result = parse_financial_data(RAW_DATA)
        is_ = result["periods"][0]["statements"]["income_statement"]
        assert abs(is_["revenue"] - 391035.0) < 0.1
        assert abs(is_["net_income"] - 93736.0) < 0.1
        assert is_["gross_profit"] > 0

    def test_has_balance_sheet(self):
        result = parse_financial_data(RAW_DATA)
        bs = result["periods"][0]["statements"]["balance_sheet"]
        assert abs(bs["total_assets"] - 364980.0) < 0.1
        assert abs(bs["total_equity"] - 56950.0) < 0.1

    def test_has_cash_flow_statement(self):
        result = parse_financial_data(RAW_DATA)
        cfs = result["periods"][0]["statements"]["cash_flow_statement"]
        assert abs(cfs["operating_cf"] - 118254.0) < 0.1
        assert cfs["capex"] < 0

    def test_has_validation(self):
        result = parse_financial_data(RAW_DATA)
        v = result["periods"][0]["validation"]
        assert "accounting_equation" in v

    def test_no_periods(self):
        result = parse_financial_data({"company": {}, "periods": []})
        assert result["status"] == "WARNING"
        assert len(result["periods"]) == 0

    def test_has_mapping_stats(self):
        result = parse_financial_data(RAW_DATA)
        assert "mapping_stats" in result
        assert result["mapping_stats"]["mapped_exact"] > 0

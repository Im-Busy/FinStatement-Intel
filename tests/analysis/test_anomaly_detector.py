"""Tests for anomaly detector."""

from src.analysis.anomaly_detector import detect_anomalies, detect_volatility_spikes


class TestDetectVolatilitySpikes:
    def test_no_spikes(self):
        values = [100.0, 105.0, 110.0, 115.0]
        periods = ["FY2021", "FY2022", "FY2023", "FY2024"]
        result = detect_volatility_spikes(values, periods, "revenue")
        assert result == []

    def test_spike_detected(self):
        values = [100.0, 130.0, 90.0, 200.0]
        periods = ["FY2021", "FY2022", "FY2023", "FY2024"]
        result = detect_volatility_spikes(values, periods, "revenue")
        assert len(result) == 3

    def test_small_values_skipped(self):
        values = [0.5, 2.0]
        periods = ["FY2023", "FY2024"]
        result = detect_volatility_spikes(values, periods, "revenue")
        assert result == []

    def test_single_period(self):
        result = detect_volatility_spikes([100.0], ["FY2024"], "revenue")
        assert result == []

    def test_custom_threshold(self):
        values = [100.0, 115.0]
        periods = ["FY2023", "FY2024"]
        result = detect_volatility_spikes(values, periods, "revenue", threshold=0.10)
        assert len(result) == 1

    def test_has_correct_keys(self):
        values = [100.0, 130.0]
        periods = ["FY2023", "FY2024"]
        result = detect_volatility_spikes(values, periods, "revenue")
        assert result[0]["item"] == "revenue"
        assert result[0]["period"] == "FY2024"
        assert result[0]["prev_value"] == 100.0
        assert result[0]["curr_value"] == 130.0
        assert result[0]["change_pct"] == 0.3


class TestDetectAnomalies:
    def test_no_anomalies(self):
        periods = [
            {
                "fiscal_year": 2023,
                "statements": {
                    "income_statement": {"revenue": 1000, "net_income": 100},
                    "cash_flow_statement": {"operating_cf": 150},
                    "balance_sheet": {"total_assets": 2000, "total_liabilities": 1200},
                },
            },
            {
                "fiscal_year": 2024,
                "statements": {
                    "income_statement": {"revenue": 1050, "net_income": 105},
                    "cash_flow_statement": {"operating_cf": 155},
                    "balance_sheet": {"total_assets": 2100, "total_liabilities": 1250},
                },
            },
        ]
        result = detect_anomalies(periods)
        assert result == []

    def test_detects_revenue_spike(self):
        periods = [
            {
                "fiscal_year": 2023,
                "statements": {
                    "income_statement": {"revenue": 1000, "net_income": 100},
                    "cash_flow_statement": {"operating_cf": 150},
                    "balance_sheet": {"total_assets": 2000, "total_liabilities": 1200},
                },
            },
            {
                "fiscal_year": 2024,
                "statements": {
                    "income_statement": {"revenue": 1300, "net_income": 105},
                    "cash_flow_statement": {"operating_cf": 155},
                    "balance_sheet": {"total_assets": 2100, "total_liabilities": 1250},
                },
            },
        ]
        result = detect_anomalies(periods)
        assert len(result) == 1
        assert result[0]["item"] == "revenue"

    def test_sorted_descending(self):
        periods = [
            {
                "fiscal_year": 2023,
                "statements": {
                    "income_statement": {"revenue": 100, "net_income": 100},
                    "cash_flow_statement": {"operating_cf": 100},
                    "balance_sheet": {"total_assets": 100, "total_liabilities": 100},
                },
            },
            {
                "fiscal_year": 2024,
                "statements": {
                    "income_statement": {"revenue": 200, "net_income": 400, "operating_cf": 0},
                    "cash_flow_statement": {"operating_cf": 300},
                    "balance_sheet": {"total_assets": 100, "total_liabilities": 100},
                },
            },
        ]
        result = detect_anomalies(periods)
        assert len(result) >= 1
        largest = abs(result[0]["change_pct"])
        assert all(abs(r["change_pct"]) <= largest for r in result)

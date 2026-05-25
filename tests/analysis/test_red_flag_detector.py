"""Tests for red flag detector — all 12 pattern-based checks."""

from src.analysis.red_flag_detector import (
    detect_acquisition_risk,
    detect_all_red_flags,
    detect_cannot_cover_interest,
    detect_cash_burn,
    detect_debt_service_concern,
    detect_demand_problem,
    detect_earnings_quality_concern,
    detect_excessive_leverage,
    detect_liquidity_crisis,
    detect_negative_equity,
    detect_sustained_margin_decline,
    detect_sustained_negative_ocf,
)
from src.models.enums import Severity
from src.models.ratios import RatioPoint


class TestDetectEarningsQualityConcern:
    def test_triggered(self):
        flag = detect_earnings_quality_concern([0.3, 0.4, 0.2], ["FY2022", "FY2023", "FY2024"])
        assert flag is not None
        assert flag.severity == Severity.CRITICAL

    def test_not_triggered(self):
        flag = detect_earnings_quality_concern([0.8, 1.0, 1.2], ["FY2022", "FY2023", "FY2024"])
        assert flag is None


class TestDetectLiquidityCrisis:
    def test_triggered(self):
        flag = detect_liquidity_crisis([0.8, 0.7], ["FY2023", "FY2024"])
        assert flag is not None
        assert flag.severity == Severity.CRITICAL

    def test_not_triggered(self):
        flag = detect_liquidity_crisis([1.5, 1.6], ["FY2023", "FY2024"])
        assert flag is None


class TestDetectExcessiveLeverage:
    def test_triggered(self):
        flag = detect_excessive_leverage([1.0, 1.5, 2.5], ["FY2022", "FY2023", "FY2024"])
        assert flag is not None
        assert flag.severity == Severity.WARNING

    def test_not_triggered(self):
        flag = detect_excessive_leverage([0.5, 1.0, 1.5], ["FY2022", "FY2023", "FY2024"])
        assert flag is None

    def test_zero_de_ignored(self):
        flag = detect_excessive_leverage([0.0, 3.0], ["FY2023", "FY2024"])
        assert flag is not None

    def test_custom_threshold(self):
        flag = detect_excessive_leverage([1.5, 1.8], ["FY2023", "FY2024"], threshold=1.5)
        assert flag is not None


class TestDetectSustainedNegativeOcf:
    def test_triggered(self):
        flag = detect_sustained_negative_ocf([-100, -200, -150], ["FY2022", "FY2023", "FY2024"])
        assert flag is not None
        assert flag.severity == Severity.CRITICAL

    def test_not_triggered_short_streak(self):
        flag = detect_sustained_negative_ocf([100, -50, 200], ["FY2022", "FY2023", "FY2024"])
        assert flag is None

    def test_not_triggered_all_positive(self):
        flag = detect_sustained_negative_ocf([100, 200, 300], ["FY2022", "FY2023", "FY2024"])
        assert flag is None


class TestDetectDemandProblem:
    def test_triggered(self):
        flag = detect_demand_problem([0.10, 0.15], [0.05, 0.05], ["FY2023", "FY2024"])
        assert flag is not None
        assert flag.severity == Severity.WARNING

    def test_not_triggered(self):
        flag = detect_demand_problem([0.05, 0.05], [0.10, 0.15], ["FY2023", "FY2024"])
        assert flag is None

    def test_empty_input(self):
        assert detect_demand_problem([], [0.05], []) is None
        assert detect_demand_problem([0.05], [], []) is None


class TestDetectAcquisitionRisk:
    def test_triggered(self):
        flag = detect_acquisition_risk(60000, 80000, "FY2024")
        assert flag is not None
        assert flag.severity == Severity.WARNING

    def test_not_triggered(self):
        flag = detect_acquisition_risk(10000, 80000, "FY2024")
        assert flag is None

    def test_negative_values(self):
        flag = detect_acquisition_risk(0, 80000, "FY2024")
        assert flag is None


class TestDetectDebtServiceConcern:
    def test_triggered(self):
        flag = detect_debt_service_concern([1.2, 1.3], ["FY2023", "FY2024"])
        assert flag is not None

    def test_not_triggered(self):
        flag = detect_debt_service_concern([2.0, 2.5], ["FY2023", "FY2024"])
        assert flag is None


class TestDetectCannotCoverInterest:
    def test_triggered(self):
        flag = detect_cannot_cover_interest([0.5, 0.8], ["FY2023", "FY2024"])
        assert flag is not None
        assert flag.severity == Severity.CRITICAL

    def test_skips_zero(self):
        flag = detect_cannot_cover_interest([0.0, -0.5], ["FY2023", "FY2024"])
        assert flag is None


class TestDetectNegativeEquity:
    def test_triggered(self):
        flag = detect_negative_equity([80000, -10000], ["FY2023", "FY2024"])
        assert flag is not None
        assert flag.severity == Severity.CRITICAL

    def test_not_triggered(self):
        flag = detect_negative_equity([80000, 90000], ["FY2023", "FY2024"])
        assert flag is None


class TestDetectSustainedMarginDecline:
    def test_triggered(self):
        flag = detect_sustained_margin_decline(
            [0.20, 0.18, 0.16, 0.14], ["FY2021", "FY2022", "FY2023", "FY2024"]
        )
        assert flag is not None

    def test_not_triggered(self):
        flag = detect_sustained_margin_decline([0.10, 0.12, 0.10], ["FY2022", "FY2023", "FY2024"])
        assert flag is None


class TestDetectCashBurn:
    def test_triggered(self):
        flag = detect_cash_burn([-100, -200, -150], ["FY2022", "FY2023", "FY2024"])
        assert flag is not None

    def test_not_triggered(self):
        flag = detect_cash_burn([-100, 50, -200], ["FY2022", "FY2023", "FY2024"])
        assert flag is None


class TestDetectAllRedFlags:
    def _make_period(self, year, rev, ni, ocf, ca, cl, ta, te, tl, inv, ar, ie):
        return {
            "fiscal_year": year,
            "statements": {
                "income_statement": {
                    "revenue": rev,
                    "net_income": ni,
                    "interest_expense": ie,
                    "operating_income": ni + ie + 1000,
                },
                "balance_sheet": {
                    "current_assets": ca,
                    "current_liabilities": cl,
                    "total_assets": ta,
                    "total_equity": te,
                    "total_liabilities": tl,
                    "inventory": inv,
                    "accounts_receivable": ar,
                    "goodwill": te * 0.3,
                },
                "cash_flow_statement": {"operating_cf": ocf},
            },
        }

    def test_healthy_company(self):
        periods_data = [
            self._make_period(2022, 1000, 100, 120, 400, 200, 2000, 1000, 1000, 80, 100, 10),
            self._make_period(2023, 1100, 110, 130, 420, 210, 2100, 1050, 1050, 85, 105, 11),
            self._make_period(2024, 1200, 120, 140, 440, 220, 2200, 1100, 1100, 90, 110, 12),
        ]
        ratios = {
            "cash_flow_quality": {
                "cf_to_ni": [
                    RatioPoint("FY2022", 1.2),
                    RatioPoint("FY2023", 1.18),
                    RatioPoint("FY2024", 1.17),
                ],
                "fcf": [
                    RatioPoint("FY2022", 100),
                    RatioPoint("FY2023", 110),
                    RatioPoint("FY2024", 120),
                ],
            },
            "liquidity": {
                "current_ratio": [
                    RatioPoint("FY2022", 2.0),
                    RatioPoint("FY2023", 2.0),
                    RatioPoint("FY2024", 2.0),
                ],
            },
            "solvency": {
                "debt_to_equity": [
                    RatioPoint("FY2022", 1.0),
                    RatioPoint("FY2023", 1.0),
                    RatioPoint("FY2024", 1.0),
                ],
                "interest_coverage": [
                    RatioPoint("FY2022", 10.0),
                    RatioPoint("FY2023", 10.0),
                    RatioPoint("FY2024", 10.0),
                ],
            },
            "profitability": {
                "net_margin": [
                    RatioPoint("FY2022", 0.10),
                    RatioPoint("FY2023", 0.10),
                    RatioPoint("FY2024", 0.10),
                ],
            },
        }
        flags = detect_all_red_flags(periods_data, ratios)
        assert len(flags) == 0

    def test_troubled_company(self):
        periods_data = [
            self._make_period(2022, 1000, 100, 30, 200, 300, 2000, 200, 1800, 150, 100, 50),
            self._make_period(2023, 950, 80, 25, 180, 350, 1900, 100, 1800, 170, 120, 50),
            self._make_period(2024, 900, -50, -100, 150, 400, 1800, -100, 1900, 190, 140, 55),
        ]
        ratios = {
            "cash_flow_quality": {
                "cf_to_ni": [
                    RatioPoint("FY2022", 0.3),
                    RatioPoint("FY2023", 0.31),
                    RatioPoint("FY2024", 0.0),
                ],
                "fcf": [
                    RatioPoint("FY2022", -50),
                    RatioPoint("FY2023", -100),
                    RatioPoint("FY2024", -150),
                ],
            },
            "liquidity": {
                "current_ratio": [
                    RatioPoint("FY2022", 0.67),
                    RatioPoint("FY2023", 0.51),
                    RatioPoint("FY2024", 0.38),
                ],
            },
            "solvency": {
                "debt_to_equity": [
                    RatioPoint("FY2022", 9.0),
                    RatioPoint("FY2023", 18.0),
                    RatioPoint("FY2024", 0.0),
                ],
                "interest_coverage": [
                    RatioPoint("FY2022", 3.0),
                    RatioPoint("FY2023", 2.5),
                    RatioPoint("FY2024", 0.5),
                ],
            },
            "profitability": {
                "net_margin": [
                    RatioPoint("FY2022", 0.10),
                    RatioPoint("FY2023", 0.08),
                    RatioPoint("FY2024", -0.05),
                ],
            },
        }
        flags = detect_all_red_flags(periods_data, ratios)
        assert len(flags) >= 3

    def test_sorted_critical_first(self):
        periods_data = [
            self._make_period(2023, 1000, 50, -50, 200, 300, 2000, -500, 2500, 100, 100, 50),
            self._make_period(2024, 900, 40, -60, 180, 350, 1900, -600, 2500, 120, 110, 55),
        ]
        ratios = {
            "cash_flow_quality": {
                "cf_to_ni": [RatioPoint("FY2023", 0.3), RatioPoint("FY2024", 0.25)],
                "fcf": [RatioPoint("FY2023", -80), RatioPoint("FY2024", -100)],
            },
            "liquidity": {
                "current_ratio": [RatioPoint("FY2023", 0.67), RatioPoint("FY2024", 0.51)],
            },
            "solvency": {
                "debt_to_equity": [RatioPoint("FY2023", 0.0), RatioPoint("FY2024", 0.0)],
                "interest_coverage": [RatioPoint("FY2023", 1.0), RatioPoint("FY2024", 0.5)],
            },
            "profitability": {
                "net_margin": [RatioPoint("FY2023", 0.05), RatioPoint("FY2024", 0.04)],
            },
        }
        flags = detect_all_red_flags(periods_data, ratios)
        if flags:
            severities = [f.severity for f in flags]
            critical_count = sum(1 for s in severities if s == Severity.CRITICAL)
            non_critical = [s for s in severities if s != Severity.CRITICAL]
            for nc in non_critical:
                assert severities.index(nc) > critical_count - 1

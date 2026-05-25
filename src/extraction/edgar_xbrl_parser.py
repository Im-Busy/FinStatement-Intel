"""XBRL facts parser — converts SEC companyfacts JSON into structured raw line items.

Handles concept-to-statement classification, fiscal year filtering,
value extraction, and unit handling.
"""

from __future__ import annotations

import logging
from typing import Any

from src.models.enums import StatementType

logger = logging.getLogger(__name__)

XBRL_CONCEPT_TO_STATEMENT: dict[str, str] = {
    "Revenues": "income_statement",
    "RevenueFromContractWithCustomerExcludingAssessedTax": "income_statement",
    "CostOfGoodsAndServicesSold": "income_statement",
    "CostOfRevenue": "income_statement",
    "GrossProfit": "income_statement",
    "OperatingExpenses": "income_statement",
    "ResearchAndDevelopmentExpense": "income_statement",
    "SellingGeneralAndAdministrativeExpense": "income_statement",
    "OperatingIncomeLoss": "income_statement",
    "NonoperatingIncomeExpense": "income_statement",
    "InterestExpense": "income_statement",
    "InterestIncomeExpenseNonoperatingNet": "income_statement",
    "InvestmentIncomeInterest": "income_statement",
    "IncomeTaxExpenseBenefit": "income_statement",
    "NetIncomeLoss": "income_statement",
    "EarningsPerShareBasic": "income_statement",
    "EarningsPerShareDiluted": "income_statement",
    "WeightedAverageNumberOfSharesOutstandingBasic": "income_statement",
    "WeightedAverageNumberOfDilutedSharesOutstanding": "income_statement",
    "DepreciationDepletionAndAmortization": "income_statement",
    "Assets": "balance_sheet",
    "AssetsCurrent": "balance_sheet",
    "CashAndCashEquivalentsAtCarryingValue": "balance_sheet",
    "Cash": "balance_sheet",
    "AccountsReceivableNetCurrent": "balance_sheet",
    "InventoryNet": "balance_sheet",
    "OtherAssetsCurrent": "balance_sheet",
    "PropertyPlantAndEquipmentNet": "balance_sheet",
    "PropertyPlantAndEquipmentGross": "balance_sheet",
    "AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment": "balance_sheet",
    "Goodwill": "balance_sheet",
    "IntangibleAssetsNetExcludingGoodwill": "balance_sheet",
    "OtherAssetsNoncurrent": "balance_sheet",
    "Liabilities": "balance_sheet",
    "LiabilitiesCurrent": "balance_sheet",
    "AccountsPayableCurrent": "balance_sheet",
    "ShortTermBorrowings": "balance_sheet",
    "LongTermDebtCurrent": "balance_sheet",
    "DeferredRevenueCurrent": "balance_sheet",
    "OtherLiabilitiesCurrent": "balance_sheet",
    "LongTermDebtNoncurrent": "balance_sheet",
    "LongTermDebt": "balance_sheet",
    "DeferredIncomeTaxLiabilitiesNet": "balance_sheet",
    "OtherLiabilitiesNoncurrent": "balance_sheet",
    "StockholdersEquity": "balance_sheet",
    "CommonStockValue": "balance_sheet",
    "RetainedEarningsAccumulatedDeficit": "balance_sheet",
    "AccumulatedOtherComprehensiveIncomeLossNetOfTax": "balance_sheet",
    "TreasuryStockValue": "balance_sheet",
    "NetCashProvidedByUsedInOperatingActivities": "cash_flow_statement",
    "NetCashProvidedByUsedInInvestingActivities": "cash_flow_statement",
    "NetCashProvidedByUsedInFinancingActivities": "cash_flow_statement",
    "PaymentsToAcquirePropertyPlantAndEquipment": "cash_flow_statement",
    "ProceedsFromSaleOfPropertyPlantAndEquipment": "cash_flow_statement",
    "PaymentsToAcquireBusinessesNetOfCashAcquired": "cash_flow_statement",
    "PaymentsToAcquireInvestments": "cash_flow_statement",
    "ProceedsFromSaleAndMaturityOfInvestments": "cash_flow_statement",
    "PaymentsForRepurchaseOfCommonStock": "cash_flow_statement",
    "PaymentsOfDividends": "cash_flow_statement",
    "ProceedsFromIssuanceOfCommonStock": "cash_flow_statement",
    "ProceedsFromIssuanceOfLongTermDebt": "cash_flow_statement",
    "RepaymentsOfLongTermDebt": "cash_flow_statement",
    "EffectOfExchangeRateOnCash": "cash_flow_statement",
    "CashAndCashEquivalentsPeriodIncreaseDecrease": "cash_flow_statement",
}

_STATEMENT_SIMULTANEOUS = {"NetIncomeLoss", "DepreciationDepletionAndAmortization"}


def classify_concept(concept_name: str) -> StatementType | None:
    """Classify an XBRL concept name into a statement type.

    Args:
        concept_name: The XBRL concept name (e.g., "Revenues", "Assets").

    Returns:
        StatementType or None if concept is unknown.
    """
    stmt = XBRL_CONCEPT_TO_STATEMENT.get(concept_name)
    if stmt is None:
        return None
    return StatementType(stmt)


def _map_stmt_to_key(stmt: StatementType) -> str:
    return {
        StatementType.INCOME_STATEMENT: "IS",
        StatementType.BALANCE_SHEET: "BS",
        StatementType.CASH_FLOW_STATEMENT: "CFS",
    }[stmt]


def extract_fact_values(fact_data: dict[str, Any], periods: int) -> list[dict[str, Any]]:
    """Extract annual (FY) values from a single XBRL fact's data.

    Args:
        fact_data: The data dict for a single us-gaap concept
                   (e.g., facts["us-gaap"]["Revenues"]).
        periods: Maximum number of periods to return.

    Returns:
        List of dicts with keys: fiscal_year, end_date, value, unit.
    """
    units = fact_data.get("units", {})
    values: list[dict[str, Any]] = []

    for currency, entries in units.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if entry.get("form") == "10-K" or entry.get("fp") == "FY":
                frame = entry.get("frame", "")
                fy = entry.get("fy")
                if fy is None and frame:
                    try:
                        fy = int(frame[2:6])
                    except (ValueError, IndexError):
                        pass
                val = entry.get("val")
                if fy is not None and val is not None:
                    values.append(
                        {
                            "fiscal_year": fy,
                            "end_date": entry.get("end", ""),
                            "value": val,
                            "unit": currency,
                        }
                    )

    values.sort(key=lambda x: x["fiscal_year"], reverse=True)
    return values[:periods]


def parse_company_facts(
    facts: dict[str, Any], periods: int = 5, ticker: str = ""
) -> dict[str, Any]:
    """Parse SEC companyfacts JSON into raw line items grouped by statement and year.

    Args:
        facts: Raw company facts JSON from get_company_facts().
        periods: Number of fiscal periods to extract.
        ticker: Stock ticker symbol (not available in facts JSON, passed from extractor).

    Returns:
        Dict with keys: company, periods[type, fiscal_year, end_date, source, statements].
    """
    entity_name = facts.get("entityName", "")
    cik = str(facts.get("cik", "")).zfill(10)
    if not ticker and "tickers" in facts and facts["tickers"]:
        ticker = str(facts["tickers"][0])

    us_gaap = facts.get("facts", {}).get("us-gaap", {})
    if not us_gaap:
        dei = facts.get("facts", {}).get("dei", {})
        if dei:
            entity_name = (
                dei.get("EntityRegistrantName", {})
                .get("units", {})
                .get("USD", [{}])[0]
                .get("val", entity_name)
            )

    period_data: dict[int, dict[str, list[dict[str, Any]]]] = {}

    for concept_name, concept_data in us_gaap.items():
        stmt = classify_concept(concept_name)
        if stmt is None:
            continue

        stmt_key = _map_stmt_to_key(stmt)
        fact_entries = extract_fact_values(concept_data, periods)

        placement = [stmt_key]
        if concept_name in _STATEMENT_SIMULTANEOUS:
            if stmt_key == "IS":
                placement.append("CFS")
            elif stmt_key == "CFS":
                placement.append("IS")

        for entry in fact_entries:
            fy = entry["fiscal_year"]
            if fy not in period_data:
                period_data[fy] = {"IS": [], "BS": [], "CFS": []}
            for key in placement:
                period_data[fy][key].append(
                    {
                        "label": concept_name,
                        "value": entry["value"],
                        "needs_review": False,
                    }
                )

    periods_list: list[dict[str, Any]] = []
    for fy in sorted(period_data.keys(), reverse=True)[:periods]:
        pd = period_data[fy]
        has_data = any(pd[k] for k in ("IS", "BS", "CFS"))
        if not has_data:
            continue
        fy_entries = extract_fact_values(us_gaap.get("Revenues", {}), periods)
        end_date = ""
        for fe in fy_entries:
            if fe["fiscal_year"] == fy:
                end_date = fe.get("end_date", "")
                break

        periods_list.append(
            {
                "type": "annual",
                "fiscal_year": fy,
                "end_date": end_date,
                "source": "sec-edgar-xbrl",
                "statements": {
                    "IS": {
                        "unit": "USD",
                        "line_items": pd["IS"],
                    },
                    "BS": {
                        "unit": "USD",
                        "line_items": pd["BS"],
                    },
                    "CFS": {
                        "unit": "USD",
                        "line_items": pd["CFS"],
                    },
                },
            }
        )

    return {
        "status": "SUCCESS",
        "company": {
            "name": entity_name,
            "ticker": ticker,
            "cik": cik,
            "fiscal_year_end": "",
            "currency": "USD",
        },
        "periods": periods_list,
        "warnings": [],
        "metadata": {
            "extraction_method": "edgar-xbrl",
            "periods_requested": periods,
            "periods_extracted": len(periods_list),
        },
    }

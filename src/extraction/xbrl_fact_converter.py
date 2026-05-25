"""XBRL fact-to-period converter — transforms XBRL concept data into the standard
extraction output format consumed by the parser pipeline.

Takes a flat {concept: {date: value}} dict from filing_fetcher and produces
the standard {periods: [{type, fiscal_year, end_date, source, statements}]} format.
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
    "DepreciationDepletionAndAmortization": "income_statement",
    "Assets": "balance_sheet",
    "AssetsCurrent": "balance_sheet",
    "CashAndCashEquivalentsAtCarryingValue": "balance_sheet",
    "Cash": "balance_sheet",
    "AccountsReceivableNetCurrent": "balance_sheet",
    "InventoryNet": "balance_sheet",
    "PropertyPlantAndEquipmentNet": "balance_sheet",
    "AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment": "balance_sheet",
    "Goodwill": "balance_sheet",
    "Liabilities": "balance_sheet",
    "LiabilitiesCurrent": "balance_sheet",
    "AccountsPayableCurrent": "balance_sheet",
    "LongTermDebtNoncurrent": "balance_sheet",
    "LongTermDebt": "balance_sheet",
    "ShortTermBorrowings": "balance_sheet",
    "StockholdersEquity": "balance_sheet",
    "CommonStockValue": "balance_sheet",
    "RetainedEarningsAccumulatedDeficit": "balance_sheet",
    "NetCashProvidedByUsedInOperatingActivities": "cash_flow_statement",
    "NetCashProvidedByUsedInInvestingActivities": "cash_flow_statement",
    "NetCashProvidedByUsedInFinancingActivities": "cash_flow_statement",
    "PaymentsToAcquirePropertyPlantAndEquipment": "cash_flow_statement",
    "PaymentsForRepurchaseOfCommonStock": "cash_flow_statement",
    "PaymentsOfDividends": "cash_flow_statement",
    "ProceedsFromIssuanceOfCommonStock": "cash_flow_statement",
    "ProceedsFromIssuanceOfLongTermDebt": "cash_flow_statement",
    "RepaymentsOfLongTermDebt": "cash_flow_statement",
    "EffectOfExchangeRateOnCash": "cash_flow_statement",
    "CashAndCashEquivalentsPeriodIncreaseDecrease": "cash_flow_statement",
}

STATEMENT_SIMULTANEOUS = {
    "NetIncomeLoss",
    "DepreciationDepletionAndAmortization",
}

STMT_KEY_MAP = {
    "income_statement": "IS",
    "balance_sheet": "BS",
    "cash_flow_statement": "CFS",
}


def _classify_concept(concept_name: str) -> StatementType | None:
    stmt = XBRL_CONCEPT_TO_STATEMENT.get(concept_name)
    if stmt is None:
        return None
    return StatementType(stmt)


def _stmt_to_key(stmt: StatementType) -> str:
    return STMT_KEY_MAP[stmt.value]


def convert_facts_to_periods(
    facts: dict[str, dict[str, float]],
    ticker: str,
    company_name: str = "",
    max_periods: int = 5,
) -> dict[str, Any]:
    """Convert flat XBRL facts into standard extraction output.

    Args:
        facts: {concept_name: {end_date: value}} from filing_fetcher.
        ticker: Stock ticker symbol.
        company_name: Company name.
        max_periods: Maximum number of periods to include.

    Returns:
        Standard extraction result dict with periods key.
    """
    period_data: dict[str, dict[str, dict[str, list[dict[str, Any]]]]] = {}

    for concept_name, date_values in facts.items():
        stmt = _classify_concept(concept_name)
        if stmt is None:
            continue
        stmt_key = _stmt_to_key(stmt)

        for end_date, value in date_values.items():
            if end_date not in period_data:
                period_data[end_date] = {"IS": {}, "BS": {}, "CFS": {}}

            entry = {"label": concept_name, "value": value, "needs_review": False}

            targets = [stmt_key]
            if concept_name in STATEMENT_SIMULTANEOUS:
                for other_key in ("IS", "CFS"):
                    if other_key != stmt_key:
                        targets.append(other_key)

            for target in targets:
                if concept_name not in period_data[end_date][target]:
                    period_data[end_date][target][concept_name] = entry

    sorted_dates = sorted(period_data.keys(), reverse=True)[:max_periods]
    periods_list: list[dict[str, Any]] = []

    for end_date in sorted_dates:
        pd = period_data[end_date]
        statements_dict: dict[str, dict[str, Any]] = {}

        for stmt_key in ("IS", "BS", "CFS"):
            items = list(pd[stmt_key].values())
            statements_dict[stmt_key] = {
                "unit": "USD",
                "line_items": items,
            }

        try:
            fy = int(end_date[:4])
        except (ValueError, IndexError):
            fy = 0

        periods_list.append(
            {
                "type": "annual",
                "fiscal_year": fy,
                "end_date": end_date,
                "source": "sec-edgar-10k-xbrl",
                "statements": statements_dict,
            }
        )

    return {
        "status": "SUCCESS",
        "company": {
            "name": company_name,
            "ticker": ticker,
            "cik": "",
            "fiscal_year_end": "",
            "currency": "USD",
        },
        "periods": periods_list,
        "warnings": [],
        "metadata": {
            "extraction_method": "sec-edgar-10k-xbrl",
            "periods_extracted": len(periods_list),
        },
    }

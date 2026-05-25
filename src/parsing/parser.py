"""Parse raw financial data into standardized structured statements.

Handles label normalization, unit conversion, structural validation,
and mapping of company-specific line items to standard names.
"""

from __future__ import annotations

import logging
from typing import Any

from src.models.enums import MappingConfidence, PeriodType, StatementType
from src.models.line_item import LineItem, UnmappedItem
from src.models.period import Period
from src.models.statements import BalanceSheet, CashFlowStatement, IncomeStatement
from src.parsing.fiscal_year_handler import detect_fiscal_year_end
from src.parsing.label_mapper import (
    load_mapping_dictionary,
    map_all_line_items,
)
from src.parsing.structure_validator import run_all_validations
from src.parsing.subtotal_calculator import compute_derived_fields
from src.parsing.unit_normalizer import normalize_period

logger = logging.getLogger(__name__)

KEY_TO_ATTR_IS = {
    "revenue": "revenue",
    "cogs": "cogs",
    "gross_profit": "gross_profit",
    "operating_expenses": "operating_expenses",
    "rnd_expense": "rnd_expense",
    "sga_expense": "sga_expense",
    "operating_income": "operating_income",
    "interest_expense": "interest_expense",
    "interest_income": "interest_income",
    "income_tax": "income_tax",
    "net_income": "net_income",
    "eps_basic": "eps_basic",
    "eps_diluted": "eps_diluted",
    "ebitda": "ebitda",
    "depreciation_amortization": "depreciation_amortization",
}

KEY_TO_ATTR_BS = {
    "total_assets": "total_assets",
    "current_assets": "current_assets",
    "cash_and_equivalents": "cash_and_equivalents",
    "accounts_receivable": "accounts_receivable",
    "inventory": "inventory",
    "total_liabilities": "total_liabilities",
    "current_liabilities": "current_liabilities",
    "long_term_debt": "long_term_debt",
    "total_equity": "total_equity",
    "goodwill": "goodwill",
    "ppe_net": "ppe_net",
    "accounts_payable": "accounts_payable",
    "short_term_debt": "short_term_debt",
    "accumulated_depreciation": "accumulated_depreciation",
}

KEY_TO_ATTR_CFS = {
    "operating_cf": "operating_cf",
    "investing_cf": "investing_cf",
    "financing_cf": "financing_cf",
    "capex": "capex",
    "depreciation_amortization": "depreciation_amortization",
    "net_change_cash": "net_change_cash",
    "dividends_paid": "dividends_paid",
    "stock_issuance": "stock_issuance",
    "debt_repayment": "debt_repayment",
    "debt_issuance": "debt_issuance",
    "fx_effect": "fx_effect",
    "net_income": "net_income",
}


def _populate_dataclass(
    mapped_items: list[LineItem],
    key_map: dict[str, str],
    dataclass: Any,
    statement_type: StatementType,
) -> list[UnmappedItem]:
    unmapped: list[UnmappedItem] = []
    for li in mapped_items:
        if li.standard_key and li.standard_key in key_map:
            setattr(dataclass, key_map[li.standard_key], li.value)
        elif li.standard_key is None or li.mapping_confidence == MappingConfidence.UNMAPPED:
            unmapped.append(
                UnmappedItem(
                    original_label=li.label,
                    value=li.value,
                    statement_type=statement_type,
                )
            )
    return unmapped


def parse_financial_data(raw_data: dict[str, Any]) -> dict[str, Any]:
    """Parse extracted raw data into structured financial statements.

    Args:
        raw_data: JSON from the extractor agent.

    Returns:
        Parsed result JSON with standardized line items and validation results.
    """
    logger.info(
        "Parsing financial data for %s", raw_data.get("company", {}).get("ticker", "unknown")
    )

    mapping = load_mapping_dictionary("us-gaap")

    company = raw_data.get("company", {})
    raw_periods = raw_data.get("periods", [])

    if not raw_periods:
        return {
            "status": "WARNING",
            "message": "No period data to parse",
            "company": company,
            "periods": [],
        }

    fiscal_year_end = detect_fiscal_year_end(raw_periods)
    if fiscal_year_end:
        company["fiscal_year_end"] = fiscal_year_end

    total_mapped_exact = 0
    total_mapped_fuzzy = 0
    total_unmapped = 0
    parsed_periods: list[dict[str, Any]] = []

    for raw_period in raw_periods:
        normalized = normalize_period(raw_period, "millions")
        statements = normalized.get("statements", {})

        is_items = map_all_line_items(
            statements.get("IS", {}).get("line_items", []),
            StatementType.INCOME_STATEMENT,
            mapping,
        )
        bs_items = map_all_line_items(
            statements.get("BS", {}).get("line_items", []),
            StatementType.BALANCE_SHEET,
            mapping,
        )
        cfs_items = map_all_line_items(
            statements.get("CFS", {}).get("line_items", []),
            StatementType.CASH_FLOW_STATEMENT,
            mapping,
        )

        is_stmt = IncomeStatement()
        bs_stmt = BalanceSheet()
        cfs_stmt = CashFlowStatement()

        is_unmapped = _populate_dataclass(
            is_items, KEY_TO_ATTR_IS, is_stmt, StatementType.INCOME_STATEMENT
        )
        bs_unmapped = _populate_dataclass(
            bs_items, KEY_TO_ATTR_BS, bs_stmt, StatementType.BALANCE_SHEET
        )
        cfs_unmapped = _populate_dataclass(
            cfs_items, KEY_TO_ATTR_CFS, cfs_stmt, StatementType.CASH_FLOW_STATEMENT
        )

        is_stmt.unmapped = is_unmapped
        bs_stmt.unmapped = bs_unmapped
        cfs_stmt.unmapped = cfs_unmapped

        compute_derived_fields(is_stmt, bs_stmt, cfs_stmt)

        period = Period(
            type=PeriodType.ANNUAL,
            fiscal_year=raw_period.get("fiscal_year", 0),
            end_date=raw_period.get("end_date", ""),
            income_statement=is_stmt,
            balance_sheet=bs_stmt,
            cash_flow_statement=cfs_stmt,
            source=raw_period.get("source", ""),
            original_unit=normalized.get("original_unit", ""),
        )

        results = run_all_validations(period)
        period.validation_results = results

        parsed_periods.append(
            {
                "type": period.type.value,
                "fiscal_year": period.fiscal_year,
                "end_date": period.end_date,
                "statements": {
                    "income_statement": {
                        k: getattr(is_stmt, k)
                        for k in KEY_TO_ATTR_IS.values()
                        if hasattr(is_stmt, k)
                    },
                    "balance_sheet": {
                        k: getattr(bs_stmt, k)
                        for k in KEY_TO_ATTR_BS.values()
                        if hasattr(bs_stmt, k)
                    },
                    "cash_flow_statement": {
                        k: getattr(cfs_stmt, k)
                        for k in KEY_TO_ATTR_CFS.values()
                        if hasattr(cfs_stmt, k)
                    },
                },
                "validation": {
                    "accounting_equation": _vr_to_dict(
                        next((r for r in results if r.check_name == "accounting_equation"), None)
                    ),
                    "cash_flow_reconciliation": _vr_to_dict(
                        next(
                            (r for r in results if r.check_name == "cash_flow_reconciliation"), None
                        )
                    ),
                    "income_statement_arithmetic": _vr_to_dict(
                        next(
                            (r for r in results if r.check_name == "income_statement_arithmetic"),
                            None,
                        )
                    ),
                    "warnings": [],
                },
            }
        )

        for li in is_items + bs_items + cfs_items:
            if li.mapping_confidence == MappingConfidence.EXACT:
                total_mapped_exact += 1
            elif li.mapping_confidence in (MappingConfidence.FUZZY, MappingConfidence.LOW):
                total_mapped_fuzzy += 1
            else:
                total_unmapped += 1

    return {
        "status": "SUCCESS" if total_unmapped == 0 else "WARNING",
        "company": company,
        "accounting_standard": "US GAAP",
        "unit": "millions",
        "currency": "USD",
        "periods": parsed_periods,
        "mapping_stats": {
            "total_items": total_mapped_exact + total_mapped_fuzzy + total_unmapped,
            "mapped_exact": total_mapped_exact,
            "mapped_fuzzy": total_mapped_fuzzy,
            "unmapped": total_unmapped,
        },
    }


def _vr_to_dict(vr: object | None) -> dict[str, Any] | None:
    if vr is None:
        return None
    return {
        "holds": getattr(vr, "holds", False),
        "expected": getattr(vr, "expected", 0.0),
        "actual": getattr(vr, "actual", 0.0),
        "difference": getattr(vr, "difference", 0.0),
        "diff_pct": getattr(vr, "diff_pct", 0.0),
        "detail": getattr(vr, "detail", ""),
    }

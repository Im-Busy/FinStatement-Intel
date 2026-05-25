"""Ratio calculator orchestrator — computes all 22 ratios across all periods."""

from __future__ import annotations

import logging
from typing import Any

from src.analysis.cash_flow_quality import (
    compute_cf_to_ni,
    compute_fcf,
    compute_fcf_margin,
    compute_fcf_to_ni,
)
from src.analysis.efficiency import (
    compute_asset_turnover,
    compute_days_sales_outstanding,
    compute_inventory_turnover,
    compute_receivables_turnover,
)
from src.analysis.liquidity import (
    compute_current_ratio,
    compute_operating_cf_ratio,
    compute_quick_ratio,
    compute_working_capital,
)
from src.analysis.profitability import (
    compute_ebitda_margin,
    compute_gross_margin,
    compute_net_margin,
    compute_operating_margin,
    compute_roa,
    compute_roe,
)
from src.analysis.solvency import (
    compute_debt_to_assets,
    compute_debt_to_equity,
    compute_interest_coverage,
    compute_lt_debt_to_equity,
)
from src.models.ratios import RatioPoint

logger = logging.getLogger(__name__)


def compute_all_ratios(periods: list[dict]) -> dict[str, Any]:
    """Compute all 22 ratios for all periods.

    Args:
        periods: List of parsed period dicts with statements.

    Returns:
        Dict with profitability, liquidity, solvency, efficiency, cash_flow_quality keys.
    """
    result: dict[str, dict[str, list[RatioPoint]]] = {
        "profitability": {
            "gross_margin": [],
            "operating_margin": [],
            "net_margin": [],
            "roa": [],
            "roe": [],
            "ebitda_margin": [],
        },
        "liquidity": {
            "current_ratio": [],
            "quick_ratio": [],
            "working_capital": [],
            "operating_cf_ratio": [],
        },
        "solvency": {
            "debt_to_equity": [],
            "debt_to_assets": [],
            "interest_coverage": [],
            "lt_debt_to_equity": [],
        },
        "efficiency": {
            "asset_turnover": [],
            "receivables_turnover": [],
            "inventory_turnover": [],
            "days_sales_outstanding": [],
        },
        "cash_flow_quality": {
            "fcf": [],
            "fcf_margin": [],
            "cf_to_ni": [],
            "fcf_to_ni": [],
        },
    }

    for period in periods:
        stmts = period.get("statements", {})
        is_data = stmts.get("income_statement", {})
        bs_data = stmts.get("balance_sheet", {})
        cfs_data = stmts.get("cash_flow_statement", {})

        label = f"FY{period.get('fiscal_year', '')}"

        r = result["profitability"]
        r["gross_margin"].append(
            RatioPoint(
                label,
                compute_gross_margin(is_data.get("gross_profit", 0), is_data.get("revenue", 0))
                or 0.0,
                "%",
            )
        )
        r["operating_margin"].append(
            RatioPoint(
                label,
                compute_operating_margin(
                    is_data.get("operating_income", 0), is_data.get("revenue", 0)
                )
                or 0.0,
                "%",
            )
        )
        r["net_margin"].append(
            RatioPoint(
                label,
                compute_net_margin(is_data.get("net_income", 0), is_data.get("revenue", 0)) or 0.0,
                "%",
            )
        )
        r["roa"].append(
            RatioPoint(
                label,
                compute_roa(is_data.get("net_income", 0), bs_data.get("total_assets", 0)) or 0.0,
                "%",
            )
        )
        r["roe"].append(
            RatioPoint(
                label,
                compute_roe(is_data.get("net_income", 0), bs_data.get("total_equity", 0)) or 0.0,
                "%",
            )
        )
        r["ebitda_margin"].append(
            RatioPoint(
                label,
                compute_ebitda_margin(is_data.get("ebitda", 0), is_data.get("revenue", 0)) or 0.0,
                "%",
            )
        )

        lq = result["liquidity"]
        lq["current_ratio"].append(
            RatioPoint(
                label,
                compute_current_ratio(
                    bs_data.get("current_assets", 0), bs_data.get("current_liabilities", 0)
                )
                or 0.0,
                "ratio",
            )
        )
        lq["quick_ratio"].append(
            RatioPoint(
                label,
                compute_quick_ratio(
                    bs_data.get("current_assets", 0),
                    bs_data.get("inventory", 0),
                    bs_data.get("current_liabilities", 0),
                )
                or 0.0,
                "ratio",
            )
        )
        lq["working_capital"].append(
            RatioPoint(
                label,
                compute_working_capital(
                    bs_data.get("current_assets", 0), bs_data.get("current_liabilities", 0)
                ),
                "USD",
            )
        )
        lq["operating_cf_ratio"].append(
            RatioPoint(
                label,
                compute_operating_cf_ratio(
                    cfs_data.get("operating_cf", 0), bs_data.get("current_liabilities", 0)
                )
                or 0.0,
                "ratio",
            )
        )

        sv = result["solvency"]
        sv["debt_to_equity"].append(
            RatioPoint(
                label,
                compute_debt_to_equity(
                    bs_data.get("total_liabilities", 0), bs_data.get("total_equity", 0)
                )
                or 0.0,
                "ratio",
            )
        )
        sv["debt_to_assets"].append(
            RatioPoint(
                label,
                compute_debt_to_assets(
                    bs_data.get("total_liabilities", 0), bs_data.get("total_assets", 0)
                )
                or 0.0,
                "%",
            )
        )
        sv["interest_coverage"].append(
            RatioPoint(
                label,
                compute_interest_coverage(
                    is_data.get("operating_income", 0), is_data.get("interest_expense", 0)
                )
                or 0.0,
                "ratio",
            )
        )
        sv["lt_debt_to_equity"].append(
            RatioPoint(
                label,
                compute_lt_debt_to_equity(
                    bs_data.get("long_term_debt", 0), bs_data.get("total_equity", 0)
                )
                or 0.0,
                "ratio",
            )
        )

        ef = result["efficiency"]
        rt = compute_receivables_turnover(
            is_data.get("revenue", 0), bs_data.get("accounts_receivable", 0)
        )
        ef["asset_turnover"].append(
            RatioPoint(
                label,
                compute_asset_turnover(is_data.get("revenue", 0), bs_data.get("total_assets", 0))
                or 0.0,
                "ratio",
            )
        )
        ef["receivables_turnover"].append(RatioPoint(label, rt or 0.0, "ratio"))
        ef["inventory_turnover"].append(
            RatioPoint(
                label,
                compute_inventory_turnover(is_data.get("cogs", 0), bs_data.get("inventory", 0))
                or 0.0,
                "ratio",
            )
        )
        ef["days_sales_outstanding"].append(
            RatioPoint(label, compute_days_sales_outstanding(rt) or 0.0, "days")
        )

        cf = result["cash_flow_quality"]
        fcf_val = compute_fcf(cfs_data.get("operating_cf", 0), cfs_data.get("capex", 0))
        cf["fcf"].append(RatioPoint(label, fcf_val, "USD"))
        cf["fcf_margin"].append(
            RatioPoint(label, compute_fcf_margin(fcf_val, is_data.get("revenue", 0)) or 0.0, "%")
        )
        cf["cf_to_ni"].append(
            RatioPoint(
                label,
                compute_cf_to_ni(cfs_data.get("operating_cf", 0), is_data.get("net_income", 0))
                or 0.0,
                "ratio",
            )
        )
        cf["fcf_to_ni"].append(
            RatioPoint(
                label, compute_fcf_to_ni(fcf_val, is_data.get("net_income", 0)) or 0.0, "ratio"
            )
        )

    return result

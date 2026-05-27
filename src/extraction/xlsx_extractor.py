"""XLSX extraction — extract financial statements from Excel spreadsheets.

Uses openpyxl to scan worksheets and classify financial line items into
Income Statement, Balance Sheet, and Cash Flow Statement categories.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from src.extraction.line_item_extractor import build_line_item, clean_label
from src.extraction.unit_detector import detect_unit

logger = logging.getLogger(__name__)

_STATEMENT_KEYWORDS: dict[str, list[str]] = {
    "IS": [
        r"revenue",
        r"sales",
        r"cost of",
        r"gross profit",
        r"operating (?:income|profit|expenses?)",
        r"net income",
        r"earnings per share",
        r"eps",
        r"ebitda",
        r"income tax",
        r"r&d",
        r"research and development",
        r"selling,? general",
        r"interest (?:income|expense)",
        r"other (?:income|expense)",
    ],
    "BS": [
        r"total assets",
        r"current assets",
        r"current liabilities",
        r"total liabilities",
        r"shareholders.? equity",
        r"stockholders.? equity",
        r"cash and (?:cash )?equivalents",
        r"accounts? receivable",
        r"inventor(?:y|ies)",
        r"property.*equipment",
        r"accounts? payable",
        r"long-term debt",
        r"goodwill",
        r"retained earnings",
        r"accumulated (?:other )?comprehensive",
        r"total current assets",
        r"total current liabilities",
        r"intangible",
        r"deferred",
    ],
    "CFS": [
        r"operating activities",
        r"investing activities",
        r"financing activities",
        r"depreciation and amortization",
        r"amortization",
        r"stock.based compensation",
        r"capital expenditures?",
        r"capex",
        r"free cash flow",
        r"proceeds from",
        r"repayment of",
        r"repayments? of",
        r"dividends? paid",
        r"share repurchase",
        r"net change in cash",
        r"net cash (?:provided|used)",
    ],
}

_SHEET_NAME_PATTERNS = {
    "IS": re.compile(r"income|profit.*loss|operations|earnings|p&l|sopl", re.IGNORECASE),
    "BS": re.compile(r"balance|financial position|sofp|assets.*liabilities", re.IGNORECASE),
    "CFS": re.compile(r"cash.?flow|socf|cash flow", re.IGNORECASE),
}

_AMOUNT_RE = re.compile(r"^\s*\$?\s*-?\(?[\d,.]+\)?\s*$")


def _classify_sheet_name(name: str) -> str | None:
    """Try to classify a worksheet by its name.

    Args:
        name: The sheet/tab name.

    Returns:
        'IS', 'BS', 'CFS', or None if unclassifiable.
    """
    for stmt, pattern in _SHEET_NAME_PATTERNS.items():
        if pattern.search(name):
            return stmt
    return None


def _classify_row(label: str) -> str:
    """Classify a row label into IS, BS, or CFS.

    Args:
        label: The text label of a row.

    Returns:
        'IS', 'BS', or 'CFS'.
    """
    lower = label.lower().strip()
    for stmt, patterns in _STATEMENT_KEYWORDS.items():
        for pattern in patterns:
            if re.search(pattern, lower):
                return stmt
    return "BS"


def _extract_sheet_data(
    worksheet: Any,
    sheet_name: str,
) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    """Extract line items from a single worksheet.

    Args:
        worksheet: An openpyxl Worksheet instance.
        sheet_name: Name of the sheet.

    Returns:
        Tuple of (statements_dict, text_cells for unit detection).
    """
    statements: dict[str, list[dict[str, Any]]] = {"IS": [], "BS": [], "CFS": []}
    text_cells: list[str] = []
    seen_labels: set[str] = set()

    sheet_classification = _classify_sheet_name(sheet_name)

    for row in worksheet.iter_rows(min_row=1, values_only=True):
        if not row or len(row) < 2:
            continue

        label = str(row[0]).strip() if row[0] is not None else ""
        if not label or len(label) < 3:
            continue

        label_clean = clean_label(label)
        label_lower = label_clean.lower()
        if label_lower in seen_labels:
            continue

        value = 0.0
        for cell in row[1:]:
            if cell is None:
                continue
            try:
                if isinstance(cell, (int, float)):
                    value = float(cell)
                    break
                cell_str = str(cell).strip().replace("$", "").replace(",", "")
                if cell_str.startswith("(") and cell_str.endswith(")"):
                    cell_str = f"-{cell_str[1:-1]}"
                value = float(cell_str)
                break
            except (ValueError, TypeError):
                continue

        text_cells.append(label_clean)

        if sheet_classification:
            seen_labels.add(label_lower)
            statements[sheet_classification].append(build_line_item(label_clean, value))
        else:
            stmt = _classify_row(label_clean)
            seen_labels.add(label_lower)
            statements[stmt].append(build_line_item(label_clean, value))

    return statements, text_cells


def extract_from_xlsx(
    xlsx_path: str | Path,
    ticker: str = "",
) -> dict[str, Any]:
    """Extract financial statement data from an Excel (.xlsx/.xls) file.

    Scans each worksheet and extracts line items. Sheet names containing
    keywords like 'Income', 'Balance', 'Cash Flow' get pre-classified.

    Args:
        xlsx_path: Path to the .xlsx or .xls file.
        ticker: Optional company ticker for metadata.

    Returns:
        Standard extraction result dict.
    """
    try:
        import openpyxl
    except ImportError:
        return {
            "status": "ERROR",
            "message": "openpyxl not installed. Install with: uv add openpyxl",
            "company": {"name": ticker.upper(), "ticker": ticker.upper(), "fiscal_year_end": ""},
            "periods": [],
            "warnings": [],
        }

    path = Path(xlsx_path)
    if not path.exists():
        return {
            "status": "ERROR",
            "message": f"File not found: {xlsx_path}",
            "company": {"name": ticker.upper(), "ticker": ticker.upper(), "fiscal_year_end": ""},
            "periods": [],
            "warnings": [],
        }

    try:
        wb = openpyxl.load_workbook(str(path), data_only=True, read_only=True)
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"Failed to open workbook: {e}",
            "company": {"name": ticker.upper(), "ticker": ticker.upper(), "fiscal_year_end": ""},
            "periods": [],
            "warnings": [],
        }

    all_statements: dict[str, list[dict[str, Any]]] = {"IS": [], "BS": [], "CFS": []}
    all_text: list[str] = []

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        stmts, texts = _extract_sheet_data(ws, sheet_name)
        for key in all_statements:
            all_statements[key].extend(stmts[key])
        all_text.extend(texts)

    wb.close()

    total_items = sum(len(v) for v in all_statements.values())
    if total_items == 0:
        return {
            "status": "ERROR",
            "message": f"No financial data found in {path.name}",
            "company": {"name": ticker.upper(), "ticker": ticker.upper(), "fiscal_year_end": ""},
            "periods": [],
            "warnings": [],
        }

    unit_name, currency = detect_unit(all_text)

    period = {
        "type": "annual",
        "fiscal_year": 0,
        "end_date": "",
        "source": f"xlsx:{path.name}",
        "statements": {
            "IS": {"unit": unit_name, "line_items": all_statements["IS"]},
            "BS": {"unit": unit_name, "line_items": all_statements["BS"]},
            "CFS": {"unit": unit_name, "line_items": all_statements["CFS"]},
        },
    }

    return {
        "status": "SUCCESS",
        "company": {
            "name": ticker.upper() if ticker else "UNKNOWN",
            "ticker": ticker.upper() if ticker else "",
            "fiscal_year_end": "",
            "currency": currency,
        },
        "periods": [period],
        "warnings": [],
        "metadata": {
            "extraction_method": "xlsx",
            "extraction_timestamp": "",
            "periods_requested": 1,
            "periods_extracted": 1,
        },
    }

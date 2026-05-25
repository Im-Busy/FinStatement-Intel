"""PDF statement extraction (L3) — extract financial tables from PDF annual reports.

Uses PyMuPDF (fitz) for text extraction with coordinate clustering to detect
table boundaries, split dual tables, and handle cross-page continuation.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from src.extraction.line_item_extractor import build_line_item, clean_label
from src.extraction.unit_detector import detect_unit, parse_value

logger = logging.getLogger(__name__)

_STATEMENT_BOUNDARIES = {
    "CFS_start": [
        r"(?:consolidated\s+)?statements?\s+of\s+cash\s+flows?",
        r"cash\s+flow\s+statements?",
        r"cash\s+flows?\s+from\s+operating\s+activities",
    ],
    "CFS_end": [
        r"supplemental\s+(?:cash\s+flow\s+)?(?:disclosure|information)",
        r"notes?\s+to\s+(?:the\s+)?(?:consolidated\s+)?financial\s+statements?",
    ],
    "IS_start": [
        r"(?:consolidated\s+)?statements?\s+of\s+(?:operations|income|earnings)",
        r"income\s+statements?",
        r"profit\s+and\s+loss",
    ],
    "IS_end": [
        r"(?:consolidated\s+)?balance\s+sheets?",
        r"(?:consolidated\s+)?statements?\s+of\s+(?:financial\s+position|cash\s+flows?)",
        r"notes?\s+to\s+(?:the\s+)?(?:consolidated\s+)?financial\s+statements?",
    ],
    "BS_start": [
        r"(?:consolidated\s+)?balance\s+sheets?",
        r"(?:consolidated\s+)?statements?\s+of\s+financial\s+position",
    ],
    "BS_end": [
        r"(?:consolidated\s+)?statements?\s+of\s+(?:operations|income|earnings|cash\s+flows?)",
        r"notes?\s+to\s+(?:the\s+)?(?:consolidated\s+)?financial\s+statements?",
    ],
}

_CFS_SECTION_HEADERS = [
    r"operating\s+activities",
    r"investing\s+activities",
    r"financing\s+activities",
    r"supplemental",
]

_NUMBER_RE = re.compile(r"^\s*\$?\s*-?[\d,]+\.?\d*\s*$")
_PAREN_RE = re.compile(r"^\s*\$?\s*\([\d,]+\.?\d*\)\s*$")
_AMOUNT_RE = re.compile(r"^\s*[\d,]+\.?\d*\s*$")

_PAGE_NUMBER_RE = re.compile(r"^\s*\d{1,3}\s*$")


def _is_numeric(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    cleaned = stripped.lstrip("$").replace(",", "")
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = cleaned[1:-1]
    cleaned = cleaned.lstrip("-")
    try:
        float(cleaned)
        return True
    except ValueError:
        return False


def _extract_text_blocks(
    pdf_path: str,
    pages: list[int] | None = None,
) -> list[dict[str, Any]]:
    """Extract text blocks with coordinates from PDF pages.

    Returns list of blocks with: text, x0, y0, x1, y1, page
    """
    try:
        import fitz
    except ImportError:
        logger.warning("PyMuPDF not installed. Install with: uv add PyMuPDF")
        return []

    blocks: list[dict[str, Any]] = []
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        logger.warning("Failed to open PDF %s: %s", pdf_path, e)
        return []

    target_pages = pages if pages else range(len(doc))
    for page_num in target_pages:
        if page_num >= len(doc):
            break
        page = doc[page_num]
        try:
            text_blocks = page.get_text("blocks")
        except Exception:
            continue
        for block in text_blocks:
            x0, y0, x1, y1, text, block_type, _ = block
            cleaned = text.strip()
            if not cleaned:
                continue
            if _PAGE_NUMBER_RE.match(cleaned) and block_type == 0:
                continue
            blocks.append(
                {
                    "text": cleaned,
                    "x0": round(x0, 1),
                    "y0": round(y0, 1),
                    "x1": round(x1, 1),
                    "y1": round(y1, 1),
                    "page": page_num,
                }
            )
    doc.close()
    return blocks


def _cluster_by_rows(
    blocks: list[dict[str, Any]], y_tolerance: float = 5.0
) -> list[list[dict[str, Any]]]:
    """Group text blocks into rows by Y-coordinate proximity."""
    if not blocks:
        return []

    sorted_blocks = sorted(blocks, key=lambda b: (b["page"], b["y0"]))
    rows: list[list[dict[str, Any]]] = []
    current_row: list[dict[str, Any]] = [sorted_blocks[0]]
    current_y = sorted_blocks[0]["y0"]

    for block in sorted_blocks[1:]:
        if block["page"] != current_row[0]["page"]:
            rows.append(current_row)
            current_row = [block]
            current_y = block["y0"]
        elif abs(block["y0"] - current_y) <= y_tolerance:
            current_row.append(block)
        else:
            rows.append(current_row)
            current_row = [block]
            current_y = block["y0"]

    if current_row:
        rows.append(current_row)

    return rows


def _detect_statement_section(
    row: list[dict[str, Any]],
    current_section: str | None,
) -> str | None:
    """Detect statement type from row text content.

    Updates current_section if a new section header is found.
    Returns the active section type.
    """
    row_text = " ".join(b["text"] for b in row).strip()
    row_lower = row_text.lower()

    if current_section is None:
        for stmt_type in ["CFS", "IS", "BS"]:
            for pattern in _STATEMENT_BOUNDARIES[f"{stmt_type}_start"]:
                if re.search(pattern, row_lower):
                    return stmt_type

    for stmt_type in ["CFS", "IS", "BS"]:
        for pattern in _STATEMENT_BOUNDARIES[f"{stmt_type}_start"]:
            if re.search(pattern, row_lower) and stmt_type != current_section:
                return stmt_type

    for stmt_type in ["CFS", "IS", "BS"]:
        for pattern in _STATEMENT_BOUNDARIES[f"{stmt_type}_end"]:
            if re.search(pattern, row_lower):
                return None

    return current_section


def _is_section_header_row(row: list[dict[str, Any]]) -> bool:
    """Check if a row is a subsection header (e.g., 'Operating Activities')."""
    row_text = " ".join(b["text"] for b in row).strip().lower()
    for pattern in _CFS_SECTION_HEADERS:
        if re.search(pattern, row_text):
            return True
    return False


def _extract_line_items_from_rows(
    rows: list[list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    """Extract financial line items from clustered rows.

    Returns dict of statement type to line item lists.
    """
    statements: dict[str, list[dict[str, Any]]] = {"IS": [], "BS": [], "CFS": []}
    current_section: str | None = None
    seen_labels: set[str] = set()

    for row in rows:
        section = _detect_statement_section(row, current_section)
        if section is not None:
            current_section = section

        if current_section is None:
            continue

        if _is_section_header_row(row):
            continue

        row_text = " ".join(b["text"] for b in row)
        if not row_text.strip():
            continue

        cells = sorted(row, key=lambda b: b["x0"])
        text_cells = [c for c in cells if not _is_numeric(c["text"])]
        numeric_cells = [c for c in cells if _is_numeric(c["text"])]

        if not text_cells or not numeric_cells:
            continue

        label = clean_label(" ".join(c["text"] for c in text_cells))
        if not label or len(label) < 3 or label.lower() in seen_labels:
            continue

        value = parse_value(numeric_cells[-1]["text"])

        if label:
            seen_labels.add(label.lower())
            statements[current_section].append(build_line_item(label, value))

    return statements


def _extract_tables_with_camelot(pdf_path: str, pages: str = "1-end") -> list[dict[str, Any]]:
    """Extract tables from PDF using camelot-py.

    Returns list of tables with rows/columns or empty list if unavailable.
    """
    try:
        import camelot
    except ImportError:
        logger.debug("camelot-py not installed — install with: uv add camelot-py[cv]")
        return []

    try:
        tables = camelot.read_pdf(pdf_path, pages=pages, flavor="lattice")
        if not tables or tables.n == 0:
            tables = camelot.read_pdf(pdf_path, pages=pages, flavor="stream")

        results: list[dict[str, Any]] = []
        for table in tables:
            results.append(
                {
                    "page": table.page,
                    "rows": table.df.values.tolist(),
                    "accuracy": float(table.parsing_report.get("accuracy", 0)),
                }
            )
        return results
    except Exception as e:
        logger.debug("Camelot extraction failed: %s", e)
        return []


def _camelot_tables_to_statements(
    tables: list[dict[str, Any]],
    ticker: str,
) -> dict[str, Any] | None:
    """Convert camelot-extracted tables to standard extraction output format."""
    from src.extraction.line_item_extractor import build_line_item, clean_label
    from src.extraction.unit_detector import parse_value

    all_line_items: dict[str, list[dict[str, Any]]] = {"IS": [], "BS": [], "CFS": []}
    unit_name = "actual"

    for table in tables:
        rows = table.get("rows", [])
        if not rows or len(rows) < 2:
            continue

        for row in rows:
            if not row or len(row) < 2:
                continue
            label = clean_label(str(row[0]))
            if not label:
                continue

            for cell in row[1:]:
                try:
                    value = parse_value(str(cell))
                except (ValueError, TypeError):
                    continue

                lower = label.lower()
                if any(
                    kw in lower
                    for kw in [
                        "revenue",
                        "sales",
                        "cost of",
                        "gross",
                        "operating",
                        "net income",
                        "tax",
                        "ebitda",
                        "eps",
                    ]
                ):
                    all_line_items["IS"].append(build_line_item(label, value))
                elif any(
                    kw in lower
                    for kw in [
                        "assets",
                        "liabilities",
                        "equity",
                        "cash",
                        "receivable",
                        "inventory",
                        "payable",
                        "debt",
                    ]
                ):
                    all_line_items["BS"].append(build_line_item(label, value))
                elif any(
                    kw in lower
                    for kw in [
                        "operating activ",
                        "investing",
                        "financing",
                        "depreciation",
                        "capex",
                        "free cash",
                    ]
                ):
                    all_line_items["CFS"].append(build_line_item(label, value))
                else:
                    all_line_items["BS"].append(build_line_item(label, value))

    total_items = sum(len(items) for items in all_line_items.values())
    if total_items == 0:
        return None

    period = {
        "type": "annual",
        "fiscal_year": 0,
        "end_date": "",
        "source": "pdf-camelot",
        "statements": {
            "IS": {"unit": unit_name, "line_items": all_line_items.get("IS", [])},
            "BS": {"unit": unit_name, "line_items": all_line_items.get("BS", [])},
            "CFS": {"unit": unit_name, "line_items": all_line_items.get("CFS", [])},
        },
    }

    return {
        "status": "SUCCESS",
        "company": {
            "name": ticker.upper(),
            "ticker": ticker.upper(),
            "fiscal_year_end": "",
            "currency": "USD",
        },
        "periods": [period],
        "warnings": [],
        "metadata": {
            "extraction_method": "pdf-camelot",
            "extraction_timestamp": "",
            "periods_requested": 1,
            "periods_extracted": 1,
        },
    }


def extract_from_pdf(
    pdf_path: str,
    ticker: str,
    pages: list[int] | None = None,
) -> dict[str, Any] | None:
    """Extract financial statement data from a PDF document.

    Tries camelot-py table extraction first (if available), then falls
    back to coordinate-clustered text extraction with PyMuPDF.

    Args:
        pdf_path: Path to the PDF file.
        ticker: Stock ticker symbol.
        pages: Optional list of page indices (0-based) to process.

    Returns:
        Extraction result dict or None on failure.
    """
    camelot_tables = _extract_tables_with_camelot(pdf_path)
    if camelot_tables:
        stmts = _camelot_tables_to_statements(camelot_tables, ticker)
        if stmts:
            return stmts

    blocks = _extract_text_blocks(pdf_path, pages)
    if not blocks:
        return None

    rows = _cluster_by_rows(blocks)
    statements = _extract_line_items_from_rows(rows)

    total_items = sum(len(items) for items in statements.values())
    if total_items == 0:
        logger.warning("No statement data extracted from PDF %s", pdf_path)
        return None

    all_text = [b["text"] for b in blocks]
    unit_name, currency = detect_unit(all_text)

    period = {
        "type": "annual",
        "fiscal_year": 0,
        "end_date": "",
        "source": "pdf-extraction",
        "statements": {
            "IS": {"unit": unit_name, "line_items": statements.get("IS", [])},
            "BS": {"unit": unit_name, "line_items": statements.get("BS", [])},
            "CFS": {"unit": unit_name, "line_items": statements.get("CFS", [])},
        },
    }

    return {
        "status": "SUCCESS",
        "company": {
            "name": ticker.upper(),
            "ticker": ticker.upper(),
            "fiscal_year_end": "",
            "currency": currency,
        },
        "periods": [period],
        "warnings": [],
        "metadata": {
            "extraction_method": "pdf",
            "extraction_timestamp": "",
            "periods_requested": 1,
            "periods_extracted": 1,
        },
    }

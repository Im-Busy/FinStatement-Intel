"""HTML table extraction (L2) — scrape financial statement tables from SEC filings.

Strategy:
    1. Fetch the 10-K filing document via SEC EDGAR (HTML version)
    2. Locate financial statement sections by header text patterns
    3. Extract tables within each section using BeautifulSoup
    4. Parse rows into line item label + value pairs
    5. Handle multi-year comparison tables (columns = fiscal years)
"""

from __future__ import annotations

import logging
import re
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag

from src.config import SEC_USER_AGENT
from src.extraction.line_item_extractor import build_line_item, clean_label
from src.extraction.unit_detector import detect_unit, parse_value

logger = logging.getLogger(__name__)

_STATEMENT_HEADERS = {
    "IS": [
        r"consolidated\s+statements?\s+of\s+(operations|income|earnings)",
        r"income\s+statement",
        r"statement\s+of\s+(operations|income|earnings)",
        r"profit\s+and\s+loss",
    ],
    "BS": [
        r"consolidated\s+balance\s+sheets?",
        r"balance\s+sheets?",
        r"statement\s+of\s+financial\s+position",
    ],
    "CFS": [
        r"consolidated\s+statements?\s+of\s+cash\s+flows?",
        r"statement\s+of\s+cash\s+flows?",
        r"cash\s+flow\s+statement",
    ],
}

_YEAR_COL_RE = re.compile(
    r"(?:FY|Fiscal\s+)?(?:year\s+ended\s+)?(?:Dec|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov)[a-z]*\.?\s*\d{1,2},?\s*(\d{4})|(\d{4})\s*$",
    re.IGNORECASE,
)

_VALUE_CELL_RE = re.compile(r"^\s*\$?\s*-?[\d,]+\.?\d*\s*$")
_PAREN_VALUE_RE = re.compile(r"^\s*\$?\s*\([\d,]+\.?\d*\)\s*$")

SECTION_INDICATORS = {
    "IS": [
        "revenue",
        "net sales",
        "cost of",
        "gross profit",
        "gross margin",
        "operating income",
        "operating expenses",
        "net income",
        "earnings per share",
        "income before",
        "provision for income taxes",
    ],
    "BS": [
        "total assets",
        "total current assets",
        "total liabilities",
        "total current liabilities",
        "stockholders' equity",
        "shareholders' equity",
        "cash and cash equivalents",
        "accounts receivable",
        "inventory",
        "property and equipment",
        "goodwill",
        "intangible assets",
        "long-term debt",
        "accounts payable",
        "accumulated",
    ],
    "CFS": [
        "operating activities",
        "investing activities",
        "financing activities",
        "net cash provided by",
        "net cash used in",
        "depreciation and amortization",
        "stock-based compensation",
        "deferred income taxes",
        "purchase of",
        "proceeds from",
        "repayments of",
        "dividends paid",
        "effect of exchange rate",
        "net increase",
        "net decrease",
        "cash at beginning",
        "cash at end",
    ],
}


def _fetch_filing_html(cik: str, accession_number: str, primary_doc: str) -> str | None:
    """Fetch an SEC filing document in HTML format.

    Args:
        cik: 10-digit zero-padded CIK number.
        accession_number: Filing accession number with dashes removed.
        primary_doc: Primary document filename (e.g. 'abc-20240928.htm').

    Returns:
        HTML content string, or None on failure.
    """
    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_number}/{primary_doc}"
    try:
        resp = requests.get(url, headers={"User-Agent": SEC_USER_AGENT}, timeout=30)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        logger.warning("Failed to fetch SEC filing HTML: %s — %s", url, e)
        return None


def _classify_statement_section(text: str) -> str | None:
    """Identify which financial statement a text block belongs to.

    Returns 'IS', 'BS', 'CFS', or None.
    """
    text_lower = text.lower()
    for stmt_type, patterns in _STATEMENT_HEADERS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return stmt_type
    return None


def _classify_by_content(text: str) -> str | None:
    """Fallback: classify statement by row content keywords."""
    text_lower = text.lower()
    scores: dict[str, int] = {}
    for stmt_type, keywords in SECTION_INDICATORS.items():
        scores[stmt_type] = sum(1 for kw in keywords if kw in text_lower)
    if not scores:
        return None
    best = max(scores, key=scores.get)
    return best if scores[best] >= 3 else None


def _parse_year_columns(header_row: Tag) -> list[int]:
    """Extract fiscal years from a table header row.

    Returns sorted list of fiscal years found.
    """
    years: list[int] = []
    for cell in header_row.find_all(["th", "td"]):
        text = cell.get_text(strip=True)
        match = _YEAR_COL_RE.search(text)
        if match:
            yr = match.group(1) or match.group(2)
            if yr:
                years.append(int(yr))
    return sorted(set(years))


def _is_value_cell(text: str) -> bool:
    """Check if cell text looks like a numeric financial value."""
    stripped = text.strip()
    if not stripped:
        return False
    return bool(_VALUE_CELL_RE.match(stripped) or _PAREN_VALUE_RE.match(stripped))


def _extract_statement_tables(soup: BeautifulSoup) -> dict[str, list[dict[str, Any]]]:
    """Extract financial statement tables from parsed HTML.

    Returns dict mapping statement type ('IS', 'BS', 'CFS') to
    lists of line items with labels and values.
    """
    statements: dict[str, list[dict[str, Any]]] = {"IS": [], "BS": [], "CFS": []}

    current_section: str | None = None

    for element in soup.find_all(["div", "table", "p", "h1", "h2", "h3", "h4", "strong"]):
        text = element.get_text(" ", strip=True)
        if not text:
            continue

        section_type = _classify_statement_section(text)
        if section_type:
            current_section = section_type
            continue

        if element.name == "table" and current_section:
            rows = element.find_all("tr")
            if len(rows) < 2:
                continue

            for row in rows:
                cells = row.find_all(["td", "th"])
                if len(cells) < 2:
                    continue

                label_cell = cells[0]
                label = clean_label(label_cell.get_text(strip=True))

                if not label or len(label) < 2:
                    continue

                for cell in cells[1:]:
                    cell_text = cell.get_text(strip=True)
                    if _is_value_cell(cell_text):
                        value = parse_value(cell_text)
                        statements[current_section].append(build_line_item(label, value))
                        break

    if not any(statements.values()):
        current_section = None
        for element in soup.find_all("table"):
            rows = element.find_all("tr")
            if len(rows) < 2:
                continue

            section_text_rows: list[str] = []
            for row in rows:
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    section_text_rows.append(row.get_text(" ", strip=True))

            section_text = " ".join(section_text_rows[:5])
            section_type = _classify_by_content(section_text)
            if not section_type:
                continue

            for row in rows:
                cells = row.find_all(["td", "th"])
                if len(cells) < 2:
                    continue
                label_cell = cells[0]
                label = clean_label(label_cell.get_text(strip=True))
                if not label or len(label) < 2:
                    continue
                for cell in cells[1:]:
                    cell_text = cell.get_text(strip=True)
                    if _is_value_cell(cell_text):
                        value = parse_value(cell_text)
                        statements[section_type].append(build_line_item(label, value))
                        break

    return statements


def extract_from_html_filing(
    cik: str,
    accession_number: str,
    primary_doc: str,
    ticker: str,
) -> dict[str, Any] | None:
    """Extract financial data from an SEC filing HTML document.

    Args:
        cik: 10-digit CIK number.
        accession_number: Filing accession number (dashes removed).
        primary_doc: Primary document filename.
        ticker: Stock ticker symbol.

    Returns:
        Extraction result dict or None on failure.
    """
    html = _fetch_filing_html(cik, accession_number, primary_doc)
    if not html:
        return None

    soup = BeautifulSoup(html, "lxml")

    statements = _extract_statement_tables(soup)

    total_items = sum(len(items) for items in statements.values())
    if total_items == 0:
        logger.warning("No statement data extracted from HTML for %s", ticker)
        return None

    unit_name, currency = detect_unit([soup.get_text(" ", strip=True)])

    period = {
        "type": "annual",
        "fiscal_year": 0,
        "end_date": "",
        "source": "sec-edgar-html",
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
            "cik": cik,
            "fiscal_year_end": "",
            "currency": currency,
        },
        "periods": [period],
        "warnings": [],
        "metadata": {
            "extraction_method": "html",
            "extraction_timestamp": "",
            "periods_requested": 1,
            "periods_extracted": 1,
        },
    }

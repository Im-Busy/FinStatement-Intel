"""Extract financial data from SEC EDGAR, 10-K XBRL instances, HTML, PDF, and API sources.

Escalation order:
    L1  SEC companyfacts API — fast, may lack historical data
    L1.5 SEC 10-K XBRL instances — multi-year, cached locally after first fetch
    L2  HTML tables — scrape SEC filing HTML documents
    L3  PDF documents — PyMuPDF text extraction with coordinate clustering
    L4  OCR — pytesseract/PaddleOCR fallback for scanned PDFs
"""

from __future__ import annotations

import logging
from typing import Any

from src.extraction.edgar_client import get_cik, get_company_facts
from src.extraction.edgar_xbrl_parser import parse_company_facts
from src.extraction.filing_fetcher import fetch_10k_xbrl_facts, merge_facts
from src.extraction.xbrl_fact_converter import convert_facts_to_periods

logger = logging.getLogger(__name__)

SOURCE_HANDLERS: dict[str, str] = {
    "edgar": "_extract_from_edgar",
    "edgar+external": "_extract_from_edgar_with_external",
    "external": "_extract_from_external",
    "html": "_extract_from_html",
    "pdf": "_extract_from_pdf",
    "ocr": "_extract_from_ocr",
    "auto": "auto",
}


def _extract_from_edgar(ticker: str, periods: int) -> dict[str, Any]:
    """Extract financial data from SEC EDGAR (L1 API + L1.5 10-K XBRL instances)."""
    try:
        cik = get_cik(ticker)
    except ValueError as e:
        return {"status": "ERROR", "message": str(e)}
    except Exception as e:
        return {"status": "ERROR", "message": f"SEC API error looking up ticker: {e}"}

    try:
        facts = get_company_facts(cik)
    except Exception as e:
        return {"status": "ERROR", "message": f"SEC API error fetching company facts: {e}"}

    if not facts.get("facts", {}).get("us-gaap"):
        return {
            "status": "ERROR",
            "message": f"No us-gaap financial data found for {ticker} (CIK: {cik})",
        }

    result = parse_company_facts(facts, periods=periods, ticker=ticker)
    company_name = result.get("company", {}).get("name", ticker)

    result.setdefault("metadata", {})
    result["metadata"]["extraction_method"] = "edgar-api"

    populated_periods = sum(
        1
        for p in result.get("periods", [])
        if p.get("statements", {}).get("IS", {}).get("line_items", [])
    )

    if populated_periods < periods:
        logger.info(
            "Companyfacts API only yielded %d statement-periods for %d requested — "
            "supplementing with 10-K XBRL instances",
            populated_periods,
            periods,
        )
        try:
            xbrl_facts = fetch_10k_xbrl_facts(ticker, cik, max_filings=min(periods, 3))
        except Exception as e:
            logger.warning("Failed to fetch 10-K XBRL facts: %s", e)
            xbrl_facts = {}

        if xbrl_facts:
            companyfacts_dict = {}
            for p in result.get("periods", []):
                for stmt_key in ("IS", "BS", "CFS"):
                    for item in p.get("statements", {}).get(stmt_key, {}).get("line_items", []):
                        concept = item.get("xbrl_concept") or item.get("label", "")
                        if concept not in companyfacts_dict:
                            companyfacts_dict[concept] = {}
                        date_key = p.get("end_date", "")
                        companyfacts_dict[concept][date_key] = item.get("value", 0)

            merged = merge_facts(companyfacts_dict, xbrl_facts)
            result = convert_facts_to_periods(
                merged,
                ticker,
                company_name,
                max_periods=periods,
            )
            result["metadata"]["extraction_method"] = "edgar-api+xbrl-instance"
            result["metadata"]["xbrl_supplemented"] = True

    if not result["periods"]:
        result["status"] = "WARNING"
        result["warnings"].append("No financial data found for the requested periods")

    return result


def _extract_from_html(ticker: str, periods: int) -> dict[str, Any]:
    """Extract financial data from HTML tables (L2) via SEC filing documents."""
    from src.extraction.edgar_client import get_annual_filings, get_cik, get_submissions
    from src.extraction.html_extractor import extract_from_html_filing

    try:
        cik = get_cik(ticker)
    except ValueError as e:
        return {
            "status": "ERROR",
            "message": str(e),
            "company": {"name": ticker.upper(), "ticker": ticker.upper(), "fiscal_year_end": ""},
            "periods": [],
            "warnings": [],
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"SEC API error: {e}",
            "company": {"name": ticker.upper(), "ticker": ticker.upper(), "fiscal_year_end": ""},
            "periods": [],
            "warnings": [],
        }

    try:
        submissions = get_submissions(cik)
        filings = get_annual_filings(
            submissions, limit=min(periods, 3), form_types=["10-K", "10-K405"]
        )
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"SEC filing lookup failed: {e}",
            "company": {"name": ticker.upper(), "ticker": ticker.upper(), "fiscal_year_end": ""},
            "periods": [],
            "warnings": [],
        }

    if not filings:
        return {
            "status": "WARNING",
            "message": f"No 10-K filings found for {ticker}",
            "company": {"name": ticker.upper(), "ticker": ticker.upper(), "fiscal_year_end": ""},
            "periods": [],
            "warnings": [],
        }

    for filing in filings[: min(periods, 3)]:
        accession = filing.get("accession_number", "").replace("-", "")
        primary_doc = filing.get("primary_document", "")
        if not accession or not primary_doc:
            continue

        result = extract_from_html_filing(cik, accession, primary_doc, ticker)
        if result and result.get("periods"):
            return result

    return {
        "status": "WARNING",
        "message": f"HTML extraction yielded no usable data for {ticker}",
        "company": {"name": ticker.upper(), "ticker": ticker.upper(), "fiscal_year_end": ""},
        "periods": [],
        "warnings": [],
    }


def _extract_from_pdf(ticker: str, periods: int) -> dict[str, Any]:
    """Extract financial data from PDF documents (L3) — PyMuPDF with coordinate clustering."""
    from pathlib import Path

    from src.extraction.edgar_client import get_annual_filings, get_cik, get_submissions
    from src.extraction.pdf_extractor import extract_from_pdf

    try:
        cik = get_cik(ticker)
    except ValueError as e:
        return {
            "status": "ERROR",
            "message": str(e),
            "company": {"name": ticker.upper(), "ticker": ticker.upper(), "fiscal_year_end": ""},
            "periods": [],
            "warnings": [],
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"SEC API error: {e}",
            "company": {"name": ticker.upper(), "ticker": ticker.upper(), "fiscal_year_end": ""},
            "periods": [],
            "warnings": [],
        }

    try:
        import requests

        from src.config import SEC_USER_AGENT

        submissions = get_submissions(cik)
        filings = get_annual_filings(submissions, limit=min(periods, 3))
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"SEC filing lookup failed: {e}",
            "company": {"name": ticker.upper(), "ticker": ticker.upper(), "fiscal_year_end": ""},
            "periods": [],
            "warnings": [],
        }

    if not filings:
        return {
            "status": "WARNING",
            "message": f"No 10-K filings found for {ticker}",
            "company": {"name": ticker.upper(), "ticker": ticker.upper(), "fiscal_year_end": ""},
            "periods": [],
            "warnings": [],
        }

    for filing in filings[: min(periods, 3)]:
        accession = filing.get("accession_number", "").replace("-", "")
        if not accession:
            continue

        pdf_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/{accession}.pdf"
        pdf_path = Path(f"data/filings/{ticker}/{accession}.pdf")
        pdf_path.parent.mkdir(parents=True, exist_ok=True)

        if not pdf_path.exists():
            try:
                resp = requests.get(pdf_url, headers={"User-Agent": SEC_USER_AGENT}, timeout=60)
                resp.raise_for_status()
                pdf_path.write_bytes(resp.content)
            except Exception:
                continue

        result = extract_from_pdf(str(pdf_path), ticker)
        if result and result.get("periods"):
            return result

    return {
        "status": "WARNING",
        "message": f"PDF extraction yielded no usable data for {ticker}",
        "company": {"name": ticker.upper(), "ticker": ticker.upper(), "fiscal_year_end": ""},
        "periods": [],
        "warnings": [],
    }


def _extract_from_ocr(ticker: str, periods: int) -> dict[str, Any]:
    """Extract financial data via OCR (L4) — OCR fallback for scanned PDFs."""
    from pathlib import Path

    from src.extraction.edgar_client import get_annual_filings, get_cik, get_submissions
    from src.extraction.ocr_extractor import extract_with_ocr

    try:
        cik = get_cik(ticker)
    except ValueError as e:
        return {
            "status": "ERROR",
            "message": str(e),
            "company": {"name": ticker.upper(), "ticker": ticker.upper(), "fiscal_year_end": ""},
            "periods": [],
            "warnings": [],
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"SEC API error: {e}",
            "company": {"name": ticker.upper(), "ticker": ticker.upper(), "fiscal_year_end": ""},
            "periods": [],
            "warnings": [],
        }

    try:
        import requests

        from src.config import SEC_USER_AGENT

        submissions = get_submissions(cik)
        filings = get_annual_filings(submissions, limit=min(periods, 3))
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"SEC filing lookup failed: {e}",
            "company": {"name": ticker.upper(), "ticker": ticker.upper(), "fiscal_year_end": ""},
            "periods": [],
            "warnings": [],
        }

    if not filings:
        return {
            "status": "WARNING",
            "message": f"No 10-K filings found for {ticker}",
            "company": {"name": ticker.upper(), "ticker": ticker.upper(), "fiscal_year_end": ""},
            "periods": [],
            "warnings": [],
        }

    for filing in filings[: min(periods, 3)]:
        accession = filing.get("accession_number", "").replace("-", "")
        if not accession:
            continue

        pdf_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/{accession}.pdf"
        pdf_path = Path(f"data/filings/{ticker}/{accession}_ocr.pdf")
        pdf_path.parent.mkdir(parents=True, exist_ok=True)

        if not pdf_path.exists():
            try:
                resp = requests.get(pdf_url, headers={"User-Agent": SEC_USER_AGENT}, timeout=60)
                resp.raise_for_status()
                pdf_path.write_bytes(resp.content)
            except Exception:
                continue

        result = extract_with_ocr(str(pdf_path), ticker)
        if result and result.get("periods"):
            return result

    return {
        "status": "WARNING",
        "message": f"OCR extraction yielded no usable data for {ticker}",
        "company": {"name": ticker.upper(), "ticker": ticker.upper(), "fiscal_year_end": ""},
        "periods": [],
        "warnings": [],
    }


def _extract_from_external(ticker: str, periods: int) -> dict[str, Any]:
    """Extract financial data from external sources (Kaggle, GitHub, web)."""
    from src.extraction.external_searcher import find_and_download_financial_data

    result = find_and_download_financial_data(ticker, periods=periods)
    if result:
        return result
    return {
        "status": "WARNING",
        "message": f"No external datasets found for {ticker}",
        "company": {"name": ticker.upper(), "ticker": ticker.upper(), "fiscal_year_end": ""},
        "periods": [],
    }


def _extract_from_edgar_with_external(ticker: str, periods: int) -> dict[str, Any]:
    """Extract from EDGAR first, fall back to external search if EDGAR fails."""
    result = _extract_from_edgar(ticker, periods)

    if result["status"] in ("ERROR", "WARNING") and len(result.get("periods", [])) < 2:
        logger.info("EDGAR yielded insufficient data, trying external sources for %s", ticker)
        try:
            ext_result = _extract_from_external(ticker, periods)
            if ext_result["status"] != "ERROR" and ext_result.get("periods"):
                result = ext_result
                if "warnings" not in result:
                    result["warnings"] = []
                result["warnings"].append("Data sourced from external (non-EDGAR) sources")
        except Exception as e:
            logger.warning("External search failed for %s: %s", ticker, e)

    return result


def extract_financial_data(
    ticker: str,
    periods: int = 5,
    source: str = "edgar",
) -> dict[str, Any]:
    """Extract raw financial data for a company.

    Args:
        ticker: Stock ticker symbol.
        periods: Number of fiscal periods to extract.
        source: Data source preference (edgar, html, pdf, ocr, auto).

    Returns:
        Extraction result JSON with status, company info, and period data.
    """
    ticker = ticker.upper().strip()
    logger.info("Extracting %s financials: %d periods from %s", ticker, periods, source)

    handler_name = SOURCE_HANDLERS.get(source)
    if handler_name is None:
        return {
            "status": "ERROR",
            "message": f"Unknown source '{source}'. Valid sources: {list(SOURCE_HANDLERS)}",
        }

    if source == "auto":
        from src.extraction.source_router import route_source

        return route_source(source, ticker, periods)

    handler = globals().get(handler_name)
    if handler is None:
        return {
            "status": "ERROR",
            "message": f"Source handler '{handler_name}' not found",
        }

    result = handler(ticker, periods)

    if "metadata" not in result:
        result["metadata"] = {
            "extraction_method": source,
            "periods_requested": periods,
            "periods_extracted": len(result.get("periods", [])),
        }

    if "warnings" not in result:
        result["warnings"] = []

    result.setdefault("company", {"name": ticker, "ticker": ticker, "fiscal_year_end": ""})

    return result

"""SEC EDGAR API client — ticker-to-CIK lookup, company facts, submissions.

Handles SEC-mandated User-Agent header and rate limiting (≤10 req/s).
Uses local cache layer (edgar_cache.py) to reduce API calls.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

from src.config import RATELIMIT_DELAY, SEC_BASE_URL, SEC_SUBMISSIONS_URL, SEC_USER_AGENT
from src.extraction.edgar_cache import (
    cache_facts,
    cache_submissions,
    cache_tickers,
    get_cached_facts,
    get_cached_submissions,
    get_cached_tickers,
)

logger = logging.getLogger(__name__)

_SESSION: requests.Session | None = None


def _get_session() -> requests.Session:
    global _SESSION  # noqa: PLW0603
    if _SESSION is None:
        _SESSION = requests.Session()
        _SESSION.headers.update(
            {
                "User-Agent": SEC_USER_AGENT,
                "Accept": "application/json",
            }
        )
    return _SESSION


def _rate_limit() -> None:
    time.sleep(RATELIMIT_DELAY)


def get_cik(ticker: str) -> str:
    """Map ticker to CIK number via SEC company_tickers.json.

    Args:
        ticker: Stock ticker symbol (case-insensitive).

    Returns:
        10-digit zero-padded CIK string.

    Raises:
        ValueError: If ticker not found in SEC database.
        requests.RequestException: If SEC API request fails.
    """
    url = "https://www.sec.gov/files/company_tickers.json"
    sess = _get_session()

    cached = get_cached_tickers()
    if cached is not None:
        data = cached
    else:
        _rate_limit()
        logger.info("Fetching company_tickers.json from SEC")
        resp = sess.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        cache_tickers(data)
    logger.info("Looking up CIK for ticker %s", ticker)
    ticker_upper = ticker.upper().strip()

    for _index, company in data.items():
        if company.get("ticker", "").upper() == ticker_upper:
            cik = company.get("cik_str", 0)
            cik_padded = str(cik).zfill(10)
            logger.info("Found CIK %s for %s", cik_padded, ticker_upper)
            return cik_padded

    raise ValueError(f"Ticker '{ticker}' not found on SEC EDGAR")


def get_company_facts(cik: str) -> dict[str, Any]:
    """Fetch XBRL company facts from SEC API.

    Args:
        cik: 10-digit zero-padded CIK string.

    Returns:
        Raw company facts JSON dict.

    Raises:
        requests.RequestException: If SEC API request fails.
    """
    url = f"{SEC_BASE_URL}/xbrl/companyfacts/CIK{cik}.json"
    sess = _get_session()

    cached = get_cached_facts(cik)
    if cached is not None:
        return cached

    _rate_limit()
    logger.info("Fetching company facts for CIK %s", cik)
    resp = sess.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    cache_facts(cik, data)
    return data


def get_submissions(cik: str) -> dict[str, Any]:
    """Fetch company submissions (filing history) from SEC.

    Args:
        cik: 10-digit zero-padded CIK string.

    Returns:
        Raw submissions JSON dict.

    Raises:
        requests.RequestException: If SEC API request fails.
    """
    url = f"{SEC_SUBMISSIONS_URL}/CIK{cik}.json"
    sess = _get_session()

    cached = get_cached_submissions(cik)
    if cached is not None:
        return cached

    _rate_limit()
    logger.info("Fetching submissions for CIK %s", cik)
    resp = sess.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    cache_submissions(cik, data)
    return data


def get_annual_filings(
    submissions: dict[str, Any],
    form_type: str = "10-K",
    limit: int = 10,
    form_types: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Extract annual filing metadata from SEC submissions JSON.

    Args:
        submissions: Raw submissions JSON from get_submissions().
        form_type: Single filing form type (10-K, 10-Q, 20-F, etc.).
        limit: Maximum number of filings to return.
        form_types: Optional list of form types (e.g. ["10-K", "10-K405"]).
                    Overrides form_type if provided.

    Returns:
        List of filing dicts with keys:
            accession_number, filing_date, report_date, primary_document.
    """
    recent = submissions.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    accessions = recent.get("accessionNumber", [])
    filing_dates = recent.get("filingDate", [])
    report_dates = recent.get("reportDate", [])
    documents = recent.get("primaryDocument", [])

    accepted = set(form_types) if form_types else {form_type}

    filings: list[dict[str, Any]] = []
    for i, form in enumerate(forms):
        if form in accepted and len(filings) < limit:
            filings.append(
                {
                    "form_type": form,
                    "accession_number": accessions[i] if i < len(accessions) else "",
                    "filing_date": filing_dates[i] if i < len(filing_dates) else "",
                    "report_date": report_dates[i] if i < len(report_dates) else "",
                    "primary_document": documents[i] if i < len(documents) else "",
                }
            )

    logger.info("Found %d filings for forms %s", len(filings), accepted)
    return filings


def download_filing_document(cik: str, accession_number: str, document: str) -> str:
    """Download a specific SEC filing document.

    Args:
        cik: 10-digit zero-padded CIK string.
        accession_number: Accession number from EDGAR (with dashes).
        document: Document filename (e.g., primary_document from get_annual_filings).

    Returns:
        Raw text content of the filing document.

    Raises:
        requests.RequestException: If download fails.
    """
    accession_clean = accession_number.replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{document}"
    sess = _get_session()
    _rate_limit()

    logger.info("Downloading filing document: %s", url)
    resp = sess.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text

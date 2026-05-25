"""SEC 10-K filing fetcher — downloads and caches XBRL instance documents.

Each 10-K filing includes a companion XBRL instance XML that contains
multi-year comparative financial data tagged with GAAP concepts.

Cache structure:
    data/filings/<ticker>/
        <accession_number>_facts.json   — parsed facts
        <accession_number>_inst.xml     — raw XBRL instance (cached)
        index.json                      — index of cached filings
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from src.config import DATA_DIR
from src.extraction.edgar_client import (
    _get_session,
    _rate_limit,
    get_annual_filings,
    get_submissions,
)

logger = logging.getLogger(__name__)

FILINGS_DIR = DATA_DIR / "filings"


def _filings_dir(ticker: str) -> Path:
    path = FILINGS_DIR / ticker.upper()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _load_index(ticker: str) -> dict[str, dict[str, Any]]:
    index_path = _filings_dir(ticker) / "index.json"
    if index_path.exists():
        return json.loads(index_path.read_text())
    return {}


def _save_index(ticker: str, index: dict[str, dict[str, Any]]) -> None:
    index_path = _filings_dir(ticker) / "index.json"
    index_path.write_text(json.dumps(index, indent=2))


def _parse_xbrl_contexts(xml_text: str) -> dict[str, str]:
    """Extract context ID -> end_date mapping from XBRL."""
    contexts: dict[str, str] = {}
    pattern = (
        r'<context id="([^"]+)".*?'
        r"(?:<startDate>[^<]+</startDate>.*?<endDate>([^<]+)</endDate>"
        r"|<instant>([^<]+)</instant>)"
        r".*?</context>"
    )
    for m in re.finditer(pattern, xml_text, re.DOTALL):
        ctx_id = m.group(1)
        if m.group(2):
            contexts[ctx_id] = m.group(2)
        elif m.group(3):
            contexts[ctx_id] = m.group(3)
    return contexts


def _parse_xbrl_units(xml_text: str) -> dict[str, str]:
    """Extract unit ID -> measure mapping."""
    units: dict[str, str] = {}
    for m in re.finditer(
        r'<unit id="([^"]+)">.*?<measure>([^<]+)</measure>.*?</unit>',
        xml_text,
        re.DOTALL,
    ):
        units[m.group(1)] = m.group(2)
    return units


def _parse_xbrl_facts(xml_text: str) -> dict[str, dict[str, float]]:
    """Parse all us-gaap facts from XBRL instance, keyed by concept.

    Returns:
        {concept_name: {end_date: value}} where end_date is YYYY-MM-DD.
    """
    contexts = _parse_xbrl_contexts(xml_text)

    facts: dict[str, dict[str, float]] = {}
    for m in re.finditer(
        r"<(?:[^>]*:)?us-gaap:([^\s>]+)[^>]*"
        r'contextRef="([^"]+)"[^>]*'
        r'(?:unitRef="[^"]*")?[^>]*>'
        r"([\d,.]+(?:\.\d+)?)"
        r"<",
        xml_text,
    ):
        concept = m.group(1)
        ctx_id = m.group(2)
        value_str = m.group(3).replace(",", "")

        end_date = contexts.get(ctx_id, "")
        if not end_date:
            continue
        end_date = end_date[:10]

        try:
            val = float(value_str)
        except ValueError:
            continue

        if concept not in facts:
            facts[concept] = {}
        facts[concept][end_date] = val

    return facts


def fetch_10k_xbrl_facts(
    ticker: str,
    cik: str,
    max_filings: int = 3,
    force_refresh: bool = False,
) -> dict[str, dict[str, float]]:
    """Download and parse XBRL facts from the most recent 10-K filing.

    Each 10-K typically contains 3 years of comparative data. Multiple
    filings can be merged to get longer history.

    Args:
        ticker: Stock ticker symbol.
        cik: 10-digit zero-padded CIK string.
        max_filings: Maximum number of 10-K filings to fetch.
        force_refresh: If True, re-download even if cached.

    Returns:
        Dict mapping concept_name -> {end_date_str -> value}.
    """
    index = _load_index(ticker)
    filings_dir = _filings_dir(ticker)

    submissions = get_submissions(cik)
    filings = get_annual_filings(submissions, "10-K", limit=max_filings)

    all_facts: dict[str, dict[str, float]] = {}

    for filing in filings:
        acc = filing["accession_number"]
        acc_clean = acc.replace("-", "")
        report_date = filing["report_date"]
        doc = filing["primary_document"]
        xbrl_filename = doc.replace(".htm", "_htm.xml")

        cache_key = acc_clean
        cache_facts_path = filings_dir / f"{cache_key}_facts.json"
        cache_xml_path = filings_dir / f"{cache_key}_inst.xml"

        if not force_refresh and cache_facts_path.exists():
            logger.info("Loading cached XBRL facts for %s %s", ticker, report_date)
            cached = json.loads(cache_facts_path.read_text())
            for concept, dates in cached.items():
                if concept not in all_facts:
                    all_facts[concept] = {}
                all_facts[concept].update(dates)
            continue

        xbrl_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_clean}/{xbrl_filename}"

        logger.info("Downloading XBRL instance for %s %s: %s", ticker, report_date, xbrl_url)
        sess = _get_session()
        _rate_limit()
        resp = sess.get(xbrl_url, timeout=60)
        resp.raise_for_status()
        xml_text = resp.text

        cache_xml_path.write_text(xml_text, encoding="utf-8")

        facts = _parse_xbrl_facts(xml_text)
        cache_facts_path.write_text(json.dumps(facts, indent=2, sort_keys=True))

        for concept, dates in facts.items():
            if concept not in all_facts:
                all_facts[concept] = {}
            all_facts[concept].update(dates)

        index[cache_key] = {
            "report_date": report_date,
            "accession_number": acc,
            "concepts_count": len(facts),
            "cached_at": filing["filing_date"],
        }

    _save_index(ticker, index)
    logger.info(
        "Fetched %d concepts across %d dates for %s from %d filings",
        len(all_facts),
        sum(len(v) for v in all_facts.values()),
        ticker,
        len(filings),
    )
    return all_facts


def fetch_companyfacts_api(
    ticker: str,
    cik: str,
    periods: int = 5,
) -> dict[str, dict[str, float]]:
    """Fetch data from SEC companyfacts API (original method).

    Returns:
        Dict mapping concept_name -> {end_date_str -> value}.
    """
    from src.extraction.edgar_client import get_company_facts

    facts_raw = get_company_facts(cik)
    us_gaap = facts_raw.get("facts", {}).get("us-gaap", {})

    result: dict[str, dict[str, float]] = {}
    for concept_name, concept_data in us_gaap.items():
        units = concept_data.get("units", {})
        for unit, entries in units.items():
            if not isinstance(entries, list):
                continue
            for entry in entries:
                fy = entry.get("fy")
                frame = entry.get("frame", "")
                end_date = entry.get("end", "")
                val = entry.get("val")

                if fy is None and frame:
                    try:
                        fy = int(frame[2:6])
                    except (ValueError, IndexError):
                        pass
                if val is None:
                    continue

                date_key = end_date[:10] if end_date else f"FY{fy}"
                if concept_name not in result:
                    result[concept_name] = {}
                result[concept_name][date_key] = val

    return result


def merge_facts(
    companyfacts: dict[str, dict[str, float]],
    xbrl_facts: dict[str, dict[str, float]],
) -> dict[str, dict[str, float]]:
    """Merge two fact dictionaries, with companyfacts taking priority."""
    merged = dict(companyfacts)
    for concept, dates in xbrl_facts.items():
        if concept not in merged:
            merged[concept] = {}
        for date, val in dates.items():
            if date not in merged[concept]:
                merged[concept][date] = val
    return merged

"""External financial data source searcher — uses Tavily/Exa to find
financial statement datasets on Kaggle, GitHub, and other platforms.

When the SEC EDGAR API and 10-K XBRL instances are insufficient (e.g.,
non-US companies, pre-XBRL filings, or data gaps), this module searches
for alternative data sources and downloads them locally.

Cache: data/external/<ticker>/
"""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import Any

from src.config import DATA_DIR

logger = logging.getLogger(__name__)

EXTERNAL_DIR = DATA_DIR / "external"

SOURCE_PRIORITY = [
    "kaggle",
    "github_raw",
    "web_csv",
    "web_json",
]


def _external_dir(ticker: str) -> Path:
    path = EXTERNAL_DIR / ticker.upper()
    path.mkdir(parents=True, exist_ok=True)
    return path


def search_financial_datasets(
    ticker: str,
    tool: str = "tavily",
) -> list[dict[str, Any]]:
    """Search for financial statement datasets using Tavily or Exa.

    Args:
        ticker: Stock ticker symbol.
        tool: Search tool to use ("tavily" or "exa").

    Returns:
        List of search result dicts with title, url, snippet.
    """
    company_search = f"{ticker} financial statements dataset 10-K annual CSV download site:kaggle.com OR site:github.com"

    results: list[dict[str, Any]] = []

    try:
        if tool == "tavily":
            from tavily import TavilyClient

            client = TavilyClient()
            response = client.search(
                query=company_search,
                search_depth="advanced",
                max_results=10,
                include_raw_content=False,
            )
            for r in response.get("results", []):
                results.append(
                    {
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "snippet": r.get("content", ""),
                        "source": "tavily",
                    }
                )
        elif tool == "exa":
            try:
                from exa_py import Exa
            except ImportError:
                logger.warning("Exa SDK not available — install with: uv add exa-py")
                return results

            try:
                client = Exa()
                response = client.search_and_contents(
                    company_search,
                    type="auto",
                    num_results=10,
                    text=True,
                )
                for r in response.results:
                    results.append(
                        {
                            "title": getattr(r, "title", "") or "",
                            "url": getattr(r, "url", "") or "",
                            "snippet": getattr(r, "text", "") or "",
                            "source": "exa",
                        }
                    )
            except Exception as e:
                logger.warning("Exa search failed for %s: %s", ticker, e)

    except ImportError:
        logger.warning("Tavily client not available — install with: uv add tavily-python")
    except Exception as e:
        logger.warning("External search failed for %s: %s", ticker, e)

    return results


def search_kaggle_datasets(ticker: str) -> list[dict[str, Any]]:
    """Search Kaggle for financial statement datasets.

    Uses Tavily to search kaggle.com for relevant datasets.

    Returns:
        List of dataset info dicts.
    """
    return search_financial_datasets(f"{ticker} financial statements annual", "tavily")


def download_dataset(url: str, ticker: str, name: str = "") -> Path | None:
    """Download a financial dataset file and cache it locally.

    Args:
        url: Direct download URL.
        ticker: Stock ticker for cache directory.
        name: Optional filename, inferred from URL if not provided.

    Returns:
        Path to cached file, or None if download fails.
    """
    import requests

    ext_dir = _external_dir(ticker)
    if not name:
        name = url.rsplit("/", 1)[-1].split("?")[0] or "dataset.csv"
    dest = ext_dir / name

    if dest.exists():
        logger.info("Dataset already cached: %s", dest)
        return dest

    try:
        logger.info("Downloading dataset: %s -> %s", url, dest)
        resp = requests.get(url, timeout=60, stream=True)
        resp.raise_for_status()
        with dest.open("wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return dest
    except Exception as e:
        logger.warning("Failed to download dataset from %s: %s", url, e)
        return None


def clone_github_repo(repo_url: str, ticker: str) -> Path | None:
    """Clone a GitHub repository containing financial data.

    Args:
        repo_url: GitHub repo URL (https://github.com/user/repo.git).
        ticker: Stock ticker for cache directory.

    Returns:
        Path to cloned repo, or None if clone fails.
    """
    ext_dir = _external_dir(ticker)
    repo_name = repo_url.rstrip("/").rsplit("/", 1)[-1].replace(".git", "")
    dest = ext_dir / repo_name

    if dest.exists():
        logger.info("Repository already cloned: %s", dest)
        return dest

    try:
        logger.info("Cloning repository: %s -> %s", repo_url, dest)
        shutil.rmtree(dest, ignore_errors=True)
        import subprocess

        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(dest)],
            check=True,
            capture_output=True,
            timeout=120,
        )
        return dest
    except Exception as e:
        logger.warning("Failed to clone repo %s: %s", repo_url, e)
        return None


def find_and_download_financial_data(
    ticker: str,
    cik: str = "",
    periods: int = 5,
) -> dict[str, Any] | None:
    """Find and download financial data from external sources.

    This is the L3 escalation — used when EDGAR XBRL sources are
    insufficient. Searches Kaggle, GitHub, and the web for structured
    financial statement datasets.

    Args:
        ticker: Stock ticker symbol.
        cik: CIK number (if known, for SEC-specific searches).
        periods: Number of periods needed.

    Returns:
        Extraction-format dict if data found, None otherwise.
    """
    datasets = search_financial_datasets(ticker)

    if not datasets:
        logger.info("No external datasets found for %s", ticker)
        return None

    logger.info(
        "Found %d potential external data sources for %s",
        len(datasets),
        ticker,
    )

    for ds in datasets:
        url = ds.get("url", "")

        if "kaggle.com" in url:
            downloaded = _try_kaggle_download(url, ticker)
            if downloaded:
                return _parse_downloaded_file(downloaded, ticker, periods)

        elif "github.com" in url and ("csv" in url.lower() or "raw" in url.lower()):
            name = url.rsplit("/", 1)[-1]
            downloaded = download_dataset(url, ticker, name)
            if downloaded:
                return _parse_downloaded_file(downloaded, ticker, periods)

    return None


def _try_kaggle_download(url: str, ticker: str) -> Path | None:
    """Attempt to download a Kaggle dataset.

    Kaggle typically requires API authentication. This method tries:
    1. kagglehub library (pip install kagglehub)
    2. Direct download via kaggle API
    """
    import re

    owner_match = re.search(r"kaggle\.com/datasets/([^/]+)/([^/\s?#]+)", url)
    if not owner_match:
        return None

    owner = owner_match.group(1)
    dataset = owner_match.group(2)
    dataset_path = f"{owner}/{dataset}"

    try:
        import kagglehub

        logger.info("Downloading Kaggle dataset: %s", dataset_path)
        download_path = kagglehub.dataset_download(dataset_path)
        return Path(download_path)
    except ImportError:
        logger.info("kagglehub not installed. Install with: uv add kagglehub")
    except Exception as e:
        logger.warning("Kaggle download failed for %s: %s", dataset_path, e)

    return None


def _parse_downloaded_file(
    file_path: Path,
    ticker: str,
    periods: int,
) -> dict[str, Any] | None:
    """Parse a downloaded file (CSV/JSON) into extraction format.

    Attempts to map CSV columns or JSON keys to standard financial line items.
    Falls back to raw data passthrough if mapping fails.

    Returns:
        Extraction-format dict or None if parsing fails.
    """
    import csv

    suffix = file_path.suffix.lower()

    try:
        if suffix == ".json":
            data = json.loads(file_path.read_text(encoding="utf-8", errors="replace"))
            return _map_json_to_extraction(data, ticker, periods)

        elif suffix == ".csv":
            with file_path.open("r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            if not rows:
                return None
            return _map_csv_to_extraction(rows, ticker, periods)

        else:
            logger.info("Unsupported file format: %s", suffix)
            return None
    except Exception as e:
        logger.warning("Failed to parse %s: %s", file_path, e)
        return None


def _map_csv_to_extraction(
    rows: list[dict[str, str]],
    ticker: str,
    periods: int,
) -> dict[str, Any] | None:
    """Map CSV rows to standard extraction output format.

    Uses header heuristics to identify financial columns and rows.
    """
    from src.extraction.line_item_extractor import build_line_item, clean_label
    from src.extraction.unit_detector import parse_value

    if not rows:
        return None

    headers = list(rows[0].keys()) if rows else []
    label_col = None
    value_cols: list[str] = []

    for h in headers:
        lower = h.lower().strip()
        if any(
            kw in lower
            for kw in ["label", "item", "line item", "name", "description", "concept", "field"]
        ):
            label_col = h
        elif any(kw in lower for kw in ["value", "amount", "balance", "usd", "$", "20", "fy"]):
            if h != label_col:
                value_cols.append(h)

    if not label_col:
        for h in headers:
            if h not in value_cols:
                label_col = h
                break

    if not label_col and headers:
        label_col = headers[0]

    if not value_cols and len(headers) >= 2:
        for h in headers[1:]:
            value_cols.append(h)

    if not label_col or not value_cols:
        return None

    all_line_items: dict[str, list[dict[str, Any]]] = {"IS": [], "BS": [], "CFS": []}

    for row in rows[:200]:
        label = row.get(label_col, "").strip()
        if not label:
            continue
        label = clean_label(label)

        for vc in value_cols[:periods]:
            raw_val = row.get(vc, "").strip()
            if not raw_val:
                continue
            try:
                value = parse_value(raw_val)
            except (ValueError, TypeError):
                continue

            item = build_line_item(label, value)
            lower = label.lower()
            if any(
                kw in lower
                for kw in [
                    "revenue",
                    "sales",
                    "cost",
                    "gross",
                    "operating",
                    "net income",
                    "eps",
                    "tax",
                    "r&d",
                    "ebitda",
                ]
            ):
                all_line_items["IS"].append(item)
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
                    "goodwill",
                    "property",
                ]
            ):
                all_line_items["BS"].append(item)
            elif any(
                kw in lower
                for kw in [
                    "cash flow",
                    "operating activ",
                    "investing",
                    "financing",
                    "depreciation",
                    "capex",
                    "dividend",
                ]
            ):
                all_line_items["CFS"].append(item)
            else:
                all_line_items["BS"].append(item)

    total_items = sum(len(items) for items in all_line_items.values())
    if total_items == 0:
        return None

    period_data = {
        "type": "annual",
        "fiscal_year": 0,
        "end_date": "",
        "source": "external-csv",
        "statements": {
            "IS": {"unit": "actual", "line_items": all_line_items.get("IS", [])},
            "BS": {"unit": "actual", "line_items": all_line_items.get("BS", [])},
            "CFS": {"unit": "actual", "line_items": all_line_items.get("CFS", [])},
        },
    }

    return {
        "status": "SUCCESS",
        "company": {"name": ticker.upper(), "ticker": ticker.upper(), "fiscal_year_end": ""},
        "periods": [period_data],
        "warnings": ["Data extracted from external CSV source"],
        "external_source": "external-csv",
        "metadata": {
            "extraction_method": "external-csv",
            "periods_requested": periods,
            "periods_extracted": 1,
        },
    }


def _map_json_to_extraction(
    data: Any,
    ticker: str,
    periods: int,
) -> dict[str, Any] | None:
    """Map JSON data to extraction output format."""
    from src.extraction.line_item_extractor import build_line_item, clean_label
    from src.extraction.unit_detector import parse_value

    if isinstance(data, list):
        if not data:
            return None
        records = data
    elif isinstance(data, dict):
        candidates = (
            data.get("data") or data.get("results") or data.get("records") or data.get("items")
        )
        if isinstance(candidates, list):
            records = candidates
        else:
            records = [data]
    else:
        return None

    all_line_items: dict[str, list[dict[str, Any]]] = {"IS": [], "BS": [], "CFS": []}

    for record in records[:200]:
        if not isinstance(record, dict):
            continue

        for key, value in record.items():
            if key in ("ticker", "company", "cik", "fiscal_year", "period", "year", "date"):
                continue
            if not isinstance(value, (int, float)):
                try:
                    value = parse_value(str(value))
                except (ValueError, TypeError):
                    continue

            item = build_line_item(clean_label(key), value)
            lower = key.lower()
            if any(
                kw in lower
                for kw in [
                    "revenue",
                    "sales",
                    "cost",
                    "gross",
                    "operating",
                    "net_income",
                    "eps",
                    "tax",
                    "r_d",
                    "ebitda",
                ]
            ):
                all_line_items["IS"].append(item)
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
                    "goodwill",
                    "property",
                ]
            ):
                all_line_items["BS"].append(item)
            elif any(
                kw in lower
                for kw in [
                    "cash_flow",
                    "operating_cf",
                    "investing",
                    "financing",
                    "depreciation",
                    "capex",
                    "dividend",
                ]
            ):
                all_line_items["CFS"].append(item)
            else:
                all_line_items["BS"].append(item)

    total_items = sum(len(items) for items in all_line_items.values())
    if total_items == 0:
        return None

    period_data = {
        "type": "annual",
        "fiscal_year": 0,
        "end_date": "",
        "source": "external-json",
        "statements": {
            "IS": {"unit": "actual", "line_items": all_line_items.get("IS", [])},
            "BS": {"unit": "actual", "line_items": all_line_items.get("BS", [])},
            "CFS": {"unit": "actual", "line_items": all_line_items.get("CFS", [])},
        },
    }

    return {
        "status": "SUCCESS",
        "company": {"name": ticker.upper(), "ticker": ticker.upper(), "fiscal_year_end": ""},
        "periods": [period_data],
        "warnings": ["Data extracted from external JSON source"],
        "metadata": {
            "extraction_method": "external-json",
            "periods_requested": periods,
            "periods_extracted": 1,
        },
    }

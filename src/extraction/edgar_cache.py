"""EDGAR filing index cache — local cache to reduce SEC API calls.

Caches company_tickers.json (ticker→CIK) and company submissions (filing history)
in local JSON files with TTL-based expiration.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from src.config import DATA_DIR

logger = logging.getLogger(__name__)

CACHE_DIR = DATA_DIR / "cache"
TICKERS_CACHE = CACHE_DIR / "company_tickers.json"
TICKERS_TTL = 86400 * 7  # 7 days

SUBMISSIONS_CACHE_TTL = 86400  # 24 hours


def _ensure_cache_dir() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _is_fresh(path: Path, ttl: int) -> bool:
    if not path.exists():
        return False
    age = time.time() - path.stat().st_mtime
    return age < ttl


def get_cached_tickers() -> dict[str, dict[str, Any]] | None:
    """Get cached SEC company_tickers.json mapping.

    Returns dict of index -> {cik_str, ticker, title} or None if cache is stale/missing.
    """
    _ensure_cache_dir()
    if not _is_fresh(TICKERS_CACHE, TICKERS_TTL):
        return None
    try:
        return json.loads(TICKERS_CACHE.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def cache_tickers(data: dict[str, dict[str, Any]]) -> None:
    """Cache the company_tickers.json mapping."""
    _ensure_cache_dir()
    TICKERS_CACHE.write_text(json.dumps(data))
    logger.info("Cached company_tickers.json (%d entries)", len(data))


def get_cached_submissions(cik: str) -> dict[str, Any] | None:
    """Get cached SEC submissions for a CIK.

    Returns submissions dict or None if cache is stale/missing.
    """
    _ensure_cache_dir()
    path = CACHE_DIR / f"submissions_{cik}.json"
    if not _is_fresh(path, SUBMISSIONS_CACHE_TTL):
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def cache_submissions(cik: str, data: dict[str, Any]) -> None:
    """Cache the submissions data for a CIK."""
    _ensure_cache_dir()
    path = CACHE_DIR / f"submissions_{cik}.json"
    path.write_text(json.dumps(data))
    logger.info("Cached submissions for CIK %s", cik)


def get_cached_facts(cik: str) -> dict[str, Any] | None:
    """Get cached company facts for a CIK.

    Returns facts dict or None if cache is stale/missing.
    """
    _ensure_cache_dir()
    path = CACHE_DIR / f"facts_{cik}.json"
    if not _is_fresh(path, SUBMISSIONS_CACHE_TTL):
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def cache_facts(cik: str, data: dict[str, Any]) -> None:
    """Cache the company facts data for a CIK."""
    _ensure_cache_dir()
    path = CACHE_DIR / f"facts_{cik}.json"
    path.write_text(json.dumps(data))
    logger.info("Cached company facts for CIK %s", cik)

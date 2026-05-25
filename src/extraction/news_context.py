"""Web search context — fetch recent 8-K filings and news for contextual analysis.

Adds qualitative context to financial reports by searching for recent
company news, material events (8-K), and market commentary.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def search_company_news(ticker: str, max_results: int = 5) -> list[dict[str, Any]]:
    """Search for recent company news using Tavily or Exa.

    Args:
        ticker: Stock ticker symbol.
        max_results: Maximum number of news items to return.

    Returns:
        List of dicts with title, url, snippet, source.
    """
    results: list[dict[str, Any]] = []

    try:
        from tavily import TavilyClient

        client = TavilyClient()
        response = client.search(
            query=f"{ticker} recent news 8-K filing material events",
            search_depth="basic",
            max_results=max_results,
            topic="news",
            days=30,
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
    except ImportError:
        logger.debug("Tavily client not available for news search")
    except Exception as e:
        logger.debug("News search failed for %s via Tavily: %s", ticker, e)

    if not results:
        try:
            from exa_py import Exa

            client = Exa()
            response = client.search_and_contents(
                f"{ticker} recent news filing",
                type="auto",
                num_results=max_results,
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
        except ImportError:
            logger.debug("Exa SDK not available for news search")
        except Exception as e:
            logger.debug("News search failed for %s via Exa: %s", ticker, e)

    return results


def search_filing_events(ticker: str, cik: str = "") -> list[dict[str, Any]]:
    """Search for recent 8-K filings and material events.

    Tries SEC EDGAR full-text search for recent filings first,
    then falls back to Tavily/Exa general search.

    Returns list of event dicts with title, url, snippet.
    """
    results: list[dict[str, Any]] = []

    if cik:
        try:
            import requests

            url = f"https://efts.sec.gov/LATEST/search-index?q={ticker}&dateRange=custom&startdt=2025-01-01"
            resp = requests.get(
                url,
                headers={"User-Agent": "reading-cfs-is-bs/0.1.0"},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                hits = data.get("hits", {}).get("hits", [])
                for hit in hits[:5]:
                    src = hit.get("_source", {})
                    results.append(
                        {
                            "title": src.get("display_names", [ticker])[0],
                            "url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}",
                            "snippet": src.get("file_num", ""),
                            "source": "sec-edgar",
                        }
                    )
        except Exception:
            pass

    if not results:
        news = search_company_news(ticker)
        results.extend(news)

    return results


def build_news_context(ticker: str, cik: str = "") -> list[str]:
    """Build a list of recent news/event context strings for reporting.

    Args:
        ticker: Stock ticker symbol.
        cik: Optional CIK for SEC-specific search.

    Returns:
        List of human-readable news context strings.
    """
    events = search_filing_events(ticker, cik)
    if not events:
        return []

    context: list[str] = []
    for event in events[:3]:
        title = event.get("title", "")
        snippet = event.get("snippet", "")
        if title and snippet:
            context.append(f"{title}: {snippet[:200]}")
        elif title:
            context.append(title)

    return context

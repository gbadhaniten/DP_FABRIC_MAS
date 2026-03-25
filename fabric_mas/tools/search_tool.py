"""
search_tool.py — Autotrain / Live-Search Tool
===============================================
Fetches the latest REST API specs, CLI docs, and best practices for a
given Fabric item so that agents always work with up-to-date knowledge.

Supports two backends:
    1. Tavily  — structured AI-search (preferred)
    2. Bing    — fallback via Bing Web Search API
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------
class SearchResult:
    """Normalised search result from any backend."""

    def __init__(
        self,
        title: str,
        url: str,
        snippet: str,
        source: str = "unknown",
        score: float = 0.0,
        raw: Optional[Dict[str, Any]] = None,
    ):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.source = source
        self.score = score
        self.raw = raw or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "score": self.score,
        }

    def __repr__(self) -> str:
        return f"<SearchResult '{self.title[:40]}…' ({self.source})>"


# ---------------------------------------------------------------------------
# Search Tool
# ---------------------------------------------------------------------------
class SearchTool:
    """
    Autotrain search engine.

    Usage::

        st = SearchTool()
        results = st.search("Microsoft Fabric Lakehouse REST API create 2025")
    """

    def __init__(
        self,
        tavily_api_key: Optional[str] = None,
        bing_api_key: Optional[str] = None,
        max_results: int = 5,
    ):
        self.tavily_api_key = tavily_api_key or os.getenv("TAVILY_API_KEY")
        self.bing_api_key = bing_api_key or os.getenv("BING_SEARCH_API_KEY")
        self.max_results = max_results

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------
    def search(
        self,
        query: str,
        *,
        max_results: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run autotrain search — tries Tavily first, then Bing fallback.
        Returns a dict with ``results`` list and ``metadata``.
        """
        n = max_results or self.max_results
        results: List[SearchResult] = []
        backend_used = "none"

        # --- Tavily -------------------------------------------------
        if self.tavily_api_key:
            try:
                results = self._tavily_search(query, n)
                backend_used = "tavily"
            except Exception as exc:
                logger.warning("Tavily search failed: %s", exc)

        # --- Bing fallback ------------------------------------------
        if not results and self.bing_api_key:
            try:
                results = self._bing_search(query, n)
                backend_used = "bing"
            except Exception as exc:
                logger.warning("Bing search failed: %s", exc)

        if not results:
            logger.info("Autotrain: no results for query — using cached knowledge")
            return {
                "results": [],
                "metadata": {"query": query, "backend": "none", "count": 0},
            }

        return {
            "results": [r.to_dict() for r in results],
            "metadata": {
                "query": query,
                "backend": backend_used,
                "count": len(results),
            },
        }

    def search_fabric_api(
        self, item_type: str, operation: str
    ) -> Dict[str, Any]:
        """
        Convenience method: search specifically for a Fabric item's API
        spec for a given CRUD operation.
        """
        query = (
            f"Microsoft Fabric REST API {item_type} {operation} "
            f"endpoint parameters latest 2025"
        )
        return self.search(query)

    def search_fabric_cli(
        self, item_type: str, operation: str
    ) -> Dict[str, Any]:
        """Search for `fab` CLI usage for this item + operation."""
        query = (
            f"ms-fabric-cli fab {item_type} {operation} "
            f"command options examples"
        )
        return self.search(query)

    # ------------------------------------------------------------------
    # Tavily backend
    # ------------------------------------------------------------------
    def _tavily_search(self, query: str, max_results: int) -> List[SearchResult]:
        """Call the Tavily Search API."""
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": self.tavily_api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": max_results,
            "include_domains": [
                "learn.microsoft.com",
                "docs.microsoft.com",
                "github.com/microsoft",
                "fabric.microsoft.com",
            ],
        }
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        results: List[SearchResult] = []
        for item in data.get("results", []):
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""),
                    source="tavily",
                    score=item.get("score", 0.0),
                    raw=item,
                )
            )
        logger.info("Tavily returned %d results for: %s", len(results), query)
        return results

    # ------------------------------------------------------------------
    # Bing backend
    # ------------------------------------------------------------------
    def _bing_search(self, query: str, max_results: int) -> List[SearchResult]:
        """Call the Bing Web Search v7 API."""
        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {"Ocp-Apim-Subscription-Key": self.bing_api_key}
        params = {"q": query, "count": max_results, "mkt": "en-US"}
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        results: List[SearchResult] = []
        for page in data.get("webPages", {}).get("value", []):
            results.append(
                SearchResult(
                    title=page.get("name", ""),
                    url=page.get("url", ""),
                    snippet=page.get("snippet", ""),
                    source="bing",
                    raw=page,
                )
            )
        logger.info("Bing returned %d results for: %s", len(results), query)
        return results

"""GDELT Doc 2.0 API client. No auth required."""
from __future__ import annotations
import logging
from typing import Any, Dict, List

import requests

logger = logging.getLogger(__name__)

GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"


def fetch_articles(
    query: str,
    timeout_s: float = 4.0,
    max_records: int = 25,
) -> List[Dict[str, Any]]:
    """
    Fetch recent articles from GDELT Doc 2.0 matching query.
    Returns list of article dicts. Raises requests.RequestException on failure.
    """
    params = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": max_records,
        "timespan": "14d",
        "sort": "hybridrel",
    }
    resp = requests.get(GDELT_URL, params=params, timeout=timeout_s)
    resp.raise_for_status()
    data = resp.json()
    return data.get("articles", []) or []

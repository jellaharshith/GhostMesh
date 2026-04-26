"""GDELT Doc 2.0 API client. No auth required."""
from __future__ import annotations
import logging
import time
from typing import Any, Dict, List

import requests

logger = logging.getLogger(__name__)

GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
_RETRIES = 2
_RETRY_DELAY_S = 1.5


def fetch_articles(
    query: str,
    timeout_s: float = 8.0,
    max_records: int = 25,
) -> List[Dict[str, Any]]:
    """
    Fetch recent articles from GDELT Doc 2.0 matching query.
    Retries up to _RETRIES times on timeout/connection error.
    Returns list of article dicts. Raises requests.RequestException on final failure.
    """
    params = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": max_records,
        "timespan": "14d",
        "sort": "hybridrel",
    }
    last_exc: Exception = RuntimeError("no attempts made")
    for attempt in range(1, _RETRIES + 1):
        try:
            resp = requests.get(GDELT_URL, params=params, timeout=timeout_s)
            resp.raise_for_status()
            data = resp.json()
            return data.get("articles", []) or []
        except requests.exceptions.Timeout as exc:
            last_exc = exc
            logger.debug("GDELT attempt %d/%d timed out", attempt, _RETRIES)
            if attempt < _RETRIES:
                time.sleep(_RETRY_DELAY_S)
        except requests.RequestException as exc:
            raise exc
    raise last_exc

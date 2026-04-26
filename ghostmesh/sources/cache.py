"""Three-layer cache: live API → disk cache → committed seed fallback. Never raises."""
from __future__ import annotations
import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any, Callable, List, Optional

logger = logging.getLogger(__name__)

_BASE = Path(__file__).parents[1] / "data"
_CACHE_DIR = _BASE / "cache"
_SEED_DIR  = _BASE / "seed"

_TTL_S = 24 * 3600  # 24 hours


def _cache_path(namespace: str, key: str) -> Path:
    sha = hashlib.sha1(key.encode()).hexdigest()[:12]
    return _CACHE_DIR / namespace / f"{sha}.json"


def _seed_path(namespace: str) -> Path:
    return _SEED_DIR / f"{namespace}_sample.json"


def _write(path: Path, data: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"ts": time.time(), "data": data}, indent=2), encoding="utf-8")


def _read_cache(path: Path) -> Optional[List[dict]]:
    if not path.exists():
        return None
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        if time.time() - obj.get("ts", 0) > _TTL_S:
            return None  # stale
        return obj.get("data", [])
    except Exception:
        return None


def _read_seed(namespace: str) -> List[dict]:
    path = _seed_path(namespace)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def with_cache(
    namespace: str,
    key: str,
    fetcher: Callable[[], List[dict]],
    ttl_h: float = 24.0,
) -> List[dict]:
    """
    Layer 1: call fetcher (live API). On success, persist to disk and return.
    Layer 2: disk cache (TTL-based).
    Layer 3: committed seed fallback.
    Never raises.
    """
    global _TTL_S
    _TTL_S = int(ttl_h * 3600)

    path = _cache_path(namespace, key)

    # Layer 1 — live
    try:
        data = fetcher()
        if data:
            try:
                _write(path, data)
            except Exception as exc:
                logger.debug("cache write failed: %s", exc)
            return data
    except Exception as exc:
        logger.debug("%s live fetch failed: %s", namespace, exc)

    # Layer 2 — disk cache
    cached = _read_cache(path)
    if cached is not None:
        logger.debug("%s using disk cache", namespace)
        return cached

    # Layer 3 — seed sample
    logger.debug("%s using seed fallback", namespace)
    return _read_seed(namespace)

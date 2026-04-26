"""OpenTopography (SRTM DEM) adapter.

Returns a compact terrain summary for a bbox or a named region:

    {
        "min_elev_m":    int,
        "max_elev_m":    int,
        "mean_elev_m":   int,
        "terrain_class": "mountain" | "hill" | "lowland" | "coastal" | "urban" | "mixed"
    }

Sourcing strategy:

1. If ``OPENTOPO_API_KEY`` is set, query the OpenTopography Global DEM API
   (SRTM 30m) and compute min/mean/max from the returned grid.  Result is
   cached on disk via ``with_cache(...)``.
2. Otherwise (or on any error) fall back to ``data/seed/elevation_seed.json``,
   which ships precomputed summaries for every region in
   ``overpass_adapter._REGION_BBOX``.

Never raises into the request path.
"""
from __future__ import annotations
import io
import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional

import requests

from .cache import with_cache
from .overpass_adapter import bbox_for_region

logger = logging.getLogger(__name__)

_BASE = Path(__file__).parents[1] / "data"
_SEED = _BASE / "seed" / "elevation_seed.json"

_OPENTOPO_URL = "https://portal.opentopography.org/API/globaldem"
_DEM_TYPE = "SRTMGL3"  # 90m SRTM v3, sufficient for theater-scale summary

_TERRAIN_CLASS_RULES = (
    # (min_max_elev_m, mean_elev_m, class)  — first matching rule wins
    # Coastal: very low mean elevation regardless of max
    (None, 60, "coastal"),
    (None, 200, "lowland"),
    (None, 800, "hill"),
    (3500, None, "mountain"),
)


def _classify(min_e: float, mean_e: float, max_e: float) -> str:
    if max_e >= 3500 and mean_e >= 800:
        return "mountain"
    if mean_e < 60:
        return "coastal"
    if mean_e < 200:
        return "lowland"
    if mean_e < 800:
        return "hill"
    if max_e - min_e > 3000:
        return "mixed"
    return "hill"


_seed_cache: Optional[Dict[str, Dict]] = None


def _load_seed() -> Dict[str, Dict]:
    global _seed_cache
    if _seed_cache is not None:
        return _seed_cache
    try:
        data = json.loads(_SEED.read_text(encoding="utf-8"))
        # Drop documentation key
        data.pop("_doc", None)
        _seed_cache = data
    except Exception as exc:
        logger.debug("elevation seed load failed: %s", exc)
        _seed_cache = {}
    return _seed_cache


def _seed_lookup(region: Optional[str]) -> Dict:
    if not region:
        return {"min_elev_m": 0, "max_elev_m": 0, "mean_elev_m": 0, "terrain_class": "unknown"}
    text = region.lower().strip()
    seeds = _load_seed()
    if text in seeds:
        return dict(seeds[text])
    # Substring scan (longest match wins)
    best_key = None
    best_len = 0
    for key in seeds.keys():
        if key in text and len(key) > best_len:
            best_key = key
            best_len = len(key)
    if best_key:
        return dict(seeds[best_key])
    # Final fallback: global summary
    return dict(seeds.get("global", {
        "min_elev_m": 0, "max_elev_m": 0, "mean_elev_m": 0, "terrain_class": "unknown",
    }))


def _opentopo_summary(bbox: str, api_key: str, timeout_s: float = 8.0) -> Optional[Dict]:
    """Query OpenTopography and reduce the returned DEM to a summary.

    The Global DEM endpoint returns a GeoTIFF; decoding requires rasterio /
    PIL.  We try rasterio first (handles GeoTIFF correctly), then PIL as a
    fallback.  If neither is available we bail and let the caller fall back
    to the seed.
    """
    south, west, north, east = (float(x) for x in bbox.split(","))
    params = {
        "demtype":      _DEM_TYPE,
        "south":        south,
        "west":         west,
        "north":        north,
        "east":         east,
        "outputFormat": "GTiff",
        "API_Key":      api_key,
    }
    resp = requests.get(_OPENTOPO_URL, params=params, timeout=timeout_s)
    resp.raise_for_status()
    content = resp.content
    if not content:
        return None

    # Try rasterio (preferred — proper GeoTIFF handling)
    try:
        import rasterio  # type: ignore
        with rasterio.io.MemoryFile(content) as mem:
            with mem.open() as ds:
                arr = ds.read(1)
                # Mask nodata
                nodata = ds.nodata
                if nodata is not None:
                    import numpy as np  # type: ignore
                    valid = arr[arr != nodata]
                else:
                    import numpy as np  # type: ignore
                    valid = arr.flatten()
                if valid.size == 0:
                    return None
                min_e = float(valid.min())
                max_e = float(valid.max())
                mean_e = float(valid.mean())
    except Exception:
        # Fallback: PIL (works for plain TIFF, less robust for GeoTIFF)
        try:
            from PIL import Image  # type: ignore
            import numpy as np  # type: ignore
            img = Image.open(io.BytesIO(content))
            arr = np.array(img)
            min_e = float(arr.min())
            max_e = float(arr.max())
            mean_e = float(arr.mean())
        except Exception as exc:
            logger.debug("opentopo decode failed: %s", exc)
            return None

    return {
        "min_elev_m":    int(round(min_e)),
        "max_elev_m":    int(round(max_e)),
        "mean_elev_m":   int(round(mean_e)),
        "terrain_class": _classify(min_e, mean_e, max_e),
    }


def summarize(
    region: Optional[str] = None,
    bbox: Optional[str] = None,
    timeout_s: float = 8.0,
) -> Dict:
    """Return a terrain summary for a region or bbox.

    Resolution order:
        1. If ``OPENTOPO_API_KEY`` env var is set and a bbox is available
           (either passed in or resolved from ``region``), query the live API
           through ``with_cache(...)`` so subsequent calls reuse the result.
        2. Otherwise (or on any failure), look up the bundled seed.

    Never raises.
    """
    api_key = os.environ.get("OPENTOPO_API_KEY", "").strip()
    eff_bbox = bbox or (bbox_for_region(region or "") if region else None)

    if api_key and eff_bbox:
        cache_key = f"{eff_bbox}:{_DEM_TYPE}"

        def _live() -> list:
            res = _opentopo_summary(eff_bbox, api_key, timeout_s=timeout_s)
            if res is None:
                return []
            return [res]

        cached = with_cache("opentopography", cache_key, fetcher=_live, ttl_h=24 * 7)
        if cached:
            return cached[0]

    # Seed fallback
    return _seed_lookup(region)


# Back-compat alias for callers that follow the existing adapter naming
fetch = summarize

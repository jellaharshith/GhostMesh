"""Global Terrorism Database (GTD) adapter → normalized Event list.

GTD covers ~200K incidents from 1970–2020 and is ideal for *historical
baseline* in scenario seeding ("what does the last decade look like in this
theater?").  We never raise into the request path.

Sourcing strategy (in priority order):

1. Optional: HuggingFace mirror dataset cached as parquet under
   ``data/cache/gtd/full.parquet``.  Only attempted when ``GTD_USE_HF=1`` is
   set, and only on first call per process.  Fails silently.
2. Bundled CSV: ``data/seed/gtd_sample.csv`` ships ~2K stratified rows
   (region × year balanced) so the system works fully offline.

Filters supported:
    - ``region`` free-text (matched via overpass_adapter.bbox_for_region)
    - explicit ``country`` substring
    - ``start_year`` / ``end_year``
    - ``limit``
"""
from __future__ import annotations
import csv
import logging
import os
import time
from pathlib import Path
from typing import Iterable, List, Optional

from .schemas import Event, make_event_id
from .infra import tag as infra_tag

logger = logging.getLogger(__name__)

_BASE = Path(__file__).parents[1] / "data"
_SEED_CSV = _BASE / "seed" / "gtd_sample.csv"
_CACHE_DIR = _BASE / "cache" / "gtd"
_HF_PARQUET = _CACHE_DIR / "full.parquet"

# Public mirror of GTD.  We never block on this — if it fails we fall back to
# the bundled sample.  The ``GTD_USE_HF=1`` flag gates this entirely.
_HF_REPO = "ENG-Lab/global-terrorism-database"
_HF_FILE = "data/train-00000-of-00001.parquet"

# Country → free-text region keyword used to map regions onto rows in our
# bundled sample.  Mirrors the keys in overpass_adapter._REGION_BBOX so
# callers can pass the same region strings.
_REGION_COUNTRIES: dict = {
    "europe":              {"United Kingdom", "France", "Germany", "Spain", "Italy", "Belgium",
                            "Ukraine", "Russia", "Poland", "Romania", "Belarus"},
    "western europe":      {"United Kingdom", "France", "Germany", "Spain", "Italy", "Belgium"},
    "eastern europe":      {"Ukraine", "Russia", "Poland", "Romania", "Belarus"},
    "ukraine":             {"Ukraine"},
    "poland":              {"Poland"},
    "russia":              {"Russia"},
    "germany":             {"Germany"},
    "nato eastern flank":  {"Poland", "Romania", "Ukraine"},
    "baltic":              {"Poland", "Belarus"},

    "middle east":         {"Iraq", "Syria", "Israel", "Lebanon", "Egypt", "Yemen", "Libya", "Iran"},
    "iran":                {"Iran"},
    "israel":              {"Israel", "Lebanon"},
    "gulf":                {"Iran", "Iraq"},
    "persian gulf":        {"Iran", "Iraq"},

    "africa":              {"Nigeria", "Mali", "Somalia", "Kenya", "South Africa", "Sudan", "Ethiopia"},
    "sahel":               {"Mali", "Sudan", "Nigeria"},

    "south asia":          {"Pakistan", "India", "Afghanistan", "Bangladesh", "Sri Lanka"},
    "southeast asia":      {"Philippines", "Indonesia", "Thailand", "Myanmar"},
    "indo-pacific":        {"Philippines", "Indonesia", "Thailand", "Myanmar",
                            "Japan", "South Korea", "China", "Taiwan"},
    "east asia":           {"China", "Japan", "South Korea", "Taiwan"},
    "taiwan":              {"Taiwan"},
    "taiwan strait":       {"Taiwan", "China"},
    "south china sea":     {"China", "Philippines", "Indonesia"},
    "korea":               {"South Korea"},
    "japan":               {"Japan"},

    "us":                  {"United States"},
    "usa":                 {"United States"},
    "united states":       {"United States"},
    "north america":       {"United States", "Canada", "Mexico"},
    "east coast":          {"United States"},
    "northeast us":        {"United States"},
    "mid-atlantic":        {"United States"},
    "texas":               {"United States"},
    "gulf coast":          {"United States"},
    "dc":                  {"United States"},
    "washington dc":       {"United States"},

    "south america":       {"Colombia", "Peru", "Argentina", "Brazil", "Chile"},
    "central america":     {"Guatemala", "El Salvador", "Honduras", "Cuba"},
}

# Module-level cache of parsed rows (lightweight: strings + ints)
_ROWS: Optional[List[dict]] = None
_HF_ATTEMPTED = False


def _try_hf_pull() -> Optional[List[dict]]:
    """Attempt one-shot pull of the HF mirror parquet → list[dict].

    Returns None on any failure (missing pyarrow, missing huggingface_hub,
    network error, etc.).  Honors a 24h staleness check on the cached file.
    """
    global _HF_ATTEMPTED
    if _HF_ATTEMPTED:
        return None
    _HF_ATTEMPTED = True
    if os.environ.get("GTD_USE_HF") != "1":
        return None
    try:
        # Imports gated to keep the soft dependency truly soft
        from huggingface_hub import hf_hub_download  # type: ignore
        import pyarrow.parquet as pq  # type: ignore
    except Exception as exc:
        logger.debug("GTD HF deps missing: %s", exc)
        return None

    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    fresh = _HF_PARQUET.exists() and (time.time() - _HF_PARQUET.stat().st_mtime) < 7 * 24 * 3600
    try:
        if not fresh:
            local = hf_hub_download(
                repo_id=_HF_REPO,
                filename=_HF_FILE,
                repo_type="dataset",
                local_dir=str(_CACHE_DIR),
                local_dir_use_symlinks=False,
            )
            Path(local).rename(_HF_PARQUET)
        table = pq.read_table(str(_HF_PARQUET))
        rows = table.to_pylist()
        # Normalize column names to match our CSV schema
        norm: List[dict] = []
        for r in rows:
            norm.append({
                "eventid": str(r.get("eventid") or ""),
                "iyear": r.get("iyear"),
                "imonth": r.get("imonth"),
                "iday": r.get("iday"),
                "country_txt": r.get("country_txt") or "",
                "region_txt": r.get("region_txt") or "",
                "city": r.get("city") or "",
                "attacktype1_txt": r.get("attacktype1_txt") or "",
                "targtype1_txt": r.get("targtype1_txt") or "",
                "gname": r.get("gname") or "",
                "weaptype1_txt": r.get("weaptype1_txt") or "",
                "nkill": r.get("nkill") or 0,
                "nwound": r.get("nwound") or 0,
                "summary": r.get("summary") or "",
            })
        logger.info("GTD: loaded %d rows from HF mirror", len(norm))
        return norm
    except Exception as exc:
        logger.debug("GTD HF pull failed: %s", exc)
        return None


def _load_seed() -> List[dict]:
    if not _SEED_CSV.exists():
        logger.debug("GTD seed missing: %s", _SEED_CSV)
        return []
    rows: List[dict] = []
    try:
        with _SEED_CSV.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Coerce numeric columns to int when possible
                for k in ("iyear", "imonth", "iday", "nkill", "nwound"):
                    try:
                        row[k] = int(row[k]) if row.get(k) not in (None, "") else 0
                    except Exception:
                        row[k] = 0
                rows.append(row)
    except Exception as exc:
        logger.debug("GTD seed parse failed: %s", exc)
        return []
    return rows


def _all_rows() -> List[dict]:
    global _ROWS
    if _ROWS is not None:
        return _ROWS
    rows = _try_hf_pull()
    if not rows:
        rows = _load_seed()
    _ROWS = rows
    return _ROWS


def _resolve_countries(region: Optional[str]) -> Optional[set]:
    """Map a free-text region to a set of country names; None means no filter."""
    if not region:
        return None
    text = region.lower().strip()
    if text in _REGION_COUNTRIES:
        return _REGION_COUNTRIES[text]
    # Substring scan (longest match wins)
    best_key = None
    best_len = 0
    for key in _REGION_COUNTRIES.keys():
        if key in text and len(key) > best_len:
            best_key = key
            best_len = len(key)
    if best_key:
        return _REGION_COUNTRIES[best_key]
    # Treat the whole region string as a literal country name fallback
    return {region.title()}


def _row_to_event(row: dict) -> Event:
    year = int(row.get("iyear") or 0)
    month = int(row.get("imonth") or 0) or 1
    day = int(row.get("iday") or 0) or 1
    timestamp = f"{year:04d}-{month:02d}-{day:02d}T00:00:00Z" if year else ""
    country = (row.get("country_txt") or "").strip()
    city = (row.get("city") or "").strip()
    location = ", ".join(p for p in [city, country] if p) or "Unknown"
    attack = (row.get("attacktype1_txt") or "").strip()
    target = (row.get("targtype1_txt") or "").strip()
    group = (row.get("gname") or "").strip()
    summary = (row.get("summary") or "").strip()
    nkill = int(row.get("nkill") or 0)
    nwound = int(row.get("nwound") or 0)
    if not summary:
        summary = (
            f"{attack or 'Attack'} on {target or 'target'} in {location}"
            f" — {nkill} killed, {nwound} wounded."
            + (f" Attribution: {group}." if group and group.lower() != "unknown" else "")
        )

    actors = [group] if group and group.lower() != "unknown" else ["Unattributed"]
    et = "armed-conflict" if "armed" in attack.lower() or "bombing" in attack.lower() else "other"
    if "assass" in attack.lower():
        et = "armed-conflict"
    if "kidnap" in attack.lower():
        et = "armed-conflict"
    if "infra" in (attack + target).lower() or "utilit" in target.lower():
        et = "infrastructure-incident"

    # Roughly normalize tension as 0..1 from casualty band
    tension = min(1.0, (nkill * 0.05 + nwound * 0.01))
    return Event(
        event_id=make_event_id("gtd", str(row.get("eventid") or summary[:40])),
        source="gtd",
        timestamp=timestamp,
        location=location,
        actors=actors,
        event_type=et,
        summary=summary[:280],
        tension_weight=round(tension, 3),
        infrastructure_relevance=infra_tag(f"{attack} {target} {summary}"),
    )


def _filter(rows: Iterable[dict],
            countries: Optional[set],
            start_year: Optional[int],
            end_year: Optional[int]) -> List[dict]:
    out: List[dict] = []
    for r in rows:
        if countries is not None:
            if r.get("country_txt") not in countries:
                continue
        if start_year is not None:
            try:
                if int(r.get("iyear") or 0) < start_year:
                    continue
            except Exception:
                continue
        if end_year is not None:
            try:
                if int(r.get("iyear") or 0) > end_year:
                    continue
            except Exception:
                continue
        out.append(r)
    return out


def fetch(
    region: Optional[str] = None,
    country: Optional[str] = None,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    limit: int = 50,
) -> List[Event]:
    """Return the most recent (year-desc) ``limit`` GTD events matching filters.

    Cache-free at this layer because rows are loaded once at module level
    (HF parquet → bundled CSV).  Never raises.
    """
    rows = _all_rows()
    if not rows:
        return []

    countries: Optional[set] = None
    if country:
        countries = {country}
    elif region:
        countries = _resolve_countries(region)

    filtered = _filter(rows, countries, start_year, end_year)
    # Recency-first
    filtered.sort(key=lambda r: (int(r.get("iyear") or 0),
                                 int(r.get("imonth") or 0),
                                 int(r.get("iday") or 0)),
                  reverse=True)
    out: List[Event] = []
    for r in filtered[: limit * 2]:
        try:
            out.append(_row_to_event(r))
        except Exception as exc:
            logger.debug("gtd row parse error: %s", exc)
        if len(out) >= limit:
            break
    return out


def recent_decade(region: Optional[str], limit: int = 25) -> List[Event]:
    """Convenience helper: events from the most recent decade in our data."""
    rows = _all_rows()
    if not rows:
        return []
    max_year = 2020
    try:
        max_year = max(int(r.get("iyear") or 0) for r in rows)
    except Exception:
        pass
    start_year = max(1970, max_year - 10)
    return fetch(region=region, start_year=start_year, end_year=max_year, limit=limit)

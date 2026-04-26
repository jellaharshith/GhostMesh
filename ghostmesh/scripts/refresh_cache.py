"""
Warm live-source caches for offline demo use.

Run once with network access before a network-offline demo:
    python scripts/refresh_cache.py

Writes to:
    data/cache/gdelt/        (GDELT 2.0 doc API)
    data/cache/liveuamap/    (LiveUAMap conflict markers)
    data/cache/ucdp/         (UCDP GED armed conflict)
    data/cache/opentopo/     (OpenTopography SRTM summaries, if OPENTOPO_API_KEY set)

GTD is bundled (data/seed/gtd_sample.csv) and does not require warming.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

DEMO_QUERIES = [
    "port cyber attack infrastructure",
    "power grid substation hack",
    "water utility SCADA intrusion",
    "pipeline OT network breach",
    "telecom BGP routing attack",
    "critical infrastructure china russia iran",
]

DEMO_REGIONS = [
    "Ukraine",
    "Taiwan Strait",
    "Iran",
    "Texas",
    "Korean Peninsula",
    "Eastern Europe",
]


def main() -> None:
    from sources import gdelt_adapter, liveuamap_adapter, ucdp_adapter

    print("=== Refreshing GDELT cache ===")
    for q in DEMO_QUERIES:
        try:
            events = gdelt_adapter.fetch(q, timeout_s=8.0)
            print(f"  [{len(events):3d} events] {q}")
        except Exception as exc:
            print(f"  [skip] {q}: {exc}")

    print("\n=== Refreshing LiveUAMap cache ===")
    for region in DEMO_REGIONS:
        try:
            events = liveuamap_adapter.fetch(region=region)
            print(f"  [{len(events):3d} events] {region}")
        except Exception as exc:
            print(f"  [skip] {region}: {exc}")

    print("\n=== Refreshing UCDP cache ===")
    for region in DEMO_REGIONS:
        try:
            events = ucdp_adapter.fetch(region)
            print(f"  [{len(events):3d} events] {region}")
        except Exception as exc:
            print(f"  [skip] {region}: {exc}")

    # Optional: only meaningful if OPENTOPO_API_KEY is set; otherwise the
    # adapter just reads the bundled elevation_seed.json on demand.
    print("\n=== Refreshing OpenTopography cache (optional) ===")
    try:
        from sources import opentopography_adapter
        for region in DEMO_REGIONS:
            try:
                summary = opentopography_adapter.summarize(region=region)
                tag = (summary or {}).get("terrain_class", "—")
                print(f"  [{tag:>8}] {region}")
            except Exception as exc:
                print(f"  [skip] {region}: {exc}")
    except Exception as exc:
        print(f"  [skipped opentopography_adapter: {exc}]")

    print("\nCache refresh complete. data/cache/ is ready for offline use.")


if __name__ == "__main__":
    main()

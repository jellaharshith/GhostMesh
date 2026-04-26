"""
Warm GDELT + ACLED caches for offline demo use.

Run once with network access before a network-offline demo:
    python scripts/refresh_cache.py

Writes to data/cache/gdelt/ and data/cache/acled/.
"""
from __future__ import annotations
import sys
from pathlib import Path

# Add ghostmesh root to path
sys.path.insert(0, str(Path(__file__).parents[1]))

DEMO_QUERIES = [
    "port cyber attack infrastructure",
    "power grid substation hack",
    "water utility SCADA intrusion",
    "pipeline OT network breach",
    "telecom BGP routing attack",
    "critical infrastructure china russia iran",
]


def main() -> None:
    from sources import gdelt_adapter, acled_adapter

    print("=== Refreshing GDELT cache ===")
    for q in DEMO_QUERIES:
        events = gdelt_adapter.fetch(q, timeout_s=8.0)
        print(f"  [{len(events):3d} events] {q}")

    print("\n=== Refreshing ACLED cache ===")
    for q in DEMO_QUERIES:
        events = acled_adapter.fetch(q, timeout_s=8.0)
        print(f"  [{len(events):3d} events] {q}")

    print("\nCache refresh complete. data/cache/ is ready for offline use.")


if __name__ == "__main__":
    main()

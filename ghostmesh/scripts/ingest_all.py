"""
Rebuild Chroma vector store from full corpus (including jcs/ and csis/ subfolders).

Usage:
    python scripts/ingest_all.py            # incremental
    python scripts/ingest_all.py --rebuild  # full rebuild
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))


def main() -> None:
    from retrieval.ingest import main as ingest_main
    rebuild = "--rebuild" in sys.argv
    print(f"Ingesting corpus (rebuild={rebuild}) ...")
    ingest_main(rebuild=rebuild)


if __name__ == "__main__":
    main()

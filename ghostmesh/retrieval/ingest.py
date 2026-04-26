"""Ingest corpus into Chroma vector store. Idempotent.

Usage:
    python -m ghostmesh.retrieval.ingest [--rebuild]
"""
from __future__ import annotations
import re
import sys
from pathlib import Path
from typing import Optional

CORPUS_DIR = Path(__file__).parent / "corpus"
CHROMA_DIR = Path(__file__).parents[1] / "data" / "chroma"
COLLECTION_NAME = "ghostmesh-doctrine"


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("---", 3)
    if end == -1:
        return {}, text
    fm_block = text[3:end].strip()
    body = text[end + 3:].strip()
    meta: dict = {}
    for line in fm_block.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            k = k.strip(); v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                meta[k] = [x.strip() for x in v[1:-1].split(",")]
            else:
                meta[k] = v
    return meta, body


def _chunk(text: str, target_chars: int = 800) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\n+", text) if p.strip()]
    chunks, current = [], ""
    for para in paragraphs:
        if current and len(current) + len(para) + 2 > target_chars:
            chunks.append(current)
            current = para
        else:
            current = (current + "\n\n" + para).strip() if current else para
    if current:
        chunks.append(current)
    return chunks or [text[:target_chars]]


def main(rebuild: bool = False) -> None:
    try:
        import chromadb
        from chromadb.utils import embedding_functions
    except ImportError:
        print("chromadb not installed — skipping ingest. TF-IDF fallback will be used.")
        return

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    if rebuild:
        existing = [c.name for c in client.list_collections()]
        if COLLECTION_NAME in existing:
            client.delete_collection(COLLECTION_NAME)
            print(f"Deleted existing collection '{COLLECTION_NAME}'")

    coll = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_functions.DefaultEmbeddingFunction(),
    )

    try:
        existing_ids = set(coll.get()["ids"])
    except Exception:
        existing_ids = set()

    md_files = sorted(CORPUS_DIR.rglob("*.md"))
    if not md_files:
        print(f"No markdown files found in {CORPUS_DIR}")
        return

    new_ids, new_docs, new_metas = [], [], []
    for md_path in md_files:
        meta, body = _parse_frontmatter(md_path.read_text(encoding="utf-8"))
        doc_id = meta.get("id", md_path.stem)
        source = meta.get("source", md_path.stem)
        tags = meta.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",")]
        tags_str = ",".join(tags)
        for i, chunk in enumerate(_chunk(body)):
            cid = f"{doc_id}::c{i}"
            if cid in existing_ids and not rebuild:
                continue
            new_ids.append(cid)
            new_docs.append(chunk)
            new_metas.append({"source": source, "tags": tags_str})

    if new_ids:
        coll.add(ids=new_ids, documents=new_docs, metadatas=new_metas)
        print(f"Indexed {len(md_files)} docs, {len(new_ids)} new chunks → {CHROMA_DIR}")
    else:
        print(f"Indexed 0 new chunks (already up to date, {coll.count()} total chunks)")


if __name__ == "__main__":
    main(rebuild="--rebuild" in sys.argv)

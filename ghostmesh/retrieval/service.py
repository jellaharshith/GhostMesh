"""Retrieval service: Chroma primary, TF-IDF fallback. Never raises."""
from __future__ import annotations
import concurrent.futures
import logging
from pathlib import Path
from typing import List, Optional

from .fallback import tfidf_search

logger = logging.getLogger(__name__)

CHROMA_DIR = Path(__file__).parents[1] / "data" / "chroma"
COLLECTION_NAME = "ghostmesh-doctrine"
_TIMEOUT_MS = 5000  # cold start loads ONNX model (~1-2s); subsequent calls are <100ms
_WARMED_UP = False

_chroma_client = None
_collection = None


def _get_collection():
    global _chroma_client, _collection
    if _collection is not None:
        return _collection
    try:
        import chromadb
        from chromadb.utils import embedding_functions
        _chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = _chroma_client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_functions.DefaultEmbeddingFunction(),
        )
        return _collection
    except Exception as exc:
        logger.debug("Chroma unavailable (%s), using TF-IDF fallback", exc)
        return None


def warmup() -> None:
    """Pre-load chroma client and fire a dummy query to warm ONNX embeddings."""
    global _WARMED_UP
    if _WARMED_UP:
        return
    try:
        coll = _get_collection()
        if coll is not None:
            coll.query(query_texts=["warmup"], n_results=1)
            logger.debug("Chroma warmed up (%d chunks)", coll.count())
        _WARMED_UP = True
    except Exception as exc:
        logger.debug("Chroma warmup failed (%s), TF-IDF will be used", exc)
        _WARMED_UP = True


def _chroma_retrieve(query: str, k: int, tags: Optional[List[str]]) -> List[dict]:
    coll = _get_collection()
    if coll is None:
        raise RuntimeError("no collection")
    where = None
    if tags:
        where = {"tags": {"$contains": tags[0]}}
    results = coll.query(
        query_texts=[query],
        n_results=min(k, coll.count()),
        where=where if where else None,
    )
    snippets = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    for doc, meta, dist in zip(docs, metas, distances):
        tags_list = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
        snippets.append({
            "text": doc[:300],
            "source": meta.get("source", "unknown"),
            "tags": tags_list,
            "score": round(max(0.0, 1.0 - dist), 4),
        })
    return snippets


def retrieve(query: str, k: int = 3, tags: Optional[List[str]] = None) -> List[dict]:
    """
    Retrieve k doctrine snippets relevant to query.
    Returns list of dicts with keys: text, source, tags, score.
    Never raises — returns [] on total failure.
    """
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(_chroma_retrieve, query, k, tags)
            results = future.result(timeout=_TIMEOUT_MS / 1000.0)
        if results:
            return results
    except Exception as exc:
        logger.debug("Chroma retrieve failed (%s), falling back to TF-IDF", exc)

    try:
        return tfidf_search(query, k, tags)
    except Exception as exc:
        logger.warning("TF-IDF fallback also failed: %s", exc)
        return []

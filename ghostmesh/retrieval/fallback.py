"""Pure-python TF-IDF fallback when chromadb is unavailable."""
from __future__ import annotations
import math
import re
from pathlib import Path
from typing import Dict, List, Optional

CORPUS_DIR = Path(__file__).parent / "corpus"


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split YAML front-matter from body. Returns (meta_dict, body)."""
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
            k = k.strip()
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                meta[k] = [x.strip() for x in v[1:-1].split(",")]
            else:
                meta[k] = v
    return meta, body


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


_DOCS: Optional[List[dict]] = None


def _load_corpus() -> List[dict]:
    global _DOCS
    if _DOCS is not None:
        return _DOCS
    docs = []
    for path in sorted(CORPUS_DIR.glob("*.md")):
        meta, body = _parse_frontmatter(path.read_text())
        if not body:
            continue
        docs.append({
            "id": meta.get("id", path.stem),
            "source": meta.get("source", path.stem),
            "tags": meta.get("tags", []),
            "body": body,
            "tokens": _tokenize(body),
        })
    _DOCS = docs
    return _DOCS


def tfidf_search(query: str, k: int = 3, tags: Optional[List[str]] = None) -> List[dict]:
    docs = _load_corpus()
    if not docs:
        return []

    # Filter by tags if specified
    candidates = docs
    if tags:
        tag_set = set(tags)
        filtered = [d for d in docs if tag_set.intersection(d["tags"])]
        candidates = filtered if filtered else docs

    query_tokens = set(_tokenize(query))
    N = len(docs)

    # Compute IDF across all docs
    df: Dict[str, int] = {}
    for doc in docs:
        for tok in set(doc["tokens"]):
            df[tok] = df.get(tok, 0) + 1

    scored = []
    for doc in candidates:
        doc_tokens = doc["tokens"]
        if not doc_tokens:
            continue
        tf_map: Dict[str, float] = {}
        for tok in doc_tokens:
            tf_map[tok] = tf_map.get(tok, 0) + 1
        for tok in tf_map:
            tf_map[tok] /= len(doc_tokens)

        score = 0.0
        for tok in query_tokens:
            if tok in tf_map:
                idf = math.log((N + 1) / (df.get(tok, 0) + 1)) + 1
                score += tf_map[tok] * idf

        if score > 0:
            # Short snippet: first 200 chars of body
            snippet = doc["body"][:200].strip()
            scored.append({
                "text": snippet,
                "source": doc["source"],
                "tags": doc["tags"],
                "score": round(score, 4),
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:k]

"""
Lightweight vector index over article chunks for standard RAG.

- Builds embeddings for article text chunks from `data/articles/**.json`
- Saves index under `data/processing/vector_index/` as:
  - embeddings.npy (float32 [num_chunks, dim])
  - chunks.jsonl (one JSON per line with metadata and text)
  - meta.json (aux mappings like article_id -> chunk ids)

Works with the same embedding backends as used elsewhere (OpenAI or
sentence-transformers via a provided callable).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple, Set

import numpy as np


INDEX_DIR = Path("data/processing/vector_index")
EMBEDDINGS_FILE = INDEX_DIR / "embeddings.npy"
CHUNKS_FILE = INDEX_DIR / "chunks.jsonl"
META_FILE = INDEX_DIR / "meta.json"


@dataclass
class Chunk:
    chunk_id: str
    article_id: str
    title: str
    url: str
    published_date: Optional[str]
    text: str


def _iter_article_files(articles_root: Path) -> Iterable[Path]:
    for root, _dirs, files in os.walk(articles_root):
        for f in files:
            if f.endswith(".json"):
                yield Path(root) / f


def _normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def chunk_text(text: str, max_chars: int = 1200, overlap: int = 200) -> List[str]:
    if not text:
        return []
    text = _normalize_whitespace(text)
    if len(text) <= max_chars:
        return [text]
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks


def _load_article_json(path: Path) -> Optional[Dict]:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def build_index(
    articles_dir: str,
    embed_func: Callable[[str], List[float]],
    max_chars: int = 1200,
    overlap: int = 200,
    verbose: bool = False,
    max_files: Optional[int] = None,
    max_chunks_per_file: Optional[int] = None,
    chunk_progress_every: int = 50,
    skip_article_ids: Optional[Set[str]] = None,
) -> Tuple[np.ndarray, List[Chunk], Dict]:
    articles_root = Path(articles_dir)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    embeddings: List[List[float]] = []
    chunks: List[Chunk] = []
    article_to_chunk_ids: Dict[str, List[str]] = {}

    files = list(_iter_article_files(articles_root))
    if max_files is not None:
        files = files[:max_files]
    total_files = len(files)
    files_processed = 0
    total_chunks = 0
    if verbose:
        print(f"[VectorIndex] Building index from {total_files} files...", flush=True)

    for path in files:
        data = _load_article_json(path)
        if not data or not isinstance(data, dict):
            if verbose:
                print(f"[VectorIndex] Skipping non-article JSON: {path}", flush=True)
            continue

        article_id = data.get("article_id")
        if not article_id:
            continue
        if skip_article_ids and article_id in skip_article_ids:
            if verbose:
                print(f"[VectorIndex] Skipping already indexed article={article_id}", flush=True)
            files_processed += 1
            if verbose and (files_processed % 25 == 0 or files_processed == total_files):
                print(
                    f"[VectorIndex] Processed {files_processed}/{total_files} files, total chunks embedded: {total_chunks}",
                    flush=True,
                )
            continue
        title = data.get("title", "")
        url = data.get("url", "")
        published_date = data.get("published_date")
        body = (
            (data.get("content") or {}).get("body_text")
            or " ".join((data.get("content") or {}).get("paragraphs") or [])
        )
        chunk_texts = chunk_text(body, max_chars=max_chars, overlap=overlap)
        if not chunk_texts:
            if verbose:
                print(f"[VectorIndex] No content to chunk for article={article_id} ({path})", flush=True)
            files_processed += 1
            if verbose and (files_processed % 25 == 0 or files_processed == total_files):
                print(
                    f"[VectorIndex] Processed {files_processed}/{total_files} files, total chunks embedded: {total_chunks}",
                    flush=True,
                )
            continue
        if verbose:
            print(
                f"[VectorIndex] [{files_processed+1}/{total_files}] article={article_id} chunks={len(chunk_texts)}",
                flush=True,
            )
        for idx, ctext in enumerate(chunk_texts):
            try:
                emb = embed_func(ctext)
            except Exception:
                continue
            if not emb:
                continue
            chunk_id = f"{article_id}:{idx}"
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    article_id=article_id,
                    title=title,
                    url=url,
                    published_date=published_date,
                    text=ctext,
                )
            )
            embeddings.append(emb)
            article_to_chunk_ids.setdefault(article_id, []).append(chunk_id)
            total_chunks += 1
            if verbose and (total_chunks % chunk_progress_every == 0):
                print(
                    f"[VectorIndex] Embedded chunks: {total_chunks} (file {files_processed+1}/{total_files})",
                    flush=True,
                )

            if max_chunks_per_file is not None and (idx + 1) >= max_chunks_per_file:
                break

        files_processed += 1
        if verbose and (files_processed % 25 == 0 or files_processed == total_files):
            print(
                f"[VectorIndex] Processed {files_processed}/{total_files} files, total chunks embedded: {total_chunks}",
                flush=True,
            )

    if not embeddings:
        return np.zeros((0, 0), dtype=np.float32), [], {"article_to_chunk_ids": {}}

    emb_matrix = np.array(embeddings, dtype=np.float32)
    meta = {"article_to_chunk_ids": article_to_chunk_ids}
    return emb_matrix, chunks, meta


def save_index(embeddings: np.ndarray, chunks: List[Chunk], meta: Dict) -> None:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    np.save(EMBEDDINGS_FILE, embeddings)
    with CHUNKS_FILE.open("w", encoding="utf-8") as f:
        for ch in chunks:
            f.write(
                json.dumps(
                    {
                        "chunk_id": ch.chunk_id,
                        "article_id": ch.article_id,
                        "title": ch.title,
                        "url": ch.url,
                        "published_date": ch.published_date,
                        "text": ch.text,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    with META_FILE.open("w", encoding="utf-8") as f:
        json.dump(meta, f)


def load_index() -> Tuple[np.ndarray, List[Chunk], Dict]:
    if not EMBEDDINGS_FILE.exists() or not CHUNKS_FILE.exists() or not META_FILE.exists():
        return np.zeros((0, 0), dtype=np.float32), [], {"article_to_chunk_ids": {}}
    emb = np.load(EMBEDDINGS_FILE)
    loaded_chunks: List[Chunk] = []
    with CHUNKS_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            loaded_chunks.append(
                Chunk(
                    chunk_id=d["chunk_id"],
                    article_id=d["article_id"],
                    title=d.get("title", ""),
                    url=d.get("url", ""),
                    published_date=d.get("published_date"),
                    text=d.get("text", ""),
                )
            )
    with META_FILE.open("r", encoding="utf-8") as f:
        meta = json.load(f)
    return emb, loaded_chunks, meta


def cosine_sim(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a_norm = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-8)
    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-8)
    return np.dot(a_norm, b_norm.T)


def search(
    query: str,
    embed_func: Callable[[str], List[float]],
    top_k: int = 5,
) -> List[Dict]:
    emb, chunks, _meta = load_index()
    if emb.size == 0 or not chunks:
        return []
    q = np.array([embed_func(query)], dtype=np.float32)
    sims = cosine_sim(q, emb)[0]
    top_idx = np.argsort(-sims)[:top_k]
    results: List[Dict] = []
    for i in top_idx:
        ch = chunks[int(i)]
        results.append(
            {
                "score": float(sims[int(i)]),
                "chunk_id": ch.chunk_id,
                "article_id": ch.article_id,
                "title": ch.title,
                "url": ch.url,
                "published_date": ch.published_date,
                "text": ch.text,
            }
        )
    return results


def ensure_index(
    articles_dir: str,
    embed_func: Callable[[str], List[float]],
    verbose: bool = False,
    max_files: Optional[int] = None,
    max_chunks_per_file: Optional[int] = None,
    chunk_progress_every: int = 50,
    resume: bool = False,
) -> None:
    existing = EMBEDDINGS_FILE.exists() and CHUNKS_FILE.exists() and META_FILE.exists()
    if existing and not resume:
        if verbose:
            print("[VectorIndex] Existing index found. Skipping rebuild. Use resume=True to add new files.")
        return
    if not existing:
        if verbose:
            print("[VectorIndex] No index found. Building...")
        emb, chunks, meta = build_index(
            articles_dir,
            embed_func,
            verbose=verbose,
            max_files=max_files,
            max_chunks_per_file=max_chunks_per_file,
            chunk_progress_every=chunk_progress_every,
        )
        if emb.size:
            if verbose:
                print(f"[VectorIndex] Saving index with {emb.shape[0]} chunks...")
            save_index(emb, chunks, meta)
            if verbose:
                print("[VectorIndex] Index saved.")
        return

    # Resume path: load existing and append new articles
    if verbose:
        print("[VectorIndex] Resuming index build (skipping previously indexed articles)...")
    emb0, chunks0, meta0 = load_index()
    skip_ids: Set[str] = set((meta0.get("article_to_chunk_ids") or {}).keys())
    emb_new, chunks_new, meta_new = build_index(
        articles_dir,
        embed_func,
        verbose=verbose,
        max_files=max_files,
        max_chunks_per_file=max_chunks_per_file,
        chunk_progress_every=chunk_progress_every,
        skip_article_ids=skip_ids,
    )
    if emb_new.size == 0:
        if verbose:
            print("[VectorIndex] Nothing new to index.")
        return
    # Merge
    emb_all = np.concatenate([emb0, emb_new], axis=0) if emb0.size else emb_new
    chunks_all = chunks0 + chunks_new
    meta_all = {
        "article_to_chunk_ids": {**meta0.get("article_to_chunk_ids", {}), **meta_new.get("article_to_chunk_ids", {})}
    }
    if verbose:
        print(f"[VectorIndex] Saving resumed index with {emb_all.shape[0]} total chunks...")
    save_index(emb_all, chunks_all, meta_all)
    if verbose:
        print("[VectorIndex] Resume complete.")



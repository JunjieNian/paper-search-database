"""
数据加载器：MySQL + ChromaDB + Embedding API
与当前项目 backend_algo/vector_store.py 保持一致。
"""
import json
import pickle
from pathlib import Path
from typing import Callable, Dict, List, Optional

import chromadb
import numpy as np
from openai import OpenAI
from sqlalchemy import text

import config

_embedding_client = OpenAI(
    api_key=config.EMBEDDING_API_KEY or "missing-api-key",
    base_url=config.EMBEDDING_BASE_URL,
)
_chroma_client = None
_embedding_cache_path = (
    Path(config.CACHE_DIR)
    / f"embedding_cache_{config.EMBEDDING_MODEL}_{config.EMBEDDING_DIMENSIONS}.pkl"
)
_embedding_cache: Dict[str, List[float]] = {}
_embedding_cache_dirty = False
_default_collection_ready = False


if _embedding_cache_path.exists():
    try:
        with _embedding_cache_path.open("rb") as f:
            _embedding_cache = pickle.load(f)
    except Exception:
        _embedding_cache = {}


class EmbeddingFunctionWrapper:
    def __call__(self, texts: List[str]) -> List[List[float]]:
        return embed_texts(texts)


_embedding_fn = EmbeddingFunctionWrapper()


def _ensure_embedding_api_key():
    if config.EMBEDDING_API_KEY:
        return
    raise RuntimeError(
        "未配置 Embedding API Key，请设置 EMBEDDING_API_KEY、DASHSCOPE_API_KEY 或 VLLM_API_KEY。"
    )


def _normalize_text(text: str | None) -> str:
    if not text:
        return ""
    return " ".join(str(text).split())


def _persist_embedding_cache(force: bool = False):
    global _embedding_cache_dirty
    if not force and not _embedding_cache_dirty:
        return
    _embedding_cache_path.parent.mkdir(parents=True, exist_ok=True)
    with _embedding_cache_path.open("wb") as f:
        pickle.dump(_embedding_cache, f)
    _embedding_cache_dirty = False


def get_chroma_client():
    global _chroma_client
    if _chroma_client is not None:
        return _chroma_client

    if config.CHROMA_CLIENT_MODE == "persistent":
        Path(config.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=str(config.CHROMA_PERSIST_DIR))
        return _chroma_client

    if config.CHROMA_CLIENT_MODE == "http":
        _chroma_client = chromadb.HttpClient(host=config.CHROMA_HOST, port=config.CHROMA_PORT)
        return _chroma_client

    raise RuntimeError(
        f"不支持的 CHROMA_CLIENT_MODE={config.CHROMA_CLIENT_MODE!r}，可选 persistent / http"
    )


def get_collection(name: str | None = None):
    client = get_chroma_client()
    collection_name = name or config.COLLECTION_NAME
    try:
        return client.get_collection(name=collection_name)
    except Exception:
        return client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": config.DEFAULT_CHROMA_METRIC},
        )


def create_collection(name: str, metric: str = "cosine", reset: bool = False):
    client = get_chroma_client()
    if reset:
        try:
            client.delete_collection(name)
        except Exception:
            pass
    return client.create_collection(name=name, metadata={"hnsw:space": metric})


def delete_collection(name: str):
    client = get_chroma_client()
    try:
        client.delete_collection(name)
    except Exception:
        pass


def ensure_default_collection_populated(force_reindex: bool = False) -> int:
    global _default_collection_ready
    collection_name = config.COLLECTION_NAME

    if force_reindex:
        delete_collection(collection_name)
        collection = create_collection(collection_name, metric=config.DEFAULT_CHROMA_METRIC, reset=True)
    else:
        collection = get_collection(collection_name)

    try:
        existing_count = collection.count()
    except Exception:
        existing_count = 0

    if existing_count > 0 and not force_reindex:
        _default_collection_ready = True
        return existing_count

    papers = load_papers_from_mysql()
    ids = [str(paper["id"]) for paper in papers]
    documents = [build_document_text(paper) for paper in papers]
    embeddings = embed_texts(documents)
    collection.upsert(ids=ids, documents=documents, embeddings=embeddings)
    _default_collection_ready = True
    return len(ids)


def upsert_documents(collection, ids: List[str], documents: List[str], embeddings: List[List[float]] | None = None):
    if embeddings is None:
        embeddings = embed_texts(documents)
    collection.upsert(ids=ids, documents=documents, embeddings=embeddings)


def get_embedding_function() -> Callable[[List[str]], List[List[float]]]:
    return _embedding_fn


def embed_texts(texts: List[str], use_cache: bool = True) -> List[List[float]]:
    if not texts:
        return []

    _ensure_embedding_api_key()
    global _embedding_cache_dirty

    normalized = [_normalize_text(text) for text in texts]
    batch_size = max(1, min(config.EMBEDDING_BATCH_SIZE, 10))

    if not use_cache:
        direct_results: List[List[float]] = []
        for start in range(0, len(normalized), batch_size):
            batch = normalized[start:start + batch_size]
            response = _embedding_client.embeddings.create(
                model=config.EMBEDDING_MODEL,
                input=batch,
                dimensions=config.EMBEDDING_DIMENSIONS,
                encoding_format="float",
            )
            direct_results.extend(item.embedding for item in response.data)
        return direct_results

    results: List[Optional[List[float]]] = [None] * len(normalized)
    missing_indices: List[int] = []
    missing_texts: List[str] = []

    for index, text in enumerate(normalized):
        cached = _embedding_cache.get(text)
        if cached is not None:
            results[index] = cached
        else:
            missing_indices.append(index)
            missing_texts.append(text)

    for start in range(0, len(missing_texts), batch_size):
        batch = missing_texts[start:start + batch_size]
        response = _embedding_client.embeddings.create(
            model=config.EMBEDDING_MODEL,
            input=batch,
            dimensions=config.EMBEDDING_DIMENSIONS,
            encoding_format="float",
        )
        batch_embeddings = [item.embedding for item in response.data]
        for offset, embedding in enumerate(batch_embeddings):
            original_index = missing_indices[start + offset]
            text_value = normalized[original_index]
            _embedding_cache[text_value] = embedding
            results[original_index] = embedding
            _embedding_cache_dirty = True

    _persist_embedding_cache()
    return [embedding for embedding in results if embedding is not None]


# ── 从 MySQL 加载 ─────────────────────────────────────
def load_papers_from_mysql() -> List[Dict]:
    session = config.SessionLocal()
    try:
        result = session.execute(
            text(
                "SELECT id, title, abstract, authors, venue, year, keywords, url FROM papers ORDER BY id"
            )
        )
        papers = []
        for row in result:
            papers.append(
                {
                    "id": row[0],
                    "title": row[1],
                    "abstract": row[2],
                    "authors": row[3],
                    "venue": row[4],
                    "year": row[5],
                    "keywords": row[6],
                    "url": row[7],
                }
            )
        return papers
    finally:
        session.close()


# ── 向量库读取 ────────────────────────────────────────
def load_embeddings_by_ids(paper_ids: List[int | str]) -> Optional[np.ndarray]:
    ensure_default_collection_populated()
    collection = get_collection()
    str_ids = [str(pid) for pid in paper_ids]
    results = collection.get(ids=str_ids, include=["embeddings"])
    result_ids = results.get("ids")
    result_embeddings = results.get("embeddings")
    if result_ids is None or result_embeddings is None:
        return None
    if len(result_ids) == 0 or len(result_embeddings) == 0:
        return None

    embedding_map = {str(pid): emb for pid, emb in zip(result_ids, result_embeddings)}
    ordered_embeddings = [embedding_map[pid] for pid in str_ids if pid in embedding_map]
    if not ordered_embeddings:
        return None
    return np.array(ordered_embeddings, dtype=np.float32)


def load_all_embeddings(name: str | None = None) -> tuple[list[int], np.ndarray]:
    if name is None:
        ensure_default_collection_populated()
    collection = get_collection(name=name)
    results = collection.get(include=["embeddings"])
    ids = [int(pid) for pid in results.get("ids", [])]
    embeddings = np.array(results.get("embeddings", []), dtype=np.float32)
    return ids, embeddings


def vector_search(query: str, top_k: int = 20, collection_name: str | None = None, use_cache: bool = True):
    if collection_name is None:
        ensure_default_collection_populated()
    collection = get_collection(name=collection_name)
    query_embedding = embed_texts([query], use_cache=use_cache)[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "distances"],
    )
    ids = [int(x) for x in results["ids"][0]] if results.get("ids") else []
    documents = results["documents"][0] if results.get("documents") else []
    distances = results["distances"][0] if results.get("distances") else []
    return ids, documents, distances


def vector_search_by_embedding(embedding: List[float], top_k: int = 20, collection_name: str | None = None):
    if collection_name is None:
        ensure_default_collection_populated()
    collection = get_collection(name=collection_name)
    results = collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
        include=["documents", "distances"],
    )
    ids = [int(x) for x in results["ids"][0]] if results.get("ids") else []
    distances = results["distances"][0] if results.get("distances") else []
    return ids, distances


# ── 从 JSON 加载 ──────────────────────────────────────
def load_papers_from_json() -> List[Dict]:
    with open(config.PAPERS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


# ── 辅助函数 ──────────────────────────────────────────
def group_papers_by_keywords(papers: List[Dict]) -> Dict[str, List[int]]:
    keyword_map = {}
    for paper in papers:
        keywords = [kw.strip().lower() for kw in str(paper.get("keywords", "")).split(",")]
        for keyword in keywords:
            if keyword:
                keyword_map.setdefault(keyword, []).append(paper["id"])
    return keyword_map


def group_papers_by_venue(papers: List[Dict]) -> Dict[str, List[int]]:
    venue_map = {}
    for paper in papers:
        venue = str(paper.get("venue", "")).strip()
        if venue:
            venue_map.setdefault(venue, []).append(paper["id"])
    return venue_map


def build_document_text(paper: Dict, fields: List[str] | None = None) -> str:
    if fields is None:
        fields = ["title", "abstract", "keywords"]
    parts = []
    for field in fields:
        value = _normalize_text(paper.get(field))
        if value:
            parts.append(value)
    return ". ".join(parts)


def sql_keyword_search(keyword: str, limit: int = 20) -> List[int]:
    session = config.SessionLocal()
    try:
        pattern = f"%{keyword}%"
        result = session.execute(
            text(
                """
                SELECT id FROM papers
                WHERE title LIKE :p OR abstract LIKE :p
                   OR keywords LIKE :p OR authors LIKE :p
                LIMIT :limit
                """
            ),
            {"p": pattern, "limit": limit},
        )
        return [row[0] for row in result]
    finally:
        session.close()

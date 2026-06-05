from pathlib import Path

import chromadb
from openai import OpenAI

from config import (
    CHROMA_CLIENT_MODE,
    CHROMA_HOST,
    CHROMA_PERSIST_DIR,
    CHROMA_PORT,
    CHUNK_COLLECTION_NAME,
    COLLECTION_NAME,
    EMBEDDING_API_KEY,
    EMBEDDING_BASE_URL,
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL,
)

embedding_client = OpenAI(
    api_key=EMBEDDING_API_KEY or "missing-api-key",
    base_url=EMBEDDING_BASE_URL,
)
_client = None


def _ensure_embedding_api_key():
    if EMBEDDING_API_KEY:
        return
    raise RuntimeError(
        "未配置 Embedding API Key，请设置 EMBEDDING_API_KEY、DASHSCOPE_API_KEY 或 VLLM_API_KEY。"
    )


def _normalize_text(text: str | None) -> str:
    if not text:
        return ""
    return " ".join(str(text).split())


def build_document(paper: dict) -> str:
    parts = [
        _normalize_text(paper.get("title")),
        _normalize_text(paper.get("abstract")),
        _normalize_text(paper.get("keywords")),
    ]
    return ". ".join(part for part in parts if part)


def get_client():
    global _client
    if _client is not None:
        return _client

    if CHROMA_CLIENT_MODE == "persistent":
        persist_dir = Path(CHROMA_PERSIST_DIR)
        persist_dir.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(persist_dir))
        return _client

    if CHROMA_CLIENT_MODE == "http":
        try:
            _client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
            return _client
        except Exception as exc:
            raise RuntimeError(
                "连接 Chroma HTTP 服务失败。"
                f"请确认 http://{CHROMA_HOST}:{CHROMA_PORT} 已启动，"
                "或把 backend_algo/.env 里的 CHROMA_CLIENT_MODE 改成 persistent。"
            ) from exc

    raise RuntimeError(
        f"不支持的 CHROMA_CLIENT_MODE={CHROMA_CLIENT_MODE!r}，可选值: persistent / http"
    )


def embed_texts(texts: list[str]) -> list[list[float]]:
    """调用 DashScope/OpenAI 兼容 Embedding 接口。"""
    if not texts:
        return []

    _ensure_embedding_api_key()
    batch_size = max(1, min(EMBEDDING_BATCH_SIZE, 10))
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        resp = embedding_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=batch,
            dimensions=EMBEDDING_DIMENSIONS,
            encoding_format="float",
        )
        all_embeddings.extend(item.embedding for item in resp.data)

    return all_embeddings


def get_collection():
    client = get_client()
    try:
        return client.get_collection(name=COLLECTION_NAME)
    except Exception:
        return client.create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )


def index_papers(papers: list[dict]):
    """批量索引论文到 ChromaDB。
    papers: list of dict with keys: id, title, abstract, keywords
    """
    collection = get_collection()
    ids = [str(p["id"]) for p in papers]
    documents = [build_document(p) for p in papers]
    embeddings = embed_texts(documents)
    collection.upsert(ids=ids, documents=documents, embeddings=embeddings)
    return len(ids)


def search(query: str, top_k: int = 20):
    """向量检索，返回 paper id 列表、文档和距离。"""
    collection = get_collection()
    query_embedding = embed_texts([query])[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "distances"],
    )
    ids = results["ids"][0] if results["ids"] else []
    documents = results["documents"][0] if results["documents"] else []
    distances = results["distances"][0] if results["distances"] else []
    return ids, documents, distances


def get_embeddings_by_ids(paper_ids: list[str]):
    """获取指定论文的 embedding 向量。"""
    if not paper_ids:
        return []

    collection = get_collection()
    unique_ids: list[str] = []
    seen_ids: set[str] = set()
    for paper_id in paper_ids:
        if paper_id in seen_ids:
            continue
        seen_ids.add(paper_id)
        unique_ids.append(paper_id)

    results = collection.get(ids=unique_ids, include=["embeddings"])
    result_ids = results.get("ids", [])
    result_embeddings = results.get("embeddings", [])
    embedding_map = {
        paper_id: embedding
        for paper_id, embedding in zip(result_ids, result_embeddings)
    }
    return [
        embedding_map[paper_id]
        for paper_id in paper_ids
        if paper_id in embedding_map
    ]


# ---- Chunk collection (paper full-text chunks) ----


def get_chunk_collection():
    client = get_client()
    try:
        return client.get_collection(name=CHUNK_COLLECTION_NAME)
    except Exception:
        return client.create_collection(
            name=CHUNK_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )


def _truncate_for_embedding(text: str, max_chars: int = 8000) -> str:
    """Truncate text to fit within embedding API input limits (~8192 tokens).
    Conservative char limit as safety net since some PDFs contain long encoded
    strings that tokenize into many tokens.
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars]


def index_chunks(chunks: list[dict]):
    """批量索引论文分块到 ChromaDB。
    chunks: list of dict with keys: chunk_id, paper_id, chunk_index, text
    """
    if not chunks:
        return 0
    collection = get_chunk_collection()
    ids = [c["chunk_id"] for c in chunks]
    documents = [_truncate_for_embedding(c["text"]) for c in chunks]
    metadatas = [{"paper_id": c["paper_id"], "chunk_index": c["chunk_index"]} for c in chunks]
    embeddings = embed_texts(documents)
    collection.upsert(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)
    return len(ids)


def delete_paper_vectors(paper_id: int) -> dict:
    """删除 papers collection 与 paper_chunks collection 中该论文的所有向量。"""
    result = {"paper_removed": False, "chunks_removed": False}
    try:
        get_collection().delete(ids=[str(paper_id)])
        result["paper_removed"] = True
    except Exception as exc:
        print(f"[delete] papers collection delete failed: {exc}")
    try:
        get_chunk_collection().delete(where={"paper_id": paper_id})
        result["chunks_removed"] = True
    except Exception as exc:
        print(f"[delete] paper_chunks collection delete failed: {exc}")
    return result


def search_chunks(query: str, top_k: int = 5, paper_id: int | None = None):
    """检索论文分块。paper_id=None 时全库搜索，否则按 paper_id 过滤。"""
    collection = get_chunk_collection()
    query_embedding = embed_texts([query])[0]
    where_filter = {"paper_id": paper_id} if paper_id is not None else None
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "distances", "metadatas"],
        where=where_filter,
    )
    ids = results["ids"][0] if results["ids"] else []
    documents = results["documents"][0] if results["documents"] else []
    distances = results["distances"][0] if results["distances"] else []
    metadatas = results["metadatas"][0] if results["metadatas"] else []

    output = []
    for cid, doc, dist, meta in zip(ids, documents, distances, metadatas):
        score = 1.0 / (1.0 + dist)
        output.append({
            "chunk_id": cid,
            "paper_id": meta.get("paper_id", 0),
            "text": doc,
            "score": score,
        })
    return output

import chromadb
from openai import OpenAI

from config import (
    CHROMA_HOST,
    CHROMA_PORT,
    COLLECTION_NAME,
    EMBEDDING_API_KEY,
    EMBEDDING_BASE_URL,
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL,
)

client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
embedding_client = OpenAI(
    api_key=EMBEDDING_API_KEY or "missing-api-key",
    base_url=EMBEDDING_BASE_URL,
)


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
    collection = get_collection()
    results = collection.get(ids=paper_ids, include=["embeddings"])
    return results.get("embeddings", [])

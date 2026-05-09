import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

CHROMA_HOST = "localhost"
CHROMA_PORT = 8002
COLLECTION_NAME = "papers"

# ChromaDB 内置 all-MiniLM-L6-v2 (384维)，适合英文 CS/AI 论文
default_ef = DefaultEmbeddingFunction()

client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)


def get_collection():
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=default_ef,
    )


def index_papers(papers: list[dict]):
    """批量索引论文到 ChromaDB。
    papers: list of dict with keys: id, title, abstract, keywords
    """
    collection = get_collection()
    ids = [str(p["id"]) for p in papers]
    documents = [
        f"{p['title']}. {p['abstract']}. {p.get('keywords', '')}"
        for p in papers
    ]
    collection.upsert(ids=ids, documents=documents)
    return len(ids)


def search(query: str, top_k: int = 20):
    """向量检索，返回 paper id 列表、文档和距离。"""
    collection = get_collection()
    results = collection.query(
        query_texts=[query],
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

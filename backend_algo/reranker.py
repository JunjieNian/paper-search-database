import numpy as np
from vector_store import embed_texts


def rerank(query: str, documents: list[str], top_n: int = 10):
    """基于远程 embedding 余弦相似度的重排序。
    返回格式: [{"index": i, "relevance_score": float}, ...]，按分数降序。
    """
    if not documents:
        return []

    all_texts = [query] + documents
    all_embs = np.array(embed_texts(all_texts))
    query_emb = all_embs[0]
    doc_embs = all_embs[1:]

    query_norm = query_emb / (np.linalg.norm(query_emb) + 1e-9)
    doc_norms = doc_embs / (np.linalg.norm(doc_embs, axis=1, keepdims=True) + 1e-9)
    scores = doc_norms @ query_norm

    results = [
        {"index": int(i), "relevance_score": float(scores[i])}
        for i in range(len(documents))
    ]
    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    return results[:top_n]

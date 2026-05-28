from typing import Optional

import numpy as np
import requests

from config import (
    RERANK_API_KEY,
    RERANK_ENDPOINT,
    RERANK_INSTRUCT,
    RERANK_MAX_DOCUMENT_CHARS,
    RERANK_MODEL,
    RERANK_PROVIDER,
    RERANK_TIMEOUT_SECONDS,
)
from vector_store import embed_texts


_PROVIDER_ALIASES = {
    "": "none",
    "none": "none",
    "off": "none",
    "false": "none",
    "no": "none",
    "cosine": "cosine",
    "embedding-cosine": "cosine",
    "local-cosine": "cosine",
    "qwen": "qwen",
    "qwen-rerank": "qwen",
    "qwen3-rerank": "qwen",
}


def normalize_provider(provider: Optional[str]) -> str:
    if provider is None:
        return _PROVIDER_ALIASES.get(RERANK_PROVIDER, RERANK_PROVIDER)
    key = provider.strip().lower()
    return _PROVIDER_ALIASES.get(key, key)


def cosine_rerank(query: str, documents: list[str], top_n: int = 10):
    if not documents:
        return []

    all_texts = [query] + documents
    all_embs = np.array(embed_texts(all_texts), dtype=np.float32)
    query_emb = all_embs[0]
    doc_embs = all_embs[1:]

    query_norm = query_emb / (np.linalg.norm(query_emb) + 1e-9)
    doc_norms = doc_embs / (np.linalg.norm(doc_embs, axis=1, keepdims=True) + 1e-9)
    scores = doc_norms @ query_norm

    results = [
        {"index": int(index), "relevance_score": float(scores[index])}
        for index in range(len(documents))
    ]
    results.sort(key=lambda item: item["relevance_score"], reverse=True)
    return results[: min(top_n, len(results))]


def _truncate_documents(documents: list[str]) -> list[str]:
    truncated = []
    for document in documents:
        if len(document) <= RERANK_MAX_DOCUMENT_CHARS:
            truncated.append(document)
            continue
        clipped = document[:RERANK_MAX_DOCUMENT_CHARS]
        if " " in clipped:
            clipped = clipped.rsplit(" ", 1)[0]
        truncated.append(clipped)
    return truncated


def qwen_rerank(query: str, documents: list[str], top_n: int = 10):
    if not documents:
        return []
    if not RERANK_API_KEY:
        raise RuntimeError("未配置 RERANK_API_KEY 或 DASHSCOPE_API_KEY，无法调用 qwen rerank。")

    prepared_documents = _truncate_documents(documents)
    attempt_size = len(prepared_documents)

    while attempt_size >= min(top_n, len(prepared_documents)) and attempt_size > 0:
        payload = {
            "model": RERANK_MODEL,
            "input": {
                "query": query,
                "documents": prepared_documents[:attempt_size],
            },
            "parameters": {
                "top_n": min(top_n, attempt_size),
            },
        }
        if RERANK_INSTRUCT:
            payload["parameters"]["instruct"] = RERANK_INSTRUCT

        response = requests.post(
            RERANK_ENDPOINT,
            headers={
                "Authorization": f"Bearer {RERANK_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=RERANK_TIMEOUT_SECONDS,
        )
        if response.ok:
            data = response.json()
            results = data.get("output", {}).get("results", [])
            return [
                {
                    "index": int(item["index"]),
                    "relevance_score": float(item["relevance_score"]),
                }
                for item in results
                if "index" in item and "relevance_score" in item
            ]

        if response.status_code == 400 and attempt_size > top_n:
            attempt_size = max(top_n, attempt_size // 2)
            continue

        response.raise_for_status()

    return []


def rerank(query: str, documents: list[str], top_n: int = 10, provider: Optional[str] = None):
    resolved_provider = normalize_provider(provider)
    if resolved_provider == "none":
        return []
    if resolved_provider == "cosine":
        return cosine_rerank(query, documents, top_n=top_n)
    if resolved_provider == "qwen":
        return qwen_rerank(query, documents, top_n=top_n)
    raise ValueError(f"不支持的 rerank provider: {resolved_provider}")

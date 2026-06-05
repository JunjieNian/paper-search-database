from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import numpy as np
import requests

import reranker
import schemas
import vector_store
from config import (
    LLM_MODEL,
    RERANK_ENABLED,
    RERANK_PROVIDER,
    RERANK_RECALL_K,
    VLLM_API_KEY,
    VLLM_BASE_URL,
)

app = FastAPI()

HEADERS = {
    "Authorization": f"Bearer {VLLM_API_KEY}",
    "Content-Type": "application/json",
}


def _base_ranked_results(ids, distances, top_k: int):
    results = []
    for pid, dist in zip(ids[:top_k], distances[:top_k]):
        score = 1.0 / (1.0 + dist)
        results.append(schemas.SearchResult(paper_id=int(pid), score=score))
    results.sort(key=lambda item: item.score, reverse=True)
    return results


@app.post("/chat/stream/")
async def chat_stream(conversation: schemas.Conversation):
    def generator():
        with requests.post(
            f"{VLLM_BASE_URL}/chat/completions",
            json={
                "model": LLM_MODEL,
                "stream": True,
                "messages": [message.model_dump() for message in conversation.messages],
            },
            headers=HEADERS,
            stream=True,
            timeout=60,
        ) as response:
            response.raise_for_status()
            for raw_line in response.iter_lines():
                line = raw_line.decode("utf-8").strip()
                if line == "":
                    continue
                if line.startswith("data: "):
                    line = line[len("data: ") :]
                    if line == "[DONE]":
                        yield raw_line + b"\n"
                        break
                else:
                    yield raw_line + b"\n"
                    break
                yield raw_line + b"\n"

    return StreamingResponse(generator())


@app.post("/chat/", response_model=schemas.ConversationResponse)
async def chat(conversation: schemas.Conversation):
    response = requests.post(
        f"{VLLM_BASE_URL}/chat/completions",
        json={
            "model": LLM_MODEL,
            "stream": False,
            "messages": [message.model_dump() for message in conversation.messages],
        },
        headers=HEADERS,
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


@app.post("/search", response_model=schemas.SearchResponse)
async def search(req: schemas.SearchRequest):
    top_k = max(1, req.top_k)
    use_rerank = RERANK_ENABLED if req.use_rerank is None else req.use_rerank
    rerank_provider = req.rerank_provider or RERANK_PROVIDER
    recall_k = top_k
    if use_rerank and reranker.normalize_provider(rerank_provider) != "none":
        recall_k = max(top_k, req.recall_k or RERANK_RECALL_K)

    ids, documents, distances = vector_store.search(req.query, top_k=recall_k)
    if not ids:
        return schemas.SearchResponse(results=[])

    if use_rerank and reranker.normalize_provider(rerank_provider) != "none":
        try:
            reranked = reranker.rerank(
                req.query,
                documents,
                top_n=top_k,
                provider=rerank_provider,
            )
            if reranked:
                results = []
                for item in reranked:
                    index = item["index"]
                    if 0 <= index < len(ids):
                        results.append(
                            schemas.SearchResult(
                                paper_id=int(ids[index]),
                                score=float(item["relevance_score"]),
                            )
                        )
                if results:
                    return schemas.SearchResponse(results=results)
        except Exception as exc:
            print(f"[rerank] fallback to base vector ranking: {exc}")

    return schemas.SearchResponse(results=_base_ranked_results(ids, distances, top_k))


@app.post("/recommend", response_model=schemas.RecommendResponse)
async def recommend(req: schemas.RecommendRequest):
    if not req.clicked_paper_ids:
        return schemas.RecommendResponse(paper_ids=[])

    clicked_str_ids = [str(pid) for pid in req.clicked_paper_ids]
    embeddings = vector_store.get_embeddings_by_ids(clicked_str_ids)
    if embeddings is None or len(embeddings) == 0:
        return schemas.RecommendResponse(paper_ids=[])

    centroid = np.mean(np.array(embeddings), axis=0).tolist()
    collection = vector_store.get_collection()
    results = collection.query(
        query_embeddings=[centroid],
        n_results=req.top_k + len(req.clicked_paper_ids),
    )

    clicked_set = set(clicked_str_ids)
    paper_ids = []
    for pid in results["ids"][0]:
        if pid not in clicked_set:
            paper_ids.append(int(pid))
        if len(paper_ids) >= req.top_k:
            break

    return schemas.RecommendResponse(paper_ids=paper_ids)


@app.post("/index", response_model=schemas.IndexResponse)
async def index_papers(req: schemas.IndexRequest):
    papers = [paper.model_dump() for paper in req.papers]
    count = vector_store.index_papers(papers)
    return schemas.IndexResponse(indexed_count=count)


@app.post("/index-chunks", response_model=schemas.IndexResponse)
async def index_chunks(req: schemas.ChunkIndexRequest):
    chunks = [c.model_dump() for c in req.chunks]
    count = vector_store.index_chunks(chunks)
    return schemas.IndexResponse(indexed_count=count)


@app.post("/delete-paper", response_model=schemas.DeletePaperResponse)
async def delete_paper(req: schemas.DeletePaperRequest):
    result = vector_store.delete_paper_vectors(req.paper_id)
    return schemas.DeletePaperResponse(**result)


@app.post("/search-chunks", response_model=schemas.ChunkSearchResponse)
async def search_chunks(req: schemas.ChunkSearchRequest):
    results = vector_store.search_chunks(
        query=req.query,
        top_k=req.top_k,
        paper_id=req.paper_id,
    )
    return schemas.ChunkSearchResponse(
        results=[schemas.ChunkSearchResult(**r) for r in results]
    )

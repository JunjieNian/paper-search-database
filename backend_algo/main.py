from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import schemas
import requests
import numpy as np
import vector_store
from config import VLLM_BASE_URL, VLLM_API_KEY, LLM_MODEL


app = FastAPI()


HEADERS = {
    "Authorization": f"Bearer {VLLM_API_KEY}",
    "Content-Type": "application/json",
}


@app.post("/chat/stream/")
async def chat_stream(conversation: schemas.Conversation):

    def generator():
        with requests.post(f'{VLLM_BASE_URL}/chat/completions', json={
            'model': LLM_MODEL,
            'stream': True,
            'messages': [m.model_dump() for m in conversation.messages],
        }, headers=HEADERS, stream=True, timeout=60) as resp:
            resp.raise_for_status()
            for raw_line in resp.iter_lines():
                line = raw_line.decode('utf-8').strip()
                if line == '':
                    continue
                if line.startswith('data: '):
                    line = line[len('data: '):]
                    if line == '[DONE]':
                        yield raw_line + b'\n'
                        break
                else:
                    yield raw_line + b'\n'
                    break
                yield raw_line + b'\n'

    return StreamingResponse(generator())


@app.post("/chat/", response_model=schemas.ConversationResponse)
async def chat(conversation: schemas.Conversation):
    resp = requests.post(f'{VLLM_BASE_URL}/chat/completions', json={
        'model': LLM_MODEL,
        'stream': False,
        'messages': [m.model_dump() for m in conversation.messages],
    }, headers=HEADERS, timeout=60)
    resp.raise_for_status()
    return resp.json()


@app.post("/search", response_model=schemas.SearchResponse)
async def search(req: schemas.SearchRequest):
    """向量检索：ChromaDB 召回，用距离计算相关性分数"""
    ids, documents, distances = vector_store.search(req.query, top_k=req.top_k)
    if not ids:
        return schemas.SearchResponse(results=[])

    results = []
    for pid, dist in zip(ids, distances):
        score = 1.0 / (1.0 + dist)
        results.append(schemas.SearchResult(paper_id=int(pid), score=score))

    results.sort(key=lambda x: x.score, reverse=True)
    return schemas.SearchResponse(results=results)


@app.post("/recommend", response_model=schemas.RecommendResponse)
async def recommend(req: schemas.RecommendRequest):
    """基于用户点击历史的推荐：质心近邻搜索"""
    if not req.clicked_paper_ids:
        return schemas.RecommendResponse(paper_ids=[])

    clicked_str_ids = [str(pid) for pid in req.clicked_paper_ids]

    # 获取已点击论文的 embedding
    embeddings = vector_store.get_embeddings_by_ids(clicked_str_ids)
    if embeddings is None or len(embeddings) == 0:
        return schemas.RecommendResponse(paper_ids=[])

    # 计算质心
    centroid = np.mean(np.array(embeddings), axis=0).tolist()

    # 用质心向量进行近邻搜索
    collection = vector_store.get_collection()
    results = collection.query(
        query_embeddings=[centroid],
        n_results=req.top_k + len(req.clicked_paper_ids),
    )

    # 排除已点击的论文
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
    """将论文批量索引到 ChromaDB"""
    papers = [p.model_dump() for p in req.papers]
    count = vector_store.index_papers(papers)
    return schemas.IndexResponse(indexed_count=count)

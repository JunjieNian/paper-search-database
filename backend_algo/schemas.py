from typing import List, Optional

from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: Optional[str] = None
    reasoning_content: Optional[str] = None
    tool_calls: Optional[list] = None


class Conversation(BaseModel):
    messages: List[Message]


class ConversationResponseUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_tokens_details: Optional[dict] = None


class ConversationResponseChoice(BaseModel):
    index: int
    message: Message
    finish_reason: Optional[str] = None
    logprobs: Optional[dict] = None
    stop_reason: Optional[str] = None


class ConversationResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    system_fingerprint: Optional[str] = None
    choices: List[ConversationResponseChoice]
    usage: ConversationResponseUsage
    prompt_logprobs: Optional[list] = None


class SearchRequest(BaseModel):
    query: str
    top_k: int = 20
    use_rerank: Optional[bool] = None
    rerank_provider: Optional[str] = None
    recall_k: Optional[int] = None


class SearchResult(BaseModel):
    paper_id: int
    score: float


class SearchResponse(BaseModel):
    results: List[SearchResult]


class RecommendRequest(BaseModel):
    clicked_paper_ids: List[int]
    top_k: int = 10


class RecommendResponse(BaseModel):
    paper_ids: List[int]


class IndexPaper(BaseModel):
    id: int
    title: str
    abstract: str
    keywords: str = ""


class IndexRequest(BaseModel):
    papers: List[IndexPaper]


class IndexResponse(BaseModel):
    indexed_count: int


class ChunkIndex(BaseModel):
    chunk_id: str        # "paper_42_chunk_3"
    paper_id: int
    chunk_index: int
    text: str


class ChunkIndexRequest(BaseModel):
    chunks: List[ChunkIndex]


class ChunkSearchRequest(BaseModel):
    query: str
    top_k: int = 5
    paper_id: Optional[int] = None  # None = search all


class ChunkSearchResult(BaseModel):
    chunk_id: str
    paper_id: int
    text: str
    score: float


class ChunkSearchResponse(BaseModel):
    results: List[ChunkSearchResult]


class DeletePaperRequest(BaseModel):
    paper_id: int


class DeletePaperResponse(BaseModel):
    paper_removed: bool
    chunks_removed: bool

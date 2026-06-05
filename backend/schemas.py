from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel


class UserBase(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    is_active: bool
    is_superuser: bool

    class Config:
        from_attributes = True


class UserList(BaseModel):
    total: int
    users: List[User]


class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    response: str


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatStreamRequest(BaseModel):
    messages: List[ChatMessage]
    paper_id: Optional[int] = None   # paper Q&A mode
    use_rag: bool = True             # RAG mode (ignored when paper_id is set)


class PaperBase(BaseModel):
    title: str
    abstract: str
    authors: str
    venue: str
    year: int
    keywords: str
    url: str = ""


class PaperCreate(PaperBase):
    pass


class Paper(PaperBase):
    id: int
    has_pdf: bool = False
    owner_id: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaperBrief(BaseModel):
    id: int
    title: str
    authors: str
    venue: str
    year: int
    keywords: str
    url: str = ""
    has_pdf: bool = False
    owner_id: Optional[int] = None

    class Config:
        from_attributes = True


# ---- arXiv 上传/导入 ----


class ArxivPreviewRequest(BaseModel):
    url: str


class ArxivPreview(BaseModel):
    arxiv_id: str
    title: str = ""
    abstract: str = ""
    authors: str = ""
    venue: str = "arXiv"
    year: int = 0
    keywords: str = ""
    url: str = ""
    source: str = "none"  # openalex | none —— 提示元数据是否成功提取


class ArxivImportRequest(BaseModel):
    arxiv_id: str
    title: str
    abstract: str = ""
    authors: str = ""
    venue: str = "arXiv"
    year: int = 0
    keywords: str = ""
    url: str = ""


class PaperList(BaseModel):
    total: int
    papers: List[Paper]


class SearchRequest(BaseModel):
    query: str
    page: int = 1
    page_size: int = 10
    use_rerank: Optional[bool] = None
    recall_k: Optional[int] = None
    rerank_provider: Optional[str] = None


class SearchResponse(BaseModel):
    total: int
    papers: List[PaperBrief]


class ClickRequest(BaseModel):
    paper_id: int


class RecommendResponse(BaseModel):
    papers: List[PaperBrief]


class SearchHistoryItem(BaseModel):
    id: int
    query: str
    searched_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SearchHistoryList(BaseModel):
    items: List[SearchHistoryItem]

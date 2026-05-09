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
        # orm_mode = True
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


# ---- Paper schemas ----

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

    class Config:
        from_attributes = True


class PaperList(BaseModel):
    total: int
    papers: List[Paper]


# ---- Search schemas ----

class SearchRequest(BaseModel):
    query: str
    page: int = 1
    page_size: int = 10


class SearchResponse(BaseModel):
    total: int
    papers: List[PaperBrief]


# ---- Click schemas ----

class ClickRequest(BaseModel):
    paper_id: int


# ---- Recommend schemas ----

class RecommendResponse(BaseModel):
    papers: List[PaperBrief]


# ---- Search history schemas ----

class SearchHistoryItem(BaseModel):
    id: int
    query: str
    searched_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SearchHistoryList(BaseModel):
    items: List[SearchHistoryItem]

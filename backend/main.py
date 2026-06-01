import json as _json
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel

from sqlalchemy.orm import Session

import crud, models, schemas
from database import SessionLocal, engine
from security import verify_password

import os
from pathlib import Path

import requests

PDF_STORE = Path(__file__).resolve().parent / "pdf_store"
PDF_STORE.mkdir(exist_ok=True)
MAX_PDF_SIZE = 50 * 1024 * 1024  # 50 MB


# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


models.Base.metadata.create_all(bind=engine)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()


# Dependency
def get_session():
    with SessionLocal() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def authenticate_user(db: Session, username: str, password: str):
    user = crud.get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        db: SessionDep
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[schemas.User, Depends(get_current_user)],
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: SessionDep
) -> Token:
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get("/users/me/", response_model=schemas.User)
async def read_users_me(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
):
    return current_user


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: SessionDep):
    db_user = crud.get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=schemas.UserList)
async def read_users(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        db: SessionDep,
        skip: int = 0,
        limit: int = 100,
):
    users = crud.get_users(db, skip=skip, limit=limit)
    return schemas.UserList(total=crud.count_users(db), users=users)


@app.get("/users/{user_id}", response_model=schemas.User)
async def read_user(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        user_id: int,
        db: SessionDep
):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.get("/users/name/{username}", response_model=schemas.User)
async def read_user(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        username: str,
        db: SessionDep
):
    # print(current_user.username)
    db_user = crud.get_user_by_username(db, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


ALGO_URL = os.getenv("ALGO_URL", "http://localhost:8003")


@app.post("/chat", response_model=schemas.ChatResponse)
async def chat(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        chat_request: schemas.ChatRequest
):
    # print(current_user.username)
    resp = requests.post(f'{ALGO_URL}/chat', json={
        'messages': [
            {
                'role': 'user',
                'content': chat_request.prompt,
            }
        ]
    })
    return schemas.ChatResponse(response=resp.json()['choices'][0]['message']['content'])

SYSTEM_PROMPT = (
    "你是「学术论文搜索与推荐系统」的 AI 助手，专门帮助用户理解和分析计算机科学领域的学术论文。\n\n"
    "## 你的能力\n"
    "- 解读论文内容：解释摘要、方法、结论，用通俗语言阐述技术要点\n"
    "- 对比分析：比较不同论文的方法、优缺点、适用场景\n"
    "- 知识问答：回答数据库、分布式系统、机器学习等 CS 领域的学术问题\n"
    "- 使用引导：帮助用户使用论文搜索、推荐等系统功能\n\n"
    "## 系统功能\n"
    "1. 论文搜索 — 左侧菜单「论文搜索」，输入关键词进行语义搜索\n"
    "2. 论文推荐 — 左侧菜单「论文推荐」，根据浏览历史推荐相关论文\n"
    "3. 论文详情 — 点击论文查看摘要，点击链接图标跳转 Google Scholar\n"
    "4. AI 对话 — 即本页面\n\n"
    "## 回答要求\n"
    "- 用中文回答，技术术语保留英文原文并附中文解释\n"
    "- 引用论文时使用「标题 (作者, 会议 年份)」格式\n"
    "- 如果用户提到的论文在下方的阅读上下文中，优先基于论文实际内容回答\n"
    "- 回答要有条理，适当使用 Markdown 格式（列表、加粗、代码块等）\n"
)

PAPER_QA_SYSTEM_PROMPT = (
    "你是学术论文阅读助手。用户正在阅读一篇论文，你已经获得了论文的全文片段。\n"
    "请基于提供的论文内容片段回答用户的问题。如果片段中没有足够信息，请如实说明。\n\n"
    "## 回答要求\n"
    "- 用中文回答，技术术语保留英文原文并附中文解释\n"
    "- 回答要有条理，适当使用 Markdown 格式\n"
    "- 仅基于提供的论文内容回答，不要编造论文中没有的信息\n"
)


def _build_paper_context(db, user_id: int, max_papers: int = 5) -> str:
    """构建用户最近阅读的论文上下文"""
    clicked_ids = crud.get_clicked_paper_ids(db, user_id=user_id, limit=max_papers)
    if not clicked_ids:
        return ""

    papers = crud.get_papers_by_ids(db, clicked_ids)
    if not papers:
        return ""

    # 按点击顺序排列
    paper_map = {p.id: p for p in papers}
    ordered = [paper_map[pid] for pid in clicked_ids if pid in paper_map]

    context_parts = ["\n## 用户最近阅读的论文"]
    for i, p in enumerate(ordered, 1):
        context_parts.append(
            f"\n### 论文 {i}: {p.title}\n"
            f"- **作者**: {p.authors}\n"
            f"- **会议/期刊**: {p.venue} {p.year}\n"
            f"- **关键词**: {p.keywords}\n"
            f"- **摘要**: {p.abstract}\n"
        )

    return "\n".join(context_parts)


def _search_chunks(query: str, top_k: int = 5, paper_id: int | None = None) -> list[dict]:
    """调用 algo 层 search-chunks，返回 chunk 列表。"""
    try:
        payload: dict = {"query": query, "top_k": top_k}
        if paper_id is not None:
            payload["paper_id"] = paper_id
        resp = requests.post(f"{ALGO_URL}/search-chunks", json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json().get("results", [])
    except Exception:
        return []


def _build_paper_qa_context(query: str, paper_id: int, db) -> str:
    """构建论文问答的上下文（检索该论文内的全文分块）。"""
    paper = crud.get_paper(db, paper_id)
    chunks = _search_chunks(query, top_k=5, paper_id=paper_id)

    parts = []
    if paper:
        parts.append(
            f"## 论文信息\n"
            f"- **标题**: {paper.title}\n"
            f"- **作者**: {paper.authors}\n"
            f"- **会议/期刊**: {paper.venue} {paper.year}\n"
            f"- **摘要**: {paper.abstract}\n"
        )

    if chunks:
        parts.append("## 论文全文相关片段\n")
        for i, c in enumerate(chunks, 1):
            parts.append(f"### 片段 {i}\n{c['text']}\n")

    return "\n".join(parts)


def _build_rag_context(query: str, db) -> tuple[str, list[dict]]:
    """构建 RAG 全库检索上下文，返回 (context_str, references)。"""
    chunks = _search_chunks(query, top_k=8)
    if not chunks:
        return "", []

    # 按 paper_id 聚合
    paper_chunks: dict[int, list[dict]] = {}
    for c in chunks:
        pid = c["paper_id"]
        paper_chunks.setdefault(pid, []).append(c)

    # 获取论文元信息
    paper_ids = list(paper_chunks.keys())
    db_papers = crud.get_papers_by_ids(db, paper_ids)
    paper_map = {p.id: p for p in db_papers}

    parts = ["## 检索到的相关论文内容\n"]
    references = []
    for pid in paper_ids:
        p = paper_map.get(pid)
        if not p:
            continue
        references.append({"id": pid, "title": p.title})
        parts.append(f"### {p.title} ({p.authors}, {p.venue} {p.year})\n")
        for c in paper_chunks[pid]:
            parts.append(f"{c['text']}\n")
        parts.append("")

    return "\n".join(parts), references


@app.post("/chat/stream")
async def chat_stream(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        chat_request: schemas.ChatStreamRequest,
        db: SessionDep,
):
    user_query = ""
    for m in reversed(chat_request.messages):
        if m.role == "user" and m.content.strip():
            user_query = m.content.strip()
            break

    references: list[dict] = []

    if chat_request.paper_id is not None:
        # Mode A: Paper Q&A
        qa_context = _build_paper_qa_context(user_query, chat_request.paper_id, db)
        system_content = PAPER_QA_SYSTEM_PROMPT + "\n" + qa_context
    elif chat_request.use_rag and user_query:
        # Mode B: RAG full library
        rag_context, references = _build_rag_context(user_query, db)
        paper_context = _build_paper_context(db, user_id=current_user.id)
        system_content = SYSTEM_PROMPT + paper_context
        if rag_context:
            system_content += "\n" + rag_context
    else:
        # Mode C: Plain chat (original logic)
        paper_context = _build_paper_context(db, user_id=current_user.id)
        system_content = SYSTEM_PROMPT + paper_context

    messages = [{"role": "system", "content": system_content}]
    for m in chat_request.messages:
        messages.append({"role": m.role, "content": m.content})

    def generator():
        with requests.post(
            f"{ALGO_URL}/chat/stream/",
            json={"messages": messages},
            stream=True,
            timeout=60,
        ) as resp:
            for raw_line in resp.iter_lines():
                yield raw_line + b"\n"
        # After the LLM stream completes, send references if any
        if references:
            ref_data = _json.dumps({"references": references}, ensure_ascii=False)
            yield f"data: {ref_data}\n".encode("utf-8")

    return StreamingResponse(generator(), media_type="text/event-stream")


# ---- Paper endpoints ----


@app.get("/papers/", response_model=schemas.PaperList)
async def list_papers(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        db: SessionDep,
        skip: int = 0,
        limit: int = 20,
):
    papers = crud.get_papers(db, skip=skip, limit=limit)
    total = crud.count_papers(db)
    return schemas.PaperList(total=total, papers=papers)


@app.post("/papers/bulk", response_model=schemas.PaperList)
async def bulk_create_papers(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        papers: list[schemas.PaperCreate],
        db: SessionDep,
):
    db_papers = crud.create_papers_bulk(db, papers)
    return schemas.PaperList(total=len(db_papers), papers=db_papers)


@app.get("/papers/{paper_id}", response_model=schemas.Paper)
async def get_paper(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        paper_id: int,
        db: SessionDep,
):
    paper = crud.get_paper(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper


@app.post("/search", response_model=schemas.SearchResponse)
async def search_papers(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        search_req: schemas.SearchRequest,
        db: SessionDep,
):
    # 保存搜索历史
    crud.create_search_history(db, user_id=current_user.id, query=search_req.query)

    # 调用算法层搜索
    try:
        algo_payload = {
            "query": search_req.query,
            "top_k": search_req.page * search_req.page_size,
        }
        if search_req.use_rerank is not None:
            algo_payload["use_rerank"] = search_req.use_rerank
        if search_req.recall_k is not None:
            algo_payload["recall_k"] = search_req.recall_k
        if search_req.rerank_provider:
            algo_payload["rerank_provider"] = search_req.rerank_provider

        algo_resp = requests.post(f"{ALGO_URL}/search", json=algo_payload, timeout=30)
        algo_resp.raise_for_status()
        algo_results = algo_resp.json().get("results", [])
    except Exception:
        # 算法层不可用时降级为 SQL 模糊搜索
        total, papers = crud.search_papers_by_keyword(
            db, search_req.query,
            skip=(search_req.page - 1) * search_req.page_size,
            limit=search_req.page_size,
        )
        brief_papers = [
            schemas.PaperBrief.model_validate(p) for p in papers
        ]
        return schemas.SearchResponse(total=total, papers=brief_papers)

    # 从 MySQL 获取完整论文信息
    paper_ids = [r["paper_id"] for r in algo_results]
    if not paper_ids:
        return schemas.SearchResponse(total=0, papers=[])

    db_papers = crud.get_papers_by_ids(db, paper_ids)
    paper_map = {p.id: p for p in db_papers}

    # 按算法层排序保持顺序，分页
    start = (search_req.page - 1) * search_req.page_size
    end = start + search_req.page_size
    paged_ids = paper_ids[start:end]

    brief_papers = []
    for pid in paged_ids:
        if pid in paper_map:
            brief_papers.append(schemas.PaperBrief.model_validate(paper_map[pid]))

    return schemas.SearchResponse(total=len(paper_ids), papers=brief_papers)


@app.post("/click")
async def record_click(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        click_req: schemas.ClickRequest,
        db: SessionDep,
):
    paper = crud.get_paper(db, click_req.paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    crud.create_user_click(db, user_id=current_user.id, paper_id=click_req.paper_id)
    return {"status": "ok"}


@app.get("/recommend", response_model=schemas.RecommendResponse)
async def get_recommendations(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        db: SessionDep,
):
    # 获取用户点击历史
    clicked_ids = crud.get_clicked_paper_ids(db, user_id=current_user.id)
    if not clicked_ids:
        return schemas.RecommendResponse(papers=[])

    # 调用算法层推荐
    try:
        algo_resp = requests.post(f"{ALGO_URL}/recommend", json={
            "clicked_paper_ids": clicked_ids,
            "top_k": 10,
        }, timeout=30)
        algo_resp.raise_for_status()
        recommended_ids = algo_resp.json().get("paper_ids", [])
    except Exception:
        return schemas.RecommendResponse(papers=[])

    if not recommended_ids:
        return schemas.RecommendResponse(papers=[])

    # 从 MySQL 获取完整信息
    db_papers = crud.get_papers_by_ids(db, recommended_ids)
    paper_map = {p.id: p for p in db_papers}

    papers = []
    for pid in recommended_ids:
        if pid in paper_map:
            papers.append(schemas.PaperBrief.model_validate(paper_map[pid]))

    return schemas.RecommendResponse(papers=papers)


@app.get("/search/history", response_model=schemas.SearchHistoryList)
async def get_search_history(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        db: SessionDep,
):
    history = crud.get_search_history(db, user_id=current_user.id)
    return schemas.SearchHistoryList(items=history)


# ---- PDF endpoints ----


@app.get("/papers/{paper_id}/pdf")
async def get_paper_pdf(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        paper_id: int,
        db: SessionDep,
):
    paper = crud.get_paper(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    pdf_path = PDF_STORE / f"{paper_id}.pdf"
    if not pdf_path.is_file():
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{paper_id}.pdf"'},
    )


@app.post("/papers/{paper_id}/upload-pdf")
async def upload_paper_pdf(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        paper_id: int,
        file: UploadFile,
        db: SessionDep,
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only superuser can upload PDFs")
    paper = crud.get_paper(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")
    pdf_path = PDF_STORE / f"{paper_id}.pdf"
    size = 0
    with open(pdf_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_PDF_SIZE:
                pdf_path.unlink(missing_ok=True)
                raise HTTPException(status_code=400, detail="File too large (max 50MB)")
            f.write(chunk)
    paper.has_pdf = True
    db.commit()
    return {"status": "ok"}

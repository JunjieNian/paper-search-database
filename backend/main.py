from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel

from sqlalchemy.orm import Session

import crud, models, schemas
from database import SessionLocal, engine
from security import verify_password

import os
import requests


# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


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
    "你是「学术论文搜索与推荐系统」的 AI 助手。本系统的功能：\n"
    "1. 论文搜索 — 左侧菜单「论文搜索」，输入关键词进行语义搜索\n"
    "2. 论文推荐 — 左侧菜单「论文推荐」，根据浏览历史推荐相关论文\n"
    "3. 论文详情 — 点击搜索/推荐结果中的论文查看摘要，点击链接图标跳转 Google Scholar\n"
    "4. AI 对话 — 即本页面，可以问学术问题或网站使用方法\n"
    "论文库覆盖数据库、分布式系统、查询优化等 CS 领域。请用中文简洁回答。"
)


@app.post("/chat/stream")
async def chat_stream(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        chat_request: schemas.ChatStreamRequest,
):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
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
        algo_resp = requests.post(f"{ALGO_URL}/search", json={
            "query": search_req.query,
            "top_k": search_req.page * search_req.page_size,
        }, timeout=30)
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

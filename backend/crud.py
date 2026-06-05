from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import or_

import models, schemas

from security import get_password_hash


# ---- User CRUD ----

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def count_users(db: Session):
    return db.query(models.User).count()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# ---- Paper CRUD ----

def create_paper(db: Session, paper: schemas.PaperCreate):
    db_paper = models.Paper(**paper.model_dump())
    db.add(db_paper)
    db.commit()
    db.refresh(db_paper)
    return db_paper


def paper_visible_to(paper, user_id: int) -> bool:
    """公共论文(owner_id 为空)对所有人可见；用户上传论文仅 owner 本人可见。"""
    owner_id = getattr(paper, "owner_id", None)
    return owner_id is None or owner_id == user_id


def filter_visible_papers(papers, user_id: int):
    return [p for p in papers if paper_visible_to(p, user_id)]


def create_user_paper(db: Session, data, owner_id: int):
    """创建用户上传论文（owner_id 非空）。data 为含元数据字段的对象/schema。"""
    db_paper = models.Paper(
        title=data.title,
        abstract=data.abstract or "",
        authors=data.authors or "",
        venue=data.venue or "arXiv",
        year=data.year or 0,
        keywords=data.keywords or "",
        url=data.url or "",
        has_pdf=False,
        owner_id=owner_id,
    )
    db.add(db_paper)
    db.flush()  # 取得自增 id，但先不 commit（等 PDF 下载/索引成功）
    return db_paper


def get_user_papers(db: Session, owner_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Paper)
        .filter(models.Paper.owner_id == owner_id)
        .order_by(models.Paper.created_at.desc(), models.Paper.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def count_user_papers(db: Session, owner_id: int):
    return db.query(models.Paper).filter(models.Paper.owner_id == owner_id).count()


def get_user_paper_by_url(db: Session, owner_id: int, url: str):
    if not url:
        return None
    return (
        db.query(models.Paper)
        .filter(models.Paper.owner_id == owner_id, models.Paper.url == url)
        .first()
    )


def delete_paper(db: Session, paper_id: int):
    """删除论文及其点击记录。"""
    db.query(models.UserClick).filter(models.UserClick.paper_id == paper_id).delete()
    db.query(models.Paper).filter(models.Paper.id == paper_id).delete()
    db.commit()


def create_papers_bulk(db: Session, papers: List[schemas.PaperCreate]):
    db_papers = [models.Paper(**p.model_dump()) for p in papers]
    db.add_all(db_papers)
    db.commit()
    for p in db_papers:
        db.refresh(p)
    return db_papers


def get_paper(db: Session, paper_id: int):
    return db.query(models.Paper).filter(models.Paper.id == paper_id).first()


def get_papers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Paper).offset(skip).limit(limit).all()


def get_papers_by_ids(db: Session, paper_ids: List[int]):
    if not paper_ids:
        return []
    return db.query(models.Paper).filter(models.Paper.id.in_(paper_ids)).all()


def count_papers(db: Session):
    return db.query(models.Paper).count()


def search_papers_by_keyword(db: Session, keyword: str, skip: int = 0, limit: int = 10,
                             user_id: int | None = None):
    pattern = f"%{keyword}%"
    query = db.query(models.Paper).filter(
        or_(
            models.Paper.title.like(pattern),
            models.Paper.abstract.like(pattern),
            models.Paper.keywords.like(pattern),
            models.Paper.authors.like(pattern),
        )
    )
    if user_id is not None:
        # 仅返回公共论文 + 本人上传论文
        query = query.filter(
            or_(models.Paper.owner_id.is_(None), models.Paper.owner_id == user_id)
        )
    total = query.count()
    papers = query.offset(skip).limit(limit).all()
    return total, papers


# ---- UserClick CRUD ----

def create_user_click(db: Session, user_id: int, paper_id: int):
    db_click = models.UserClick(user_id=user_id, paper_id=paper_id)
    db.add(db_click)
    db.commit()
    db.refresh(db_click)
    return db_click


def get_clicked_paper_ids(db: Session, user_id: int, limit: int = 50):
    clicks = (
        db.query(models.UserClick.paper_id)
        .filter(models.UserClick.user_id == user_id)
        .order_by(models.UserClick.clicked_at.desc())
        .limit(limit)
        .all()
    )
    return [c.paper_id for c in clicks]


# ---- SearchHistory CRUD ----

def create_search_history(db: Session, user_id: int, query: str):
    db_history = models.SearchHistory(user_id=user_id, query=query)
    db.add(db_history)
    db.commit()
    db.refresh(db_history)
    return db_history


def get_search_history(db: Session, user_id: int, limit: int = 20):
    return (
        db.query(models.SearchHistory)
        .filter(models.SearchHistory.user_id == user_id)
        .order_by(models.SearchHistory.searched_at.desc())
        .limit(limit)
        .all()
    )

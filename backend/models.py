from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    email = Column(String(256), unique=True, index=True)
    first_name = Column(String(128))
    last_name = Column(String(128))
    hashed_password = Column(String(256))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)


class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True)
    title = Column(String(512))
    abstract = Column(Text)
    authors = Column(String(1024))
    venue = Column(String(256))
    year = Column(Integer)
    keywords = Column(String(512))
    url = Column(String(512))
    has_pdf = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserClick(Base):
    __tablename__ = "user_clicks"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    paper_id = Column(Integer, ForeignKey("papers.id"))
    clicked_at = Column(DateTime, default=datetime.utcnow)


class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    query = Column(String(512))
    searched_at = Column(DateTime, default=datetime.utcnow)

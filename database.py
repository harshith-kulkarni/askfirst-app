"""
Database models and CRUD operations using SQLAlchemy + SQLite.
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chat.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ─── Models ───────────────────────────────────────────────────────────────────

class Thread(Base):
    __tablename__ = "threads"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("Message", back_populates="thread", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("threads.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)   # "user" | "assistant" | "system"
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    thread = relationship("Thread", back_populates="messages")


class UniversalMemory(Base):
    """
    Stores distilled global context extracted from all conversations.
    This persists even after individual threads are deleted.
    """
    __tablename__ = "universal_memory"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)         # distilled fact / context
    source_thread_id = Column(Integer, nullable=True)  # original thread (informational only)
    created_at = Column(DateTime, default=datetime.utcnow)


# ─── DB Init ──────────────────────────────────────────────────────────────────

def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── CRUD ─────────────────────────────────────────────────────────────────────

def create_thread(db, title: str = "New Chat") -> Thread:
    thread = Thread(title=title)
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return thread


def get_threads(db) -> list[Thread]:
    return db.query(Thread).order_by(Thread.created_at.desc()).all()


def get_thread(db, thread_id: int) -> Thread | None:
    return db.query(Thread).filter(Thread.id == thread_id).first()


def delete_thread(db, thread_id: int) -> bool:
    thread = get_thread(db, thread_id)
    if not thread:
        return False
    db.delete(thread)
    db.commit()
    return True


def get_messages(db, thread_id: int) -> list[Message]:
    return (
        db.query(Message)
        .filter(Message.thread_id == thread_id)
        .order_by(Message.timestamp.asc())
        .all()
    )


def add_message(db, thread_id: int, role: str, content: str) -> Message:
    msg = Message(thread_id=thread_id, role=role, content=content)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_universal_memory(db) -> list[UniversalMemory]:
    return db.query(UniversalMemory).order_by(UniversalMemory.created_at.asc()).all()


def add_universal_memory(db, content: str, source_thread_id: int | None = None) -> UniversalMemory:
    mem = UniversalMemory(content=content, source_thread_id=source_thread_id)
    db.add(mem)
    db.commit()
    db.refresh(mem)
    return mem

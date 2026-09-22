"""数据库引擎和会话。"""

from sqlmodel import Session, SQLModel, create_engine

from app.config import DATABASE_URL

# SQLite 需要关闭同线程校验，配合 FastAPI 的线程池使用
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


def init_db() -> None:
    """建表（已存在则跳过）。幂等，可重复调用。"""
    # 确保所有表模型都已注册到 SQLModel.metadata
    from app import models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI 依赖：提供一个数据库会话。"""
    with Session(engine) as session:
        yield session

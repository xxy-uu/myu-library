"""数据库表模型：User / Book / Borrow。"""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(SQLModel, table=True):
    __tablename__ = "user"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, max_length=50)
    password_hash: str
    is_admin: bool = False


class Book(SQLModel, table=True):
    __tablename__ = "book"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True, max_length=200)
    author: str = Field(max_length=100)
    isbn: str = Field(unique=True, max_length=20)
    category: str = Field(index=True, max_length=50)
    publisher: str = Field(max_length=100)
    price: float
    stock: int = Field(default=0, ge=0)


class Borrow(SQLModel, table=True):
    __tablename__ = "borrow"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    book_id: int = Field(foreign_key="book.id", index=True)
    borrow_at: datetime = Field(default_factory=utcnow)
    return_at: Optional[datetime] = None
    returned: bool = Field(default=False)

"""接口出入参模型（Pydantic schema）。"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---------- 认证 ----------

class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class UserPublic(BaseModel):
    id: int
    username: str
    is_admin: bool

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- 图书 ----------

class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=100)
    isbn: str = Field(min_length=1, max_length=20)
    category: str = Field(min_length=1, max_length=50)
    publisher: str = Field(min_length=1, max_length=100)
    price: float = Field(ge=0)
    stock: int = Field(default=0, ge=0)


class BookUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    author: Optional[str] = Field(default=None, max_length=100)
    isbn: Optional[str] = Field(default=None, max_length=20)
    category: Optional[str] = Field(default=None, max_length=50)
    publisher: Optional[str] = Field(default=None, max_length=100)
    price: Optional[float] = Field(default=None, ge=0)
    stock: Optional[int] = Field(default=None, ge=0)


class BookPublic(BaseModel):
    id: int
    title: str
    author: str
    isbn: str
    category: str
    publisher: str
    price: float
    stock: int

    model_config = {"from_attributes": True}


class BookPage(BaseModel):
    total: int
    page: int
    size: int
    items: list[BookPublic]


# ---------- 借阅 ----------

class BorrowPublic(BaseModel):
    id: int
    user_id: int
    book_id: int
    borrow_at: datetime
    return_at: Optional[datetime]
    returned: bool

    model_config = {"from_attributes": True}

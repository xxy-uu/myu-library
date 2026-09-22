"""图书接口：CRUD + 分页搜索。"""

from fastapi import APIRouter, HTTPException, Query, status
from sqlmodel import func, or_, select

from app.deps import AdminUser, SessionDep
from app.models import Book
from app.schemas import BookCreate, BookPage, BookPublic, BookUpdate

router = APIRouter(prefix="/api/books", tags=["图书"])


@router.get("", response_model=BookPage)
def list_books(
    session: SessionDep,
    keyword: str | None = Query(default=None, description="按书名或作者模糊搜索"),
    category: str | None = Query(default=None, description="按分类精确筛选"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
) -> BookPage:
    """图书列表：分页 + 关键词 + 分类筛选，公开访问。"""
    stmt = select(Book)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(or_(Book.title.contains(keyword), Book.author.contains(keyword), Book.title.like(like)))
    if category:
        stmt = stmt.where(Book.category == category)

    total = session.exec(select(func.count()).select_from(stmt.subquery())).one()
    items = session.exec(stmt.offset((page - 1) * size).limit(size)).all()
    return BookPage(total=total, page=page, size=size, items=list(items))


@router.get("/{book_id}", response_model=BookPublic)
def get_book(book_id: int, session: SessionDep) -> Book:
    """图书详情。"""
    book = session.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图书不存在")
    return book


@router.post("", response_model=BookPublic, status_code=status.HTTP_201_CREATED)
def create_book(data: BookCreate, session: SessionDep, _admin: AdminUser) -> Book:
    """新增图书（管理员）。"""
    exists = session.exec(select(Book).where(Book.isbn == data.isbn)).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="ISBN 已存在")
    book = Book(**data.model_dump())
    session.add(book)
    session.commit()
    session.refresh(book)
    return book


@router.put("/{book_id}", response_model=BookPublic)
def update_book(
    book_id: int, data: BookUpdate, session: SessionDep, _admin: AdminUser
) -> Book:
    """修改图书（管理员），只更新传入的字段。"""
    book = session.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图书不存在")

    changes = data.model_dump(exclude_unset=True)
    if "isbn" in changes:
        dup = session.exec(
            select(Book).where(Book.isbn == changes["isbn"], Book.id != book_id)
        ).first()
        if dup:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="ISBN 已存在")

    for key, value in changes.items():
        setattr(book, key, value)
    session.add(book)
    session.commit()
    session.refresh(book)
    return book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int, session: SessionDep, _admin: AdminUser) -> None:
    """删除图书（管理员）。"""
    book = session.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图书不存在")
    session.delete(book)
    session.commit()

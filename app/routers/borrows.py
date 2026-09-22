"""借还接口：借书、还书、我的借阅记录。"""

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.deps import CurrentUser, SessionDep
from app.models import Book, Borrow
from app.schemas import BorrowPublic

router = APIRouter(prefix="/api/borrows", tags=["借阅"])


@router.post("/{book_id}", response_model=BorrowPublic, status_code=status.HTTP_201_CREATED)
def borrow_book(book_id: int, session: SessionDep, user: CurrentUser) -> Borrow:
    """借书：库存充足才能借，借出后库存减一。"""
    book = session.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图书不存在")
    if book.stock <= 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="库存不足，无法借出")

    pending = session.exec(
        select(Borrow).where(
            Borrow.user_id == user.id, Borrow.book_id == book_id, Borrow.returned == False  # noqa: E712
        )
    ).first()
    if pending:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="您已借阅此书且尚未归还")

    book.stock -= 1
    record = Borrow(user_id=user.id, book_id=book_id)
    session.add(book)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


@router.post("/{record_id}/return", response_model=BorrowPublic)
def return_book(record_id: int, session: SessionDep, user: CurrentUser) -> Borrow:
    """还书：只能归还自己的借阅记录（管理员可代还任意记录）。"""
    record = session.get(Borrow, record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="借阅记录不存在")
    if record.user_id != user.id and not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只能归还自己的借阅记录")
    if record.returned:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该书已归还，请勿重复操作")

    from app.models import utcnow

    record.returned = True
    record.return_at = utcnow()

    book = session.get(Book, record.book_id)
    if book is not None:
        book.stock += 1
        session.add(book)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


@router.get("/my", response_model=list[BorrowPublic])
def my_borrows(session: SessionDep, user: CurrentUser) -> list[Borrow]:
    """我的借阅记录（倒序）。"""
    stmt = (
        select(Borrow)
        .where(Borrow.user_id == user.id)
        .order_by(Borrow.borrow_at.desc(), Borrow.id.desc())
    )
    return list(session.exec(stmt).all())

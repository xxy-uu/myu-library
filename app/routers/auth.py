"""认证接口：注册、登录、我的信息。"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select

from app import security
from app.deps import CurrentUser, SessionDep
from app.models import User
from app.schemas import Token, UserCreate, UserPublic

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, session: SessionDep) -> User:
    """注册新用户（普通用户，非管理员）。"""
    exists = session.exec(select(User).where(User.username == data.username)).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名已存在")
    user = User(username=data.username, password_hash=security.hash_password(data.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep) -> Token:
    """登录换取 JWT（表单字段：username / password）。"""
    user = session.exec(select(User).where(User.username == form.username)).first()
    if user is None or not security.verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
        )
    return Token(access_token=security.create_access_token(user.username, user.is_admin))


@router.get("/me", response_model=UserPublic)
def me(user: CurrentUser) -> User:
    """当前登录用户的信息。"""
    return user

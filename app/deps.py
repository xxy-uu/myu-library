"""依赖项：取数据库会话、取当前登录用户、管理员校验。"""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from app import security
from app.database import get_session
from app.models import User

# tokenUrl 指向登录接口，/docs 的 Authorize 按钮会用到
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

SessionDep = Annotated[Session, Depends(get_session)]


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep
) -> User:
    """解析 Bearer 令牌，返回对应用户；无效则 401。"""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="令牌无效或已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = security.decode_token(token)
        username: str | None = payload.get("sub")
    except jwt.PyJWTError:
        raise unauthorized

    if not username:
        raise unauthorized

    user = session.exec(select(User).where(User.username == username)).first()
    if user is None:
        raise unauthorized
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(user: CurrentUser) -> User:
    """管理员校验依赖，非管理员返回 403。"""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限"
        )
    return user


AdminUser = Annotated[User, Depends(require_admin)]

"""密码哈希 + JWT 签发校验。"""

from datetime import datetime, timezone
from typing import Any

import bcrypt
import jwt

from app import config


def hash_password(plain: str) -> str:
    """bcrypt 哈希，返回可直接入库的字符串。"""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(subject: str, is_admin: bool = False) -> str:
    """签发 JWT，subject 为用户名。"""
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "admin": is_admin,
        "iat": now,
        "exp": now + config.ACCESS_TOKEN_EXPIRE,
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """解码并校验 JWT，无效/过期会抛出 jwt 相关异常。"""
    return jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])

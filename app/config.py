"""应用配置：密钥、数据库地址、令牌有效期。

生产环境请通过环境变量覆盖默认值，例如：
    export MYU_SECRET_KEY="一个足够长的随机字符串"
"""

import os
from datetime import timedelta

# JWT 签名密钥（默认值仅用于开发/演示，上线前务必替换）
SECRET_KEY: str = os.environ.get("MYU_SECRET_KEY", "dev-secret-change-me-in-production")

# JWT 签名算法
ALGORITHM: str = "HS256"

# 访问令牌有效期
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("MYU_TOKEN_EXPIRE_MINUTES", "120"))

# SQLite 数据库地址
DATABASE_URL: str = os.environ.get("MYU_DATABASE_URL", "sqlite:///./myu_library.db")

# 令牌过期时长（供 security.py 使用）
ACCESS_TOKEN_EXPIRE: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

"""MYu图书管理系统 - 程序入口。

启动：
    uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.database import init_db
from app.routers import auth, books, borrows


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="MYu图书管理系统 API",
    description="基于 FastAPI + SQLModel + SQLite + JWT 的图书管理系统（大学生课程设计项目）",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(books.router)
app.include_router(borrows.router)


@app.get("/", include_in_schema=False)
def root():
    """根路径跳转到接口文档。"""
    return RedirectResponse(url="/docs")

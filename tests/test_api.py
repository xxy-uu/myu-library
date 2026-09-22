"""自动化测试：注册登录、CRUD、权限拦截、分页搜索、借还流程、借还规则。

运行：pytest -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from app.database import get_session
from app.main import app
from app.models import User

BOOK = {
    "title": "Python编程从入门到实践",
    "author": "Eric Matthes",
    "isbn": "9787115428028",
    "category": "计算机",
    "publisher": "人民邮电出版社",
    "price": 89.0,
    "stock": 5,
}


@pytest.fixture(name="client")
def client_fixture():
    """每个测试用例使用独立的内存数据库。"""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    app.state.test_engine = engine

    def get_test_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(name="tokens")
def tokens_fixture(client):
    """注册 admin / student 两个用户并提权，返回两者令牌。"""
    assert client.post(
        "/api/auth/register", json={"username": "admin", "password": "admin123"}
    ).status_code == 201
    assert client.post(
        "/api/auth/register", json={"username": "student", "password": "student123"}
    ).status_code == 201

    with Session(app.state.test_engine) as session:
        admin = session.exec(select(User).where(User.username == "admin")).one()
        admin.is_admin = True
        session.add(admin)
        session.commit()

    return {
        "admin": _login(client, "admin", "admin123"),
        "student": _login(client, "student", "student123"),
    }


def _login(client: TestClient, username: str, password: str) -> str:
    resp = client.post("/api/auth/login", data={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------- 1. 注册登录 ----------

def test_register_and_login(client):
    # 注册成功
    resp = client.post(
        "/api/auth/register", json={"username": "alice", "password": "alice123456"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["username"] == "alice"
    assert body["is_admin"] is False
    assert "password" not in body and "password_hash" not in body

    # 重复注册被拦截
    resp = client.post(
        "/api/auth/register", json={"username": "alice", "password": "another123456"}
    )
    assert resp.status_code == 409

    # 登录成功拿到令牌，错误密码则 401
    token = _login(client, "alice", "alice123456")
    assert token
    assert (
        client.post("/api/auth/login", data={"username": "alice", "password": "wrongpass"}).status_code
        == 401
    )

    # 用令牌访问 /me；无令牌被拦截
    resp = client.get("/api/auth/me", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"
    assert client.get("/api/auth/me").status_code == 401


# ---------- 2. 图书 CRUD ----------

def test_books_crud(client, tokens):
    admin_h = _auth(tokens["admin"])

    # 新增
    resp = client.post("/api/books", json=BOOK, headers=admin_h)
    assert resp.status_code == 201, resp.text
    book_id = resp.json()["id"]

    # ISBN 重复被拦截
    assert client.post("/api/books", json=BOOK, headers=admin_h).status_code == 409

    # 查详情
    resp = client.get(f"/api/books/{book_id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == BOOK["title"]

    # 修改（部分字段）
    resp = client.put(f"/api/books/{book_id}", json={"price": 99.0}, headers=admin_h)
    assert resp.status_code == 200
    assert resp.json()["price"] == 99.0

    # 删除后查不到
    assert client.delete(f"/api/books/{book_id}", headers=admin_h).status_code == 204
    assert client.get(f"/api/books/{book_id}").status_code == 404


# ---------- 3. 权限拦截 ----------

def test_permission_interception(client, tokens):
    admin_h = _auth(tokens["admin"])
    student_h = _auth(tokens["student"])

    # 未登录 → 401
    assert client.post("/api/books", json=BOOK).status_code == 401
    assert client.get("/api/borrows/my").status_code == 401

    # 建一本书供后续验证
    book_id = client.post("/api/books", json=BOOK, headers=admin_h).json()["id"]

    # 普通用户 → 403（写操作全部拦截）
    assert client.post("/api/books", json=BOOK, headers=student_h).status_code == 403
    assert client.put(f"/api/books/{book_id}", json={"price": 1.0}, headers=student_h).status_code == 403
    assert client.delete(f"/api/books/{book_id}", headers=student_h).status_code == 403

    # 管理员正常通过
    assert client.put(f"/api/books/{book_id}", json={"price": 1.0}, headers=admin_h).status_code == 200

    # 伪造令牌 → 401
    assert client.get("/api/auth/me", headers=_auth("not-a-real-token")).status_code == 401


# ---------- 4. 分页搜索 ----------

def test_pagination_and_search(client, tokens):
    admin_h = _auth(tokens["admin"])
    books = [
        {**BOOK, "isbn": "9780000000001", "title": "Python入门", "author": "张三", "category": "计算机", "stock": 1},
        {**BOOK, "isbn": "9780000000002", "title": "Python进阶", "author": "李四", "category": "计算机", "stock": 2},
        {**BOOK, "isbn": "9780000000003", "title": "红楼梦", "author": "曹雪芹", "category": "文学", "stock": 3},
        {**BOOK, "isbn": "9780000000004", "title": "三体", "author": "刘慈欣", "category": "科幻", "stock": 4},
    ]
    for b in books:
        resp = client.post("/api/books", json=b, headers=admin_h)
        assert resp.status_code == 201, resp.text

    # 关键词搜索（命中 Python 两条）
    data = client.get("/api/books", params={"keyword": "Python"}).json()
    assert data["total"] == 2

    # 分类筛选
    data = client.get("/api/books", params={"category": "文学"}).json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "红楼梦"

    # 分页：size=2, page=2 应返回剩余 2 条
    data = client.get("/api/books", params={"page": 2, "size": 2}).json()
    assert data["total"] == 4
    assert data["page"] == 2
    assert len(data["items"]) == 2

    # 组合：关键词 + 分类 + 分页
    data = client.get(
        "/api/books", params={"keyword": "Python", "category": "计算机", "page": 1, "size": 1}
    ).json()
    assert data["total"] == 2
    assert len(data["items"]) == 1


# ---------- 5. 借还流程 ----------

def test_borrow_and_return_flow(client, tokens):
    admin_h = _auth(tokens["admin"])
    student_h = _auth(tokens["student"])

    # 建一本书，库存 2
    resp = client.post("/api/books", json={**BOOK, "isbn": "9780000000009", "stock": 2}, headers=admin_h)
    book_id = resp.json()["id"]

    # 学生借书成功，库存 2 -> 1
    resp = client.post(f"/api/borrows/{book_id}", headers=student_h)
    assert resp.status_code == 201, resp.text
    record_id = resp.json()["id"]
    assert client.get(f"/api/books/{book_id}").json()["stock"] == 1

    # 我的借阅记录里能看到
    resp = client.get("/api/borrows/my", headers=student_h)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["returned"] is False

    # student 归还成功，库存回到 2
    resp = client.post(f"/api/borrows/{record_id}/return", headers=student_h)
    assert resp.status_code == 200
    assert resp.json()["returned"] is True
    assert client.get(f"/api/books/{book_id}").json()["stock"] == 2


# ---------- 6. 借还规则 ----------

def test_borrow_rules(client, tokens):
    admin_h = _auth(tokens["admin"])
    student_h = _auth(tokens["student"])

    # 建一本书，库存 2
    resp = client.post("/api/books", json={**BOOK, "isbn": "9780000000008", "stock": 2}, headers=admin_h)
    book_id = resp.json()["id"]

    # 学生借书
    record_id = client.post(f"/api/borrows/{book_id}", headers=student_h).json()["id"]

    # 规则1：同一本书未归还不能重复借
    assert client.post(f"/api/borrows/{book_id}", headers=student_h).status_code == 409

    # 规则2：库存不足不能借（tom 借走最后一本，jerry 借不到）
    for name in ("tom", "jerry"):
        client.post("/api/auth/register", json={"username": name, "password": name + "123456"})
    tom_h = _auth(_login(client, "tom", "tom123456"))
    jerry_h = _auth(_login(client, "jerry", "jerry123456"))
    assert client.post(f"/api/borrows/{book_id}", headers=tom_h).status_code == 201
    assert client.post(f"/api/borrows/{book_id}", headers=jerry_h).status_code == 409

    # 规则3：只能还自己的借阅记录
    assert client.post(f"/api/borrows/{record_id}/return", headers=tom_h).status_code == 403

    # 规则4：不能重复归还
    assert client.post(f"/api/borrows/{record_id}/return", headers=student_h).status_code == 200
    assert client.post(f"/api/borrows/{record_id}/return", headers=student_h).status_code == 409

# MYu图书管理系统

基于 FastAPI 的图书管理系统 API，大学生课程设计项目。

技术栈：FastAPI + SQLModel + SQLite + JWT

## 三步跑起来

```bash
# 1. 创建虚拟环境并安装依赖
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. 灌入演示数据（12 本书 + 2 个账号）
python seed.py

# 3. 启动服务
uvicorn app.main:app --reload
```

打开 http://127.0.0.1:8000/docs ，所有接口都能在网页上直接点着测。

演示账号：

| 账号 | 密码 | 角色 | 权限 |
|---|---|---|---|
| admin | admin123 | 管理员 | 全部 |
| student | student123 | 普通用户 | 只能查询和借还 |

## 在 /docs 里测试受保护接口

1. 点右上角 **Authorize** 按钮
2. 输入 `admin` / `admin123`，点 Authorize
3. 之后所有请求会自动带上令牌，直接点 "Try it out" 即可

## 接口一览

| 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|
| POST | `/api/auth/register` | 注册 | 公开 |
| POST | `/api/auth/login` | 登录换令牌 | 公开 |
| GET | `/api/auth/me` | 我的信息 | 登录 |
| GET | `/api/books` | 分页 + 关键词搜索 | 公开 |
| GET | `/api/books/{id}` | 图书详情 | 公开 |
| POST | `/api/books` | 新增图书 | 管理员 |
| PUT | `/api/books/{id}` | 修改图书 | 管理员 |
| DELETE | `/api/books/{id}` | 删除图书 | 管理员 |
| POST | `/api/borrows/{book_id}` | 借书 | 登录 |
| POST | `/api/borrows/{id}/return` | 还书 | 登录 |
| GET | `/api/borrows/my` | 我的借阅记录 | 登录 |

分页搜索示例：

```
GET /api/books?keyword=Python&category=计算机&page=1&size=10
```

## 运行测试

```bash
pytest -v
```

6 个测试用例覆盖注册登录、CRUD、权限拦截、分页搜索、借还流程。

## 项目结构

```
myu-library/
├── app/
│   ├── config.py        配置（密钥、数据库地址、令牌有效期）
│   ├── database.py      数据库引擎和会话
│   ├── models.py        数据库表模型（User / Book / Borrow）
│   ├── schemas.py       接口出入参模型
│   ├── security.py      密码哈希 + JWT 签发校验
│   ├── deps.py          依赖项（取会话、取当前用户、管理员校验）
│   ├── routers/
│   │   ├── auth.py      认证接口
│   │   ├── books.py     图书 CRUD + 分页搜索
│   │   └── borrows.py   借还接口
│   └── main.py          程序入口
├── seed.py              演示数据
├── tests/test_api.py    自动化测试
└── 学习笔记.md          详细技术方案与知识点讲解
```


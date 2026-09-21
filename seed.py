"""初始化演示数据：一个管理员、一个普通用户、若干图书。

运行：python seed.py
重复运行不会产生重复数据（已存在就跳过）。
"""

from sqlmodel import Session, select

from app.database import engine, init_db
from app.models import Book, User
from app.security import hash_password

USERS = [
    ("admin", "admin123", True),
    ("student", "student123", False),
]

BOOKS = [
    ("Python编程从入门到实践", "Eric Matthes", "9787115428028", "计算机", "人民邮电出版社", 89.0, 5),
    ("流畅的Python", "Luciano Ramalho", "9787115454157", "计算机", "人民邮电出版社", 139.0, 3),
    ("算法导论", "Thomas H. Cormen", "9787111407010", "计算机", "机械工业出版社", 128.0, 2),
    ("深入理解计算机系统", "Randal E. Bryant", "9787111544937", "计算机", "机械工业出版社", 139.0, 4),
    ("数据库系统概念", "Abraham Silberschatz", "9787111375296", "计算机", "机械工业出版社", 99.0, 3),
    ("三体", "刘慈欣", "9787536692930", "科幻", "重庆出版社", 23.0, 6),
    ("活着", "余华", "9787506365437", "文学", "作家出版社", 20.0, 4),
    ("百年孤独", "加西亚·马尔克斯", "9787544253994", "文学", "南海出版公司", 39.5, 2),
    ("人类简史", "尤瓦尔·赫拉利", "9787508647357", "历史", "中信出版社", 68.0, 3),
    ("经济学原理", "曼昆", "9787301156872", "经济", "北京大学出版社", 118.0, 2),
    ("时间简史", "史蒂芬·霍金", "9787535732309", "科普", "湖南科学技术出版社", 45.0, 3),
    ("明朝那些事儿", "当年明月", "9787801655486", "历史", "中国海关出版社", 268.0, 1),
]


def main():
    init_db()
    with Session(engine) as session:
        for username, password, is_admin in USERS:
            if session.exec(select(User).where(User.username == username)).first():
                continue
            session.add(
                User(username=username, password_hash=hash_password(password), is_admin=is_admin)
            )

        for title, author, isbn, category, publisher, price, stock in BOOKS:
            if session.exec(select(Book).where(Book.isbn == isbn)).first():
                continue
            session.add(
                Book(
                    title=title,
                    author=author,
                    isbn=isbn,
                    category=category,
                    publisher=publisher,
                    price=price,
                    stock=stock,
                )
            )

        session.commit()

    print("初始化完成")
    print("  管理员：admin / admin123")
    print("  普通用户：student / student123")


if __name__ == "__main__":
    main()

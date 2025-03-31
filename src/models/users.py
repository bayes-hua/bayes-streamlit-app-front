import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from .database import get_db_connection, close_db_connection
from .config import TZ

# 用户信息表
# 表名：users
# 字段：id，username，password，vote，created_at，role
# role: user, admin


def init_users_table():
    """初始化用户表"""
    try:
        conn, c = get_db_connection()
        # 检查表是否存在
        c.execute(
            """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='users' """
        )

        if c.fetchone()[0] == 0:
            c.execute(
                """CREATE TABLE users
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          username TEXT UNIQUE NOT NULL,
                          password TEXT NOT NULL,
                          vote INTEGER DEFAULT 0,
                          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                          role TEXT DEFAULT 'user')"""
            )
            conn.commit()
        close_db_connection(conn)
        return True
    except Exception as e:
        print(f"Error initializing users table: {e}")
        return False


def create_user(username: str, password: str, role: str = "user") -> bool:
    """创建新用户"""
    try:
        conn, c = get_db_connection()
        c.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, password, role),
        )
        conn.commit()
        close_db_connection(conn)
        return True
    except sqlite3.IntegrityError:
        return False


def get_user(username: str) -> Optional[Dict[str, Any]]:
    """获取用户信息"""
    conn, c = get_db_connection()
    c.execute(
        "SELECT id, username, password, vote, created_at, role FROM users WHERE username = ?",
        (username,),
    )
    user = c.fetchone()
    close_db_connection(conn)

    if user:
        return {
            "id": user[0],
            "username": user[1],
            "password": user[2],
            "vote": user[3],
            "created_at": datetime.fromisoformat(user[4]).astimezone(TZ).isoformat(),
            "role": user[5],
        }
    return None


def update_user_vote(username: str, vote_delta: int) -> bool:
    """更新用户投票数"""
    try:
        conn, c = get_db_connection()
        c.execute(
            "UPDATE users SET vote = vote + ? WHERE username = ?",
            (vote_delta, username),
        )
        conn.commit()
        close_db_connection(conn)
        return True
    except Exception as e:
        print(f"Error updating user vote: {e}")
        return False


def verify_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """验证用户登录"""
    user = get_user(username)
    if user and user["password"] == password:
        return user
    return None


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """用户认证"""
    return verify_user(username, password)


def register_user(username: str, password: str) -> bool:
    """用户注册"""
    return create_user(username, password)


def list_users() -> list:
    """获取所有用户列表"""
    conn, c = get_db_connection()
    c.execute("SELECT id, username, vote, created_at, role FROM users")
    users = c.fetchall()
    close_db_connection(conn)

    return [
        {
            "id": user[0],
            "username": user[1],
            "vote": user[2],
            "created_at": datetime.fromisoformat(user[3]).astimezone(TZ).isoformat(),
            "role": user[4],
        }
        for user in users
    ]


def update_user_password(username: str, current_password: str, new_password: str) -> bool:
    """更新用户密码"""
    user = get_user(username)
    if not user or user["password"] != current_password:
        return False

    try:
        conn, c = get_db_connection()
        c.execute(
            "UPDATE users SET password = ? WHERE username = ?",
            (new_password, username)
        )
        conn.commit()
        close_db_connection(conn)
        return True
    except Exception as e:
        print(f"Error updating user password: {e}")
        return False

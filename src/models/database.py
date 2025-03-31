import sqlite3
from typing import Tuple
from .config import DB_PATH

def get_db_connection() -> Tuple[sqlite3.Connection, sqlite3.Cursor]:
    """获取数据库连接和游标"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    return conn, cursor

def close_db_connection(conn: sqlite3.Connection) -> None:
    """关闭数据库连接"""
    if conn:
        conn.close()
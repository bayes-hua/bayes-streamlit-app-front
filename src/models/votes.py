import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from .database import get_db_connection, close_db_connection
from .config import TZ

# 投票历史表
# 表名：votes
# 字段：id, question_id, username，vote，created_at, option, probability

def init_votes_table():
    """初始化投票历史表"""
    try:
        conn, c = get_db_connection()
        # 检查表是否存在
        c.execute('''SELECT count(name) FROM sqlite_master
                     WHERE type='table' AND name='votes' ''')

        if c.fetchone()[0] == 0:
            c.execute('''CREATE TABLE votes
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          question_id TEXT NOT NULL,
                          username TEXT NOT NULL,
                          vote REAL NOT NULL,
                          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                          option TEXT NOT NULL,
                          probability REAL NOT NULL)''')
            conn.commit()
        close_db_connection(conn)
        return True
    except Exception as e:
        print(f"Error initializing votes table: {e}")
        return False

def create_vote(question_id: str, username: str, vote: float, option: str, probability: float) -> bool:
    """创建新的投票记录"""
    try:
        conn, c = get_db_connection()
        c.execute('''INSERT INTO votes
                    (question_id, username, vote, option, probability)
                    VALUES (?, ?, ?, ?, ?)''',
                 (question_id, username, vote, option, probability))
        conn.commit()
        close_db_connection(conn)
        return True
    except Exception as e:
        print(f"Error creating vote: {e}")
        return False

def get_user_votes(username: str) -> List[Dict[str, Any]]:
    """获取用户的所有投票历史"""
    conn, c = get_db_connection()
    c.execute('''SELECT id, question_id, vote, created_at, option, probability
                 FROM votes WHERE username = ?
                 ORDER BY created_at DESC''', (username,))
    votes = c.fetchall()
    close_db_connection(conn)

    return [{
        'id': vote[0],
        'question_id': vote[1],
        'vote': vote[2],
        'created_at': datetime.fromisoformat(vote[3]).astimezone(TZ).isoformat(),
        'option': vote[4],
        'probability': vote[5]
    } for vote in votes]

def get_question_votes(question_id: str) -> List[Dict[str, Any]]:
    """获取某个问题的所有投票历史"""
    conn, c = get_db_connection()
    c.execute('''SELECT id, username, vote, created_at, option, probability
                 FROM votes WHERE question_id = ?
                 ORDER BY created_at DESC''', (question_id,))
    votes = c.fetchall()
    close_db_connection(conn)

    return [{
        'id': vote[0],
        'username': vote[1],
        'vote': vote[2],
        'created_at': datetime.fromisoformat(vote[3]).astimezone(TZ).isoformat(),
        'option': vote[4],
        'probability': vote[5]
    } for vote in votes]

def check_user_voted(username: str, question_id: str) -> bool:
    """检查用户是否已经对某个问题投过票"""
    conn, c = get_db_connection()
    c.execute('''SELECT COUNT(*) FROM votes
                 WHERE username = ? AND question_id = ?''',
             (username, question_id))
    count = c.fetchone()[0]
    close_db_connection(conn)
    return count > 0

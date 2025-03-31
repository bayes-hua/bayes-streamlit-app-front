from typing import Dict
from .database import get_db_connection, close_db_connection


# positions表
# 表名：positions
# 字段：question_id，user_id，position
# position: 字符串类型，用逗号分隔存储用户对各选项的投票数
# status: progress, ended, expired
# type: two, multiple

def init_positions_table() -> None:
    """初始化positions表"""
    conn, cursor = get_db_connection()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS positions (
            question_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            position TEXT NOT NULL,
            PRIMARY KEY (question_id, user_id)
        )
    ''')
    conn.commit()
    close_db_connection(conn)

def get_positions(question_id: str, user_id: str = None) -> Dict[str, str]:
    """获取指定问题的用户位置信息

    Args:
        question_id: 问题ID
        user_id: 用户ID，如果提供则只返回该用户的位置信息

    Returns:
        Dict[str, str]: 用户ID到位置的映射，位置为逗号分隔的字符串
    """
    conn, cursor = get_db_connection()
    if user_id:
        cursor.execute('''
            SELECT user_id, position FROM positions WHERE question_id = ? AND user_id = ?
        ''', (question_id, user_id))
    else:
        cursor.execute('''
            SELECT user_id, position FROM positions WHERE question_id = ?
        ''', (question_id,))
    result = {row[0]: row[1] for row in cursor.fetchall()}
    close_db_connection(conn)
    return result

def update_position(question_id: str, user_id: str, position: str) -> None:
    """更新或插入用户位置信息

    Args:
        question_id: 问题ID
        user_id: 用户ID
        position: 用户投票位置，逗号分隔的字符串，表示对各选项的投票数
    """
    conn, cursor = get_db_connection()
    cursor.execute('''
        INSERT OR REPLACE INTO positions (question_id, user_id, position)
        VALUES (?, ?, ?)
    ''', (question_id, user_id, position))
    conn.commit()
    close_db_connection(conn)

def delete_position(question_id: str, user_id: str) -> None:
    """删除用户位置信息"""
    conn, cursor = get_db_connection()
    cursor.execute('''
        DELETE FROM positions WHERE question_id = ? AND user_id = ?
    ''', (question_id, user_id))
    conn.commit()
    close_db_connection(conn)
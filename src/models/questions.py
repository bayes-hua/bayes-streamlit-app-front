import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from .database import get_db_connection, close_db_connection
from .config import TZ
import json

# 问题表
# 表名：questions
# 字段：id，created_at，question，status, type, tags, options, rule, probabilities, created_by, expire_at, result, end_at
# status: progress, ended, expired
# type: two, multiple


def init_questions_table():
    """初始化问题表"""
    try:
        conn, c = get_db_connection()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS questions (
                id TEXT PRIMARY KEY,
                created_at TIMESTAMP NOT NULL,
                question TEXT NOT NULL,
                status TEXT NOT NULL,
                type TEXT NOT NULL,
                tags TEXT,
                options TEXT NOT NULL,
                probabilities TEXT NOT NULL,
                rule TEXT,
                created_by TEXT NOT NULL,
                expire_at TIMESTAMP NOT NULL,
                result TEXT,
                end_at TIMESTAMP
            )
        """
        )
        conn.commit()
        close_db_connection(conn)
        return True
    except Exception as e:
        print(f"Error initializing questions table: {e}")
        return False


def create_question(question_data: Dict[str, Any]) -> bool:
    """创建新问题"""
    try:
        conn, c = get_db_connection()
        c.execute(
            """
            INSERT INTO questions (
                id, created_at, question, status, type, tags,
                options, probabilities, rule, created_by,
                expire_at, result, end_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                question_data["id"],
                question_data["created_at"].astimezone(TZ).isoformat(),
                question_data["question"],
                question_data["status"],
                question_data["type"],
                question_data["tags"],
                question_data["options"],
                question_data["probabilities"],
                question_data["rule"],
                question_data["created_by"],
                question_data["expire_at"],
                question_data["result"],
                question_data["end_at"],
            ),
        )
        conn.commit()
        close_db_connection(conn)
        return True
    except Exception as e:
        print(f"Error creating question: {e}")
        return False


def end_question(question_id: str, result: Dict[str, Any], end_by: str) -> bool:
    """结束问题"""
    try:
        conn, c = get_db_connection()

        # 验证问题是否存在且由当前用户创建
        c.execute("SELECT created_by FROM questions WHERE id = ?", (question_id,))
        question_data = c.fetchone()
        if not question_data or question_data[0] != end_by:
            return False

        # 简化result结构，只保留获胜选项
        simplified_result = {"winning_option": result.get("winning_option")}

        c.execute(
            """
            UPDATE questions
            SET status = 'ended',
                result = ?,
                end_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """,
            (json.dumps(simplified_result), question_id),
        )
        conn.commit()
        close_db_connection(conn)
        return True
    except Exception as e:
        print(f"Error ending question: {e}")
        return False


def check_expired_questions() -> bool:
    """检查并处理过期问题"""
    try:
        conn, c = get_db_connection()

        # 更新过期问题的状态
        c.execute(
            """
            UPDATE questions
            SET status = 'expired',
                result = ?,
                end_at = CURRENT_TIMESTAMP
            WHERE status = 'progress'
            AND expire_at < CURRENT_TIMESTAMP
        """,
            (json.dumps({"status": "expired"}),),
        )

        conn.commit()
        close_db_connection(conn)
        return True
    except Exception as e:
        print(f"Error checking expired questions: {e}")
        return False


def update_question_probabilities(
    question_id: str, option: str, probability_change: float
) -> bool:
    """更新问题概率"""
    conn = None
    try:
        conn, c = get_db_connection()

        # 获取当前问题的概率和选项
        c.execute(
            "SELECT probabilities, options FROM questions WHERE id = ?", (question_id,)
        )
        result = c.fetchone()
        if not result:
            return False

        current_probabilities, options_str = result
        probabilities = [float(p) for p in current_probabilities.split(",")]
        options = options_str.split(",")

        # 验证选项是否存在
        try:
            option_index = options.index(option)
        except ValueError:
            return False

        # 更新概率
        probabilities[option_index] += probability_change

        # 确保概率在有效范围内
        probabilities = [max(0.01, min(0.99, p)) for p in probabilities]

        # 归一化概率
        total = sum(probabilities)
        probabilities = [p / total for p in probabilities]

        # 保存更新后的概率
        c.execute(
            "UPDATE questions SET probabilities = ? WHERE id = ?",
            (",".join(str(p) for p in probabilities), question_id),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating probabilities: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            close_db_connection(conn)


def list_questions() -> List[Dict[str, Any]]:
    """获取所有问题列表"""
    conn, c = get_db_connection()
    c.execute(
        "SELECT id, created_at, question, status, type, tags, options, probabilities, rule, created_by, expire_at, result, end_at FROM questions"
    )
    questions = c.fetchall()
    close_db_connection(conn)

    return [
        {
            "id": q[0],
            "created_at": datetime.fromisoformat(q[1]).astimezone(TZ).isoformat(),
            "question": q[2],
            "status": q[3],
            "type": q[4],
            "tags": q[5],
            "options": q[6],
            "probabilities": q[7],
            "rule": q[8],
            "created_by": q[9],
            "expire_at": (
                datetime.fromisoformat(q[10]).astimezone(TZ).isoformat()
                if q[10]
                else None
            ),
            "result": q[11],
            "end_at": (
                datetime.fromisoformat(q[12]).astimezone(TZ).isoformat()
                if q[12]
                else None
            ),
        }
        for q in questions
    ]


def delete_question(question_id: str, username: str) -> bool:
    """删除问题及相关数据

    Args:
        question_id: 问题ID
        username: 用户名，用于验证权限

    Returns:
        bool: 删除是否成功
    """
    conn = None
    try:
        conn, c = get_db_connection()

        # 验证问题是否存在且由当前用户创建
        c.execute("SELECT created_by FROM questions WHERE id = ?", (question_id,))
        question_data = c.fetchone()
        if not question_data:
            return False

        # 验证权限：只有创建者才能删除
        if question_data[0] != username:
            return False

        # 开始事务
        conn.execute("BEGIN TRANSACTION")

        # 删除相关的投票数据
        c.execute("DELETE FROM votes WHERE question_id = ?", (question_id,))

        # 删除相关的仓位数据
        c.execute("DELETE FROM positions WHERE question_id = ?", (question_id,))

        # 删除问题
        c.execute("DELETE FROM questions WHERE id = ?", (question_id,))

        # 提交事务
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting question: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            close_db_connection(conn)

import streamlit as st
from models.questions import (
    init_questions_table,
    list_questions,
    check_expired_questions,
)
from models.votes import init_votes_table, create_vote
from models.users import init_users_table
from models.positions import init_positions_table

# 初始化数据库
def init_database():
    """初始化数据库"""
    init_users_table()
    init_questions_table()
    init_positions_table()
    init_votes_table()


# 初始化会话状态
def init_session_state():
    """初始化会话状态"""

    # 初始化页面状态
    if "page" not in st.session_state:
        st.session_state.page = "login_page"

    # 初始化认证状态
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = None


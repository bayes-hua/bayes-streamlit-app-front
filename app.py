from re import S
import streamlit as st
from create_question_page import create_question_page
from login import login_page
from question_list_page import question_list_page
from voting_platform_page import voting_platform_page


# 初始化 session state
def init_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = True
    if 'username' not in st.session_state:
        st.session_state.username = 'system'
    if 'role' not in st.session_state:
        st.session_state.role = 'user'
    if 'page' not in st.session_state:
        st.session_state.page = "login_page"
    if 'questions' not in st.session_state:
        st.session_state.questions = []
    if 'positions' not in st.session_state:
        st.session_state.positions = {}
    if 'tags' not in st.session_state:
        st.session_state.tags = set()  # 存储所有标签
    if 'vote_history' not in st.session_state:
        st.session_state.vote_history = []  # 存储所有投票历史

def main():
    init_session_state()
    # 设置页面配置
    st.set_page_config(
        page_title="预测平台",
        page_icon="🎯",
        layout="centered"
    )

    st.header(f"🎯 预测平台 ({st.session_state.username}-{st.session_state.role})",divider=True)
    
    if st.session_state.authenticated:
        if st.session_state.page == "login_page":
            st.session_state.page = "question_list_page"
    else:
        st.session_state.page = "login_page"

    # 移除侧边栏导航，使用页面状态直接控制显示内容
    switcher = {
        "login_page": login_page,
        "create_question_page": create_question_page,
        "voting_platform_page": voting_platform_page,
        "question_list_page": question_list_page
    }
    switcher[st.session_state.page]()
        
if __name__ == "__main__":
    main()

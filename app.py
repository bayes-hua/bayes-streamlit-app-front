import streamlit as st
from create_question_page import create_question_page
from login import login_page
from question_list_page import question_list_page
from voting_platform_page import voting_platform_page
from data import init_session_state, check_expired_questions
from datetime import datetime

def main():
    # 初始化 session state
    init_session_state()

    # 检查过期问题
    check_expired_questions()

    # 设置页面配置
    st.set_page_config(
        page_title="预测平台",
        page_icon="🎯",
        layout="centered"
    )

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    st.header(f"🎯 预测平台 ({st.session_state.username}-{st.session_state.role}) ⏰ {current_time}", divider=True)

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

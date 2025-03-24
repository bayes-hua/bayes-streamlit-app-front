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
    st.set_page_config(page_title="预测平台", page_icon="🎯", layout="centered")

    # 创建标题栏布局
    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"👤 {st.session_state.username} ({st.session_state.role})")
    with col2:
        st.caption(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    st.text("")

    # 页面路由配置
    pages = {
        "login_page": {"func": login_page, "title": "登录"},
        "create_question_page": {"func": create_question_page, "title": "创建问题"},
        "voting_platform_page": {"func": voting_platform_page, "title": "参与投票"},
        "question_list_page": {"func": question_list_page, "title": "问题列表"},
    }

    # 处理认证和页面跳转
    if st.session_state.authenticated:
        if st.session_state.page == "login_page":
            st.session_state.page = "question_list_page"
    else:
        st.session_state.page = "login_page"

    # 渲染当前页面
    current_page = pages[st.session_state.page]
    st.title(f"🎯 {current_page['title']}")
    # 添加返回按钮
    if not st.session_state.page in ["login_page", "question_list_page"]:
        if st.button("👈 返回管理页面", use_container_width=True):
            st.session_state.page = "question_list_page"
            st.rerun()
    current_page["func"]()


if __name__ == "__main__":
    main()

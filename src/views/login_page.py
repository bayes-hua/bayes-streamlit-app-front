import streamlit as st
from models.users import authenticate_user, register_user, get_user

def login_page():
    """登录页面"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        with st.container(border=True):
            username = st.text_input("👤 用户名")
            password = st.text_input("🔑 密码", type="password")

            if st.button("登录/注册", use_container_width=True):
                if not username or not password:
                    st.toast("❌ 用户名和密码不能为空", icon="🚨")
                    return

                # 检查用户是否存在
                existing_user = get_user(username)
                if existing_user:
                    # 用户存在，尝试登录
                    user = authenticate_user(username, password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.role = user["role"]
                        st.toast("✅ 登录成功", icon="🎉")
                        st.rerun()
                    else:
                        st.toast("❌ 密码错误", icon="🚨")
                else:
                    # 用户不存在，自动注册并登录
                    if register_user(username, password):
                        user = authenticate_user(username, password)
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.role = user["role"]
                        st.toast("✅ 注册成功并已自动登录", icon="🎉")
                        st.rerun()
                    else:
                        st.toast("❌ 注册失败，请重试", icon="🚨")
    return st.session_state.authenticated


def logout():
    """登出功能"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.rerun()

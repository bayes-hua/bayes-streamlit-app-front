import streamlit as st

# 定义用户列表 role: admin, user
USERS = [
    {"username": "bayes", "password": "h45D884DWE3?E212", "role":"admin"},
]

def login_page():
    """登录页面"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.title("🔐 登录系统")
        
        with st.container(border=True):
            username = st.text_input("👤 用户名")
            password = st.text_input("🔑 密码", type="password")
            
            if st.button("登录", use_container_width=True):
                # 验证用户名和密码
                if any(user["username"] == username and user["password"] == password for user in USERS):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.role = next(user["role"] for user in USERS if user["username"] == username)
                else:
                    st.toast("❌ 用户名或密码错误", icon="🚨")
    return st.session_state.authenticated

def logout():
    """登出功能"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.rerun()

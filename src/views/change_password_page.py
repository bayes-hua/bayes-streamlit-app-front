import streamlit as st
from models.users import update_user_password

def change_password_page():
    """修改密码页面"""
    with st.form("change_password_form"):
        current_password = st.text_input("当前密码", type="password")
        new_password = st.text_input("新密码", type="password")
        confirm_password = st.text_input("确认新密码", type="password")

        submitted = st.form_submit_button("提交")
        if submitted:
            if new_password != confirm_password:
                st.error("新密码与确认密码不匹配！")
            elif len(new_password) < 6:
                st.error("密码长度至少需要6个字符！")
            else:
                success = update_user_password(
                    st.session_state.username,
                    current_password,
                    new_password
                )
                if success:
                    st.success("密码修改成功！")
                else:
                    st.error("当前密码不正确！")
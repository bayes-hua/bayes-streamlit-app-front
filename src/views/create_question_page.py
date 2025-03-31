import streamlit as st
from datetime import datetime
import uuid
from models.questions import create_question
from models.database import get_db_connection, close_db_connection


# 创建问题页面
def validate_inputs(title, outcomes):
    """验证用户输入"""
    if not title:
        st.write("❌ 必须要有标题")
        return False

    total_value = sum(value for _, value in outcomes)
    if abs(total_value - 1.0) > 0.01:
        st.write("❌ 所有选项的预测值之和必须等于1")
        return False

    return True


# 创建问题数据结构
def create_question_data(
    title,
    question_type,
    outcomes,
    rules,
    expire_date,
    expire_time,
    tags_input,
    username,
):
    """创建问题数据结构"""
    tags = [
        tag.strip() for tag in tags_input.replace("，", ",").split(",") if tag.strip()
    ]

    expire_datetime = datetime.combine(expire_date, expire_time)

    return {
        "id": str(uuid.uuid4()),
        "created_at": datetime.now(),
        "question": title,
        "status": "progress",
        "type": "two" if question_type == "二元" else "multiple",
        "tags": ",".join(tags) if tags else None,
        "options": ",".join([outcome[0] for outcome in outcomes]),
        "probabilities": ",".join([str(outcome[1]) for outcome in outcomes]),
        "rule": rules,
        "created_by": username,
        "expire_at": expire_datetime.isoformat(),
        "result": None,
        "end_at": None,
    }


# 创建问题页面
def create_question_page():
    # 初始化选项计数器和问题类型
    if "extra_options" not in st.session_state:
        st.session_state.extra_options = 2
    if "question_type" not in st.session_state:
        st.session_state.question_type = "二元"

    # 获取用户输入
    title = st.text_input("📝 标题 **(必填)**")
    tags_input = st.text_input("🏷️ 标签 (用英文逗号分隔多个标签)", placeholder="")
    username = st.text_input("👤 创建者", value=st.session_state.username)
    question_type = st.selectbox("📊 类型", ["二元", "多元"], key="question_type")

    # 处理问题类型变化
    if question_type != st.session_state.get("last_question_type"):
        st.session_state.last_question_type = question_type
        st.session_state.extra_options = 2 if question_type == "二元" else 3

    # 获取选项
    outcomes = []
    for i in range(st.session_state.extra_options):
        col1, col2 = st.columns(2)
        with col1:
            option = st.text_input(
                f"💫 选项{i+1}", key=f"option_{i}", value=f"选项{i+1}"
            )
        with col2:
            value = st.number_input(
                f"💯 选项{i+1}预测值",
                min_value=0.0,
                max_value=1.0,
                value=1.0 / st.session_state.extra_options,
                key=f"value_{i}",
            )
        if option and value > 0:
            outcomes.append((option, value))

    # 多元选项管理
    if question_type == "多元":
        col1, col2 = st.columns(2)
        with col1:
            if st.button("添加选项", "add_btn", use_container_width=True):
                st.session_state.extra_options += 1
        with col2:
            if (
                st.button(
                    "删除选项",
                    "del_btn",
                    type="primary",
                    disabled=st.session_state.extra_options <= 3,
                    use_container_width=True,
                )
                and st.session_state.extra_options > 2
            ):
                st.session_state.extra_options -= 1

    rules = st.text_area("📋 规则（markdown）", height=150)

    # 过期时间设置
    col1, col2 = st.columns(2)
    with col1:
        expire_date = st.date_input("📅过期日期", min_value=datetime.now().date())
    with col2:
        expire_time = st.time_input("⏰ 过期时间")

    # 创建问题
    if st.button("✨ 创建新问题", use_container_width=True):
        if not validate_inputs(title, outcomes):
            return

        question = create_question_data(
            title,
            question_type,
            outcomes,
            rules,
            expire_date,
            expire_time,
            tags_input,
            username,
        )

        if create_question(question):
            st.write("✅ 问题创建成功！")
        else:
            st.write("❌ 问题创建失败，请重试！")

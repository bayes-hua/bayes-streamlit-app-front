import streamlit as st
from datetime import datetime
import uuid
from data import save_session_data


# 创建问题页面
def create_question_page():
    # 初始化选项计数器和问题类型
    if "extra_options" not in st.session_state:
        st.session_state.extra_options = 2  # 默认为2个选项
    if "question_type" not in st.session_state:
        st.session_state.question_type = "二元"  # 默认为二元

    # 标题
    title = st.text_input("📝 标题 **(必填)**")

    # 添加标签输入
    tags_input = st.text_input("🏷️ 标签 (用英文逗号分隔多个标签)", placeholder="")

    # 添加用户名输入
    username = st.text_input("👤 创建者", value=st.session_state.username)

    # 类型选择
    question_type = st.selectbox("📊 类型", ["二元", "多元"], key="question_type")

    # 当问题类型改变时重置选项票数
    if question_type != st.session_state.get("last_question_type"):
        st.session_state.last_question_type = question_type
        st.session_state.extra_options = 2 if question_type == "二元" else 3

    # 显示所有选项
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

    # 多元的选项控制按钮
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

    # 添加结束时间选择器
    col1, col2 = st.columns(2)
    with col1:
        expire_date = st.date_input(
            "📅过期日期",
            min_value=datetime.now().date(),
        )
    with col2:
        expire_time = st.time_input("⏰ 过期时间")

    # 添加结束密码输入
    end_password = st.text_input(
        "🔑 结束密码", type="password", help="用于验证问题结束时的操作"
    )

    if st.button("✨ 创建新问题", use_container_width=True):
        # 验证预测值总和是否接近1
        total_value = sum(value for _, value in outcomes)
        if title == "":
            st.write("❌ 必须要有标题")
            return
        if abs(total_value - 1.0) > 0.01:
            st.write("❌ 所有选项的预测值之和必须等于1")
            return

        # 处理标签，支持中英文逗号分隔
        tags = [
            tag.strip()
            for tag in tags_input.replace("，", ",").split(",")
            if tag.strip()
        ]
        st.session_state.tags.update(tags)

        # 组合日期和时间
        expire_datetime = datetime.combine(expire_date, expire_time)

        question = {
            "id": str(uuid.uuid4()),
            "title": title,
            "type": question_type,
            "outcomes": [outcome[0] for outcome in outcomes],
            "rules": rules,
            "created_at": datetime.now(),
            "expire_at": expire_datetime,
            "probabilities": {outcome[0]: outcome[1] for outcome in outcomes},
            "tags": tags,
            "create_by": username,
            "end_password": end_password,
        }
        st.session_state.questions.append(question)
        save_session_data()
        st.write("✅ 问题创建成功！")

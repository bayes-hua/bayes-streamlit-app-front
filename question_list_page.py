import streamlit as st
import pandas as pd


# 获取问题状态
def get_question_status(q):
    """获取问题状态"""
    if q.get("winner") == "过期":
        return "过期"
    return "已结束" if "winner" in q else "进行中"

# 准备单个问题的数据
def prepare_question_data(q, selected_tags, status_filter):
    """准备单个问题的数据"""
    # 标签筛选
    if selected_tags and not any(tag in q.get("tags", []) for tag in selected_tags):
        return None

    # 状态筛选
    status = get_question_status(q)
    if status_filter != "全部" and status != status_filter:
        return None

    # 计算总投票数
    total_positions = sum(st.session_state.positions[q["id"]].values()) if q["id"] in st.session_state.positions else 0

    # 获取最高概率的选项
    max_probability_option = max(q["probabilities"].items(), key=lambda x: x[1])

    # 基础数据
    question_data = {
        "标题": q["title"],
        "状态": status,
        "类型": q["type"],
        "标签": ", ".join(q.get("tags", [])),
        "创建者": q["create_by"],
        "创建时间": q["created_at"].strftime("%Y-%m-%d %H:%M"),
        "过期时间": q["expire_at"].strftime("%Y-%m-%d %H:%M"),
        "规则": q.get("rules", "暂无规则"),
        "总投票数": f"{total_positions:.2f}",
        "领先选项": max_probability_option[0],
        "领先概率": f"{max_probability_option[1]:.1%}",
        "选项": ", ".join(q["outcomes"]),
    }

    # 添加结束相关信息
    if "winner" in q:
        question_data.update({
            "胜出选项": q["winner"],
            "结束用户": q.get("end_by", "未知"),
            "结束时间": q["end_at"].strftime("%Y-%m-%d %H:%M")
        })

    return question_data

# 获取表格列配置
def get_column_config(has_ended_questions):
    """获取表格列配置"""
    column_config = {
        "标题": st.column_config.TextColumn("📝 标题"),
        "状态": st.column_config.TextColumn("🔄 状态"),
        "类型": st.column_config.TextColumn("📊 类型"),
        "标签": st.column_config.TextColumn("🏷️ 标签"),
        "创建者": st.column_config.TextColumn("👤 创建者"),
        "创建时间": st.column_config.TextColumn("🕒 创建时间"),
        "过期时间": st.column_config.TextColumn("⌛ 过期时间"),
        "规则": st.column_config.TextColumn("📜 规则"),
        "总投票数": st.column_config.TextColumn("📈 总投票数"),
        "领先选项": st.column_config.TextColumn("🥇 领先选项"),
        "领先概率": st.column_config.TextColumn("💯 领先概率"),
        "选项": st.column_config.TextColumn("📋 选项"),
    }

    if has_ended_questions:
        column_config.update({
            "结束用户": st.column_config.TextColumn("👤 结束用户"),
            "结束时间": st.column_config.TextColumn("⏰ 结束时间"),
            "胜出选项": st.column_config.TextColumn("🏆 胜出选项")
        })

    return column_config

# 问题列表页面
def question_list_page():
    # 添加创建和投票按钮
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✨ 创建新问题", use_container_width=True):
            st.session_state.page = "create_question_page"
            st.rerun()
    with col2:
        if st.button("🎲 参与投票", use_container_width=True):
            st.session_state.page = "voting_platform_page"
            st.rerun()

    if not st.session_state.questions:
        st.info("暂无问题数据")
        return

    # 添加标签和状态筛选
    col1, col2 = st.columns(2)
    with col1:
        selected_tags = st.multiselect(
            "🏷️ 按标签筛选",
            options=sorted(list(st.session_state.tags)) if st.session_state.tags else []
        )
    with col2:
        status_filter = st.radio(
            "🔄 状态筛选", ["全部", "进行中", "已结束", "过期"], horizontal=True
        )

    # 准备表格数据
    data = [prepare_question_data(q, selected_tags, status_filter)
            for q in st.session_state.questions]
    data = [d for d in data if d is not None]

    # 创建并显示表格
    df = pd.DataFrame(data)
    has_ended_questions = any(q.get("winner") for q in st.session_state.questions)
    column_config = get_column_config(has_ended_questions)

    st.dataframe(
        df, column_config=column_config, use_container_width=True, hide_index=True
    )

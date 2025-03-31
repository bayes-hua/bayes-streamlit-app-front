import streamlit as st
import pandas as pd
from models.questions import list_questions, delete_question
from datetime import datetime


# 获取问题状态
def get_question_status(q):
    """获取问题状态"""
    return q.get("status", "progress")


# 准备单个问题的数据
def prepare_question_data(q, selected_tags, status_filter, current_user):
    """准备单个问题的数据"""
    # 标签筛选
    question_tags = q.get("tags", "").split(",") if q.get("tags") else []
    if selected_tags and not any(tag in question_tags for tag in selected_tags):
        return None

    # 状态筛选
    status = q.get("status", "progress")
    status_map = {"progress": "进行中", "ended": "已结束", "expired": "已过期"}
    status = status_map.get(status, status)

    if status_filter != "全部" and status != status_filter:
        return None

    # 计算总投票数
    from models.positions import get_positions

    positions = get_positions(q["id"])

    # 解析所有用户的position字符串并计算总投票数
    total_positions = 0
    options = q["options"].split(",")
    for user_id, position_str in positions.items():
        position_parts = position_str.split(",")
        for i, part in enumerate(position_parts):
            if i < len(options) and part:
                try:
                    total_positions += float(part)
                except ValueError:
                    pass

    # 获取选项和概率
    options = q["options"].split(",")
    probabilities = [float(p) for p in q["probabilities"].split(",")]
    max_probability_idx = probabilities.index(max(probabilities))

    # 基础数据
    question_data = {
        "问题ID": q["id"],
        "标题": q["question"],
        "状态": status,
        "类型": q["type"],
        "标签": ", ".join(question_tags),
        "创建者": q["created_by"],
        "创建时间": datetime.fromisoformat(q["created_at"]).strftime("%Y-%m-%d %H:%M"),
        "过期时间": datetime.fromisoformat(q["expire_at"]).strftime("%Y-%m-%d %H:%M"),
        "规则": q.get("rule", "暂无规则"),
        "总投票数": f"{total_positions:.2f}",
        "领先选项": options[max_probability_idx],
        "领先概率": f"{probabilities[max_probability_idx]:.1%}",
        "选项": ", ".join(options),
    }

    # 添加结束相关信息
    if "result" in q:
        question_data.update(
            {
                "胜出选项": q["result"],
                "结束用户": q.get("end_by"),
                "结束时间": (
                    datetime.fromisoformat(q["end_at"]).strftime("%Y-%m-%d %H:%M")
                    if q["end_at"]
                    else ""
                ),
            }
        )

    return question_data


# 获取表格列配置
def get_column_config(has_ended_questions):
    """获取表格列配置"""
    column_config = {
        "问题ID": None,  # 隐藏问题ID列
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
        column_config.update(
            {
                "结束用户": st.column_config.TextColumn("👤 结束用户"),
                "结束时间": st.column_config.TextColumn("⏰ 结束时间"),
                "胜出选项": st.column_config.TextColumn("🏆 胜出选项"),
            }
        )

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

    # 获取当前用户名
    current_user = st.session_state.username if "username" in st.session_state else None

    questions = list_questions()
    if not questions:
        st.info("暂无问题数据")
        return

    # 添加删除问题下拉框
    if current_user:
        deletable_questions = [
            q for q in questions if q["created_by"] == current_user
        ]
        if deletable_questions:
            question_titles = [q["question"] for q in deletable_questions]
            selected_question = st.selectbox(
                "🗑️ 选择要删除的问题",
                question_titles,
                index=None,
                placeholder="选择您创建的问题进行删除"
            )

            if selected_question:
                if st.button("确认删除", type="primary"):
                    question_to_delete = next(
                        q for q in deletable_questions if q["question"] == selected_question
                    )
                    if delete_question(question_to_delete["id"], current_user):
                        st.success(f"✅ 问题 '{selected_question}' 已删除")
                        st.rerun()
                    else:
                        st.error("❌ 删除失败，请重试")

    # 添加标签和状态筛选
    col1, col2 = st.columns(2)
    with col1:
        # 从问题数据中获取所有标签
        all_tags = set()
        for q in questions:
            if q.get("tags"):
                tags = [tag.strip() for tag in q["tags"].split(",") if tag.strip()]
                all_tags.update(tags)
        selected_tags = st.multiselect(
            "🏷️ 按标签筛选",
            options=sorted(list(all_tags)) if all_tags else [],
            default=[],
            placeholder="选择标签进行筛选",
        )
    with col2:
        status_filter = st.radio(
            "🔄 状态筛选", ["全部", "进行中", "已结束", "过期"], horizontal=True
        )

    # 准备表格数据
    data = [
        prepare_question_data(q, selected_tags, status_filter, current_user)
        for q in questions
    ]
    data = [d for d in data if d is not None]

    # 创建并显示表格
    df = pd.DataFrame(data)
    has_ended_questions = any(q.get("result") for q in questions)
    column_config = get_column_config(has_ended_questions)

    # 显示表格并处理点击事件
    selected_rows = st.dataframe(
        df, column_config=column_config, use_container_width=True, hide_index=True
    )

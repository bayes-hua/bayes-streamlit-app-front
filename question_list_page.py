import streamlit as st
import pandas as pd


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

    selected_tags = []  # 删除这行，因为前面已经定义过了
    # 添加标签筛选
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.tags:
            selected_tags = st.multiselect(
                "🏷️ 按标签筛选", options=sorted(list(st.session_state.tags))
            )
    with col2:
        status_filter = st.radio(
            "🔄 状态筛选", ["全部", "进行中", "已结束", "过期"], horizontal=True
        )

    # 准备表格数据
    data = []
    for q in st.session_state.questions:
        # 如果选择了标签筛选，检查问题是否包含所选标签
        if selected_tags and not any(tag in q.get("tags", []) for tag in selected_tags):
            continue

        # 状态筛选
        if status_filter == "进行中" and ("winner" in q or q.get("winner") == "过期"):
            continue
        if status_filter == "已结束" and (
            "winner" not in q or q.get("winner") == "过期"
        ):
            continue
        if status_filter == "过期" and q.get("winner") != "过期":
            continue

        # 计算总投票数
        total_positions = 0
        if q["id"] in st.session_state.positions:
            total_positions = sum(st.session_state.positions[q["id"]].values())

        # 获取最高概率的选项
        max_probability_option = max(q["probabilities"].items(), key=lambda x: x[1])

        # 基础数据字典
        question_data = {
            "标题": q["title"],
            "状态": (
                "过期"
                if q.get("winner") == "过期"
                else ("已结束" if "winner" in q else "进行中")
            ),
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
            question_data["胜出选项"] = q["winner"]
            question_data["结束用户"] = q.get("end_by", "未知")
            question_data["结束时间"] = q["end_at"].strftime("%Y-%m-%d %H:%M")

        # 将数据添加到列表中
        data.append(question_data)

    # 更新表格配置
    df = pd.DataFrame(data)
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

    # 添加结束相关列的配置
    if "结束用户" in df.columns:
        column_config["结束用户"] = st.column_config.TextColumn("👤 结束用户")
        column_config["结束时间"] = st.column_config.TextColumn("⏰ 结束时间")
        column_config["胜出选项"] = st.column_config.TextColumn("🏆 胜出选项")

    st.dataframe(
        df, column_config=column_config, use_container_width=True, hide_index=True
    )

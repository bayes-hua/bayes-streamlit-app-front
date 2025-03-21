import streamlit as st
import pandas as pd

# 问题列表页面
def question_list_page():
    st.subheader("⚙️ 问题列表")
    
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
    if st.session_state.tags:
        selected_tags = st.multiselect(
            "🏷️ 按标签筛选",
            options=sorted(list(st.session_state.tags))
        )
    
    # 准备表格数据
    data = []
    for q in st.session_state.questions:
        # 如果选择了标签筛选，检查问题是否包含所选标签
        if selected_tags and not any(tag in q.get('tags', []) for tag in selected_tags):
            continue
            
        # 计算总投票数
        total_positions = 0
        if q['id'] in st.session_state.positions:
            total_positions = sum(st.session_state.positions[q['id']].values())
            
        # 获取最高概率的选项
        max_probability_option = max(q['probabilities'].items(), key=lambda x: x[1])
        
        data.append({
            "标题": q['title'],
            "类型": q['type'],
            "用户":  q['create_by'],
            "创建时间": q['created_at'].strftime('%Y-%m-%d %H:%M'),
            "选项": ", ".join(q['outcomes']),
            "总投票数": f"{total_positions:.2f}",
            "领先选项": max_probability_option[0],
            "领先概率": f"{max_probability_option[1]:.1%}",
            "标签": ", ".join(q.get('tags', [])),
        })
    
    # 更新表格配置
    df = pd.DataFrame(data)
    st.dataframe(
        df,
        column_config={
            "标题": st.column_config.TextColumn("📝 标题"),
            "类型": st.column_config.TextColumn("📊 类型"),
            "用户": st.column_config.TextColumn("👤 用户"),
            "创建时间": st.column_config.TextColumn("🕒 创建时间"),
            "选项": st.column_config.TextColumn("📊 选项"),
            "总投票数": st.column_config.TextColumn("📈 总投票数"),
            "领先选项": st.column_config.TextColumn("🥇 领先选项"),
            "领先概率": st.column_config.TextColumn("💯 领先概率"),
            "标签": st.column_config.TextColumn("🏷️ 类型")
        },
        use_container_width=True,
        hide_index=True
    )

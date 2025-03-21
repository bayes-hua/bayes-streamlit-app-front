import streamlit as st
import pandas as pd
from datetime import datetime
import uuid

# 计算新的概率值
def calculate_new_probability(current_probability, amount, is_vote=True, all_probabilities=None, selected_outcome=None):
    """计算新的概率值"""
    if all_probabilities is None or selected_outcome is None:
        return current_probability
        
    # 计算当前选项的变化量
    change = amount * 0.01
    new_probability = current_probability + change if is_vote else current_probability - change
    new_probability = max(0.01, min(0.99, new_probability))
    
    # 计算其他选项需要调整的总量
    total_adjustment = new_probability - current_probability
    
    # 按比例调整其他选项的概率
    other_probabilities = {k: v for k, v in all_probabilities.items() if k != selected_outcome}
    total_other = sum(other_probabilities.values())
    
    if total_other > 0:
        for outcome in other_probabilities:
            ratio = other_probabilities[outcome] / total_other
            all_probabilities[outcome] -= total_adjustment * ratio
            all_probabilities[outcome] = max(0.01, min(0.99, all_probabilities[outcome]))
    
    return new_probability


# 投票平台页面
def voting_platform_page():
    st.subheader("🎲 参与投票")
    
    # 添加返回按钮
    if st.button("👈 返回管理页面", use_container_width=True):
        st.session_state.page = "question_list_page"
        st.rerun()

    # 检查是否有可用的问题
    if not st.session_state.questions:
        st.warning("目前没有可用的问题")
        return
    
    # 选择问题
    question_titles = [m['title'] for m in st.session_state.questions]
    selected_question_title = st.selectbox("选择问题", question_titles)
    
    # 获取选中的问题
    question = next(m for m in st.session_state.questions if m['title'] == selected_question_title)

    # 显示问题信息
    with st.container(border=True):
        st.markdown("**📋 问题详情**")
        
        # 使用列布局显示基本信息
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**📊 类型:** {question['type']}")
        with col2:
            st.info(f"**🕒 创建时间:** {question['created_at'].strftime('%Y-%m-%d %H:%M')}")
        
        # 显示规则
        st.markdown("**📜 规则:**")
        st.info(question['rules'])

        # 使用表格显示当前选项
        st.markdown("**📈 当前选项概率:**")
        data = []
        for outcome, probability in question['probabilities'].items():  # 改为 probability
            data.append({"选项": outcome, "概率": f"{probability:.1%}"})
        df = pd.DataFrame(data)
        st.table(df)
        
        # 显示当前当前票数信息
        question_id = question['id']
        if question_id in st.session_state.positions:
            st.markdown("**💰 当前票数:**")
            positions_data = []
            for outcome, quantity in st.session_state.positions[question_id].items():
                positions_data.append({"选项": outcome, "票数": f"{quantity:.2f}"})
            positions_df = pd.DataFrame(positions_data)
            st.table(positions_df)

    # 交易部分
    with st.container(border=True):
        st.markdown("***🗳️ 投票***")
        vote_type = st.selectbox("操作", ["投票", "撤票"], key="vote_type",index=0)
        amount = float('inf')
        selected_outcome = question['outcomes'][0]
        min_quantity = float('inf')
        current_probability = question['probabilities'][selected_outcome]
        new_probability = current_probability
        
        if vote_type == "投票":
            col1, col2 = st.columns(2)
            with col1:
                selected_outcome = st.selectbox("选择选项", question["outcomes"], key="selected_outcome",index=0)
            with col2:
                amount = st.number_input("票数", min_value=0.1, step=0.1, key="amount",format="%.2f")
        else:
            # 取出时计算可取出票数
            min_quantity = float('inf')
            if question_id in st.session_state.positions:
                for outcome in question['outcomes']:
                    quantity = st.session_state.positions[question_id].get(outcome, 0)
                    min_quantity = min(min_quantity, quantity)
                
                if min_quantity > 0:
                    amount = st.number_input(f"可撤票数: {min_quantity:.2f}", min_value=0.1, step=0.1,max_value=min_quantity, key="amount",format="%.2f")
                else:
                    st.write("❌ 需要持有所有选项才能撤票")
            else:
                st.write("❌ 您还没有投过票")
                min_quantity = 0
        
        col1, col2 = st.columns(2)
        # 预估按钮
        with col1:
            if st.button("预估结果", use_container_width=True):
                if vote_type == "投票":
                    new_probability = calculate_new_probability(
                        current_probability, 
                        amount, 
                        True,
                        question['probabilities'].copy(),
                        selected_outcome
                    )
                    st.info(f"预计概率将从 {current_probability:.1%} 变为 {new_probability:.1%}")
                elif min_quantity > 0:
                    new_probability = calculate_new_probability(
                        current_probability, 
                        amount, 
                        False,
                        question['probabilities'].copy(),
                        selected_outcome
                    )
                    st.error(f"预计概率将从 {current_probability:.1%} 变为 {new_probability:.1%}")

        # 投票按钮
        with col2:
            if st.button("执行", use_container_width=True):
                is_ok = True
                if vote_type == "投票":
                    # 更新持仓信息
                    if question_id not in st.session_state.positions:
                        st.session_state.positions[question_id] = {}
                    st.session_state.positions[question_id][selected_outcome] = st.session_state.positions[question_id].get(selected_outcome, 0) + amount
                    
                    # 更新问题概率
                    current_probability = question['probabilities'][selected_outcome]
                    new_probability = calculate_new_probability(
                        current_probability, 
                        amount, 
                        True,
                        question['probabilities'],
                        selected_outcome
                    )
                    question['probabilities'][selected_outcome] = new_probability
                    st.toast("✅ 投票成功！", icon="🎯")
                    # 记录投票历史
                    vote_record = {
                        "id": str(uuid.uuid4()),
                        "question_id": question_id,
                        "outcome": selected_outcome,
                        "amount": amount,
                        "type": vote_type,
                        "probability": new_probability - current_probability,
                        "timestamp": datetime.now(),
                        "create_by": st.session_state.username,
                    }
                    st.session_state.vote_history.append(vote_record)
                    st.rerun()
                else:
                    # 检查是否持有所有选项
                    if question_id not in st.session_state.positions:
                        st.toast("❌ 您还没有持有任何选项", icon="⚠️")
                        is_ok = False
                    if is_ok:   
                        min_quantity = float('inf')
                        for outcome in question['outcomes']:
                            quantity = st.session_state.positions[question_id].get(outcome, 0)
                            min_quantity = min(min_quantity, quantity)
                        
                        if min_quantity == 0:
                            st.toast("❌ 取出需要持有所有选项", icon="⚠️")
                            is_ok = False
                        elif amount > min_quantity:
                            st.toast(f"❌ 最大可取出票数为: {min_quantity:.2f}", icon="⚠️")
                            is_ok = False
                        if is_ok:
                            # 更新问题概率
                            for outcome in question['outcomes']:
                                st.session_state.positions[question_id][outcome] -= amount
                                current_probability = question['probabilities'][outcome]
                                new_probability = calculate_new_probability(
                                    current_probability, 
                                    amount, 
                                    False,  # 撤票时设置为 False
                                    question['probabilities'],
                                    outcome
                                )
                                question['probabilities'][outcome] = new_probability # 更新所有选项的持仓
                                prob_change = question['probabilities'][outcome] - (
                                    question['probabilities'][outcome] + amount * 0.01
                                )
                                vote_record = {   # 记录投票历史
                                    "id": str(uuid.uuid4()),
                                    "question_id": question_id,
                                    "outcome": outcome,
                                    "amount": amount,
                                    "type": vote_type,
                                    "probability": prob_change,
                                    "timestamp": datetime.now(),
                                    "create_by": st.session_state.username,
                                }
                                st.session_state.vote_history.append(vote_record)
                                    
                            st.toast("✅ 撤票成功！", icon="🎯")
                            st.rerun()


    # 历史记录显示部分修改
    with st.container(border=True):
        st.markdown("**📜 投票历史记录**")
        
        # 筛选当前问题的投票记录
        question_votes = [
            vote for vote in st.session_state.vote_history 
            if vote['question_id'] == question_id
        ]
        
        if question_votes:
            votes_data = []
            for vote in sorted(question_votes, key=lambda x: x['timestamp'], reverse=True):
                votes_data.append({
                    "时间": vote['timestamp'].strftime('%Y-%m-%d %H:%M'),
                    "操作": vote['type'],
                    "选项": vote['outcome'],
                    "票数": f"{vote['amount']:.2f}",
                    "概率": f"{vote['probability']:.1%}",
                    "用户": vote['create_by']
                })
            
            votes_df = pd.DataFrame(votes_data)
            st.dataframe(
                votes_df,
                column_config={
                    "时间": st.column_config.TextColumn("🕒 时间"),
                    "操作": st.column_config.TextColumn("📝 操作"),
                    "选项": st.column_config.TextColumn("🎯 选项"),
                    "票数": st.column_config.TextColumn("📊 票数"),
                    "概率": st.column_config.TextColumn("💯 概率变化"),
                    "用户": st.column_config.TextColumn("👤 用户")
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("暂无投票记录")


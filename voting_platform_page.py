import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
from data import save_session_data

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

# 显示问题详情
def display_question_info(question):
    """显示问题详情"""
    question_id = question['id']
    st.markdown("**📋 问题详情**")
    st.markdown(f"**📊 类型:** {question['type']}")
    st.markdown(f"**📂 标签:** {', '.join(question.get('tags', []))}")
    st.markdown(f"**👤 创建者:** {question['create_by']}")
    st.markdown(f"**🕒 时间:** {question['created_at'].strftime('%Y-%m-%d %H:%M')} - {question['expire_at'].strftime('%Y-%m-%d %H:%M')}")
    if 'winner' in question:
        st.markdown(f"**🏆 已结束 - 胜出: {question['winner']}**")
        st.markdown(f"**⏰ 结束时间:** {question['end_at'].strftime('%Y-%m-%d %H:%M')}")
        if 'end_by' in question:
            st.markdown(f"**👤 结束用户:** {question['end_by']}")

    st.markdown("**📜 规则:**")
    st.markdown(question['rules'])
    st.markdown("**📈 选项状态:**")
    data = []
    for outcome, probability in question['probabilities'].items():
        row_data = {
            "选项": outcome,
            "概率": f"{probability:.1%}",
            "票数": f"{st.session_state.positions.get(question_id, {}).get(outcome, 0):.2f}"
        }
        data.append(row_data)
    df = pd.DataFrame(data)
    st.dataframe(df, hide_index=True)

# 显示投票历史
def display_voting_history(question_id):
    """显示投票历史"""
    st.markdown("**📜 投票历史记录**")
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
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("暂无投票记录")

# 处理投票操作
def handle_voting_operation(question):
    """处理投票操作"""
    question_id = question['id']
    st.markdown("**🗳️ 投票操作**")
    vote_type = st.radio("选择操作", ["投票", "撤票"], horizontal=True,
                        help="投票：增加选项的概率；撤票：减少选项的概率")

    selected_outcome = None
    amount = 0
    min_quantity = 0

    if vote_type == "投票":
        col1, col2 = st.columns(2)
        with col1:
            selected_outcome = st.selectbox(
                "选择投票选项",
                question["outcomes"],
                format_func=lambda x: f"{x} (当前概率: {question['probabilities'][x]:.1%})"
            )
        with col2:
            amount = st.number_input(
                "投票数量",
                min_value=0.1,
                step=0.1,
                format="%.1f",
                help="每票将使选项概率增加约1%"
            )
    else:
        if question_id not in st.session_state.positions:
            st.warning("❌ 您还没有投过票")
            min_quantity = 0
        else:
            positions = st.session_state.positions[question_id]
            if not positions:
                st.warning("❌ 您还没有持有任何选项")
                min_quantity = 0
            else:
                min_quantity = min(positions.values()) if positions else 0
                if min_quantity > 0:
                    st.info(f"💰 可撤票数量：{min_quantity:.2f} 票")
                    amount = st.number_input(
                            "撤票数量",
                            min_value=0.1,
                            max_value=float(min_quantity),
                            step=0.1,
                            format="%.1f",
                            help="每票将使所有选项概率减少约1%"
                        )
                    col1, col2 = st.columns(2)
                else:
                    st.error("❌ 需要持有所有选项才能撤票")

    # 操作按钮
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👀 预估结果", use_container_width=True):
            if vote_type == "投票":
                current_probability = question['probabilities'][selected_outcome]
                new_probability = calculate_new_probability(
                    current_probability,
                    amount,
                    True,
                    question['probabilities'].copy(),
                    selected_outcome
                )
                st.info(f"预计 {selected_outcome} 概率: {current_probability:.1%} → {new_probability:.1%}")
            elif min_quantity > 0:
                changes = [f"{outcome}: {question['probabilities'][outcome]:.1%} → {calculate_new_probability(question['probabilities'][outcome], amount, False, question['probabilities'].copy(), outcome):.1%}" for outcome in question['outcomes']]
                st.warning("预计概率变化: " + " | ".join(changes))

    with col2:
        if st.button("✅ 确认执行", type="primary", use_container_width=True):
            is_ok = True
            if vote_type == "投票":
                if question_id not in st.session_state.positions:
                    st.session_state.positions[question_id] = {}
                st.session_state.positions[question_id][selected_outcome] = st.session_state.positions[question_id].get(selected_outcome, 0) + amount

                current_probability = question['probabilities'][selected_outcome]
                new_probability = calculate_new_probability(
                    current_probability,
                    amount,
                    True,
                    question['probabilities'],
                    selected_outcome
                )
                question['probabilities'][selected_outcome] = new_probability
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
                save_session_data()
                st.toast("✅ 投票成功！", icon="🎯")
            else:
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
                        for outcome in question['outcomes']:
                            st.session_state.positions[question_id][outcome] -= amount
                            current_probability = question['probabilities'][outcome]
                            new_probability = calculate_new_probability(
                                current_probability,
                                amount,
                                False,
                                question['probabilities'],
                                outcome
                            )
                            question['probabilities'][outcome] = new_probability
                            prob_change = question['probabilities'][outcome] - (
                                question['probabilities'][outcome] + amount * 0.01
                            )
                            vote_record = {
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
                        save_session_data()
                        st.toast("✅ 撤票成功！", icon="🎯")

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

    # 添加状态筛选
    status_filter = st.radio(
        "🔄 状态筛选",
        ["全部", "进行中", "已结束", "过期"],
        horizontal=True
    )

    # 根据筛选条件过滤问题
    filtered_questions = st.session_state.questions
    if status_filter == "进行中":
        filtered_questions = [q for q in filtered_questions if 'winner' not in q]
    elif status_filter == "已结束":
        filtered_questions = [q for q in filtered_questions if 'winner' in q and q.get('winner') != '过期']
    elif status_filter == "过期":
        filtered_questions = [q for q in filtered_questions if q.get('winner') == '过期']

    # 选择问题
    questions_with_status = {
        f"{m['title']} {'[过期]' if m.get('winner') == '过期' else '[已结束]' if 'winner' in m else ''}": m
        for m in filtered_questions
    }

    if not questions_with_status:
        st.warning("没有符合条件的问题")
        return

    selected_question_title = st.selectbox("选择问题", list(questions_with_status.keys()))

    # 直接从字典中获取选中的问题
    question = questions_with_status[selected_question_title]

    # 显示问题信息
    with st.container(border=True):
      display_question_info(question)

    # 只在问题未结束时显示投票操作
    if 'winner' not in question:
        # 结束问题的expander
        with st.expander("🔒 结束问题"):
            st.write("**请选择胜出选项并输入结束密码**")
            winner = st.selectbox("胜出选项", question["outcomes"])
            end_user = st.text_input("结束用户", value=st.session_state.username)
            password = st.text_input("结束密码", type="password")
            if st.button("确认结束"):
                if password == question.get('end_password', ''):
                    question['winner'] = winner
                    question['end_at'] = datetime.now()
                    question['end_by'] = end_user
                    save_session_data()
                    st.toast(f"问题已结束，胜出选项：{winner}")
                    st.rerun()
                else:
                    st.error("密码错误")

    # 交易部分
    if 'winner' not in question:
      with st.container(border=True):
         handle_voting_operation(question)

    # 显示投票历史
    with st.container(border=True):
        display_voting_history( question['id'])


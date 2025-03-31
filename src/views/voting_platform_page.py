import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
from models.votes import create_vote, get_question_votes
from models.questions import list_questions, end_question,update_question_probabilities
from models.positions import get_positions, update_position

# 计算新的概率值
def calculate_new_probability(
    current_probability,
    amount,
    is_vote=True,
    all_probabilities=None,
    selected_option=None,
):
    """计算新的概率值"""
    if all_probabilities is None or selected_option is None:
        return current_probability

    # 计算当前选项的变化量
    change = amount * 0.01
    new_probability = (
        current_probability + change if is_vote else current_probability - change
    )
    new_probability = max(0.01, min(0.99, new_probability))

    # 计算其他选项需要调整的总量
    total_adjustment = new_probability - current_probability

    # 按比例调整其他选项的概率
    other_probabilities = {
        k: v for k, v in all_probabilities.items() if k != selected_option
    }
    total_other = sum(other_probabilities.values())

    if total_other > 0:
        for option in other_probabilities:
            ratio = other_probabilities[option] / total_other
            all_probabilities[option] -= total_adjustment * ratio
            all_probabilities[option] = max(
                0.01, min(0.99, all_probabilities[option])
            )

    return new_probability


# 显示问题详情
def display_question_info(question):
    """显示问题详情"""
    question_id = question["id"]
    st.markdown("**📋 问题详情**")
    st.markdown(f"**📊 类型:** {question['type']}")
    st.markdown(f"**📂 标签:** {question.get('tags', '')}")
    st.markdown(f"**👤 创建者:** {question['created_by']}")
    st.markdown(
        f"**🕒 时间:** {datetime.fromisoformat(question["created_at"]).strftime("%Y-%m-%d %H:%M")} - {datetime.fromisoformat(question["expire_at"]).strftime("%Y-%m-%d %H:%M")}"
    )
    if question.get('result'):
        st.markdown(f"**🏆 已结束 - 胜出: {question['result']}**")
        st.markdown(f"**⏰ 结束时间:** {datetime.fromisoformat(question["end_at"]).strftime("%Y-%m-%d %H:%M")}")

    st.markdown("**📜 规则:**")
    st.markdown(question.get("rule", "暂无规则"))
    st.markdown("**📈 选项状态:**")

    data = []
    options = question["options"].split(",")
    probabilities = [float(p) for p in question["probabilities"].split(",")]

    # 获取该问题的所有投票记录
    votes = get_question_votes(question_id)
    vote_counts = {}
    for vote in votes:
        vote_counts[vote["option"]] = vote_counts.get(vote["option"], 0) + vote["vote"]

    for option, probability in zip(options, probabilities):
        row_data = {
            "选项": option,
            "概率": f"{probability:.1%}",
            "票数": f"{vote_counts.get(option, 0):.2f}",
        }
        data.append(row_data)
    df = pd.DataFrame(data)
    st.dataframe(df, hide_index=True)


# 显示投票历史
def display_voting_history(question_id):
    """显示投票历史"""
    st.markdown("**📜 投票历史记录**")
    question_votes = get_question_votes(question_id)

    if question_votes:
        votes_data = []
        for vote in question_votes:
            votes_data.append(
                {
                    "时间": datetime.fromisoformat(vote["created_at"]).strftime("%Y-%m-%d %H:%M"),
                    "用户": vote["username"],
                    "选项": vote["option"],
                    "票数": f"{vote['vote']:.2f}",
                    "概率": f"{vote['probability']:.1%}",
                }
            )
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
            hide_index=True,
        )
    else:
        st.info("暂无投票记录")


# 处理投票操作
def handle_voting_operation(question):
    """处理投票操作"""
    question_id = question["id"]
    st.markdown("**🗳️ 投票操作**")

    # 获取选项和概率
    options = question["options"].split(",")
    probabilities = [float(p) for p in question["probabilities"].split(",")]
    options_with_prob = {opt: prob for opt, prob in zip(options, probabilities)}

    # 获取用户持仓
    positions = get_positions(question_id, st.session_state.username)
    position_values = {opt: 0 for opt in options}

    if positions.get(st.session_state.username):
        position_parts = positions[st.session_state.username].split(",")
        for i, opt in enumerate(options):
            if i < len(position_parts) and position_parts[i]:
                try:
                    position_values[opt] = float(position_parts[i])
                except ValueError:
                    position_values[opt] = 0

    # 为每个选项创建操作区域
    amounts = {}
    vote_types = {}
    for option in options:
        with st.container(border=True):
            st.markdown(f"**{option}** (当前概率: {options_with_prob[option]:.1%}, 持有: {position_values.get(option, 0):.2f})")

            # 使用列将操作选择和数量输入放在同一行
            col1, col2 = st.columns([2, 3])
            with col1:
                vote_types[option] = st.radio(
                    "操作类型",
                    ["yes", "no"],
                    horizontal=True,
                    help="yes：增加选项的概率；no：减少选项的概率",
                    key=f"vote_type_{option}"
                )
            with col2:
                if vote_types[option] == "yes":
                    amounts[option] = st.number_input(
                        "投票数量",
                        min_value=0.0,
                        max_value=100.0,
                        step=0.1,
                        value=0.0,
                        format="%.1f",
                        help="每票将改变选中选项概率约1%",
                        key=f"vote_amount_{option}"
                    )
                else:
                    available_quantity = position_values.get(option, 0)
                    amounts[option] = st.number_input(
                        "撤票数量",
                        min_value=0.0,
                        max_value=float(available_quantity),
                        step=0.1,
                        value=0.0,
                        format="%.1f",
                        help=f"最多可撤 {available_quantity:.1f} 票",
                        key=f"withdraw_amount_{option}",
                        disabled=available_quantity <= 0
                    )
                    if available_quantity <= 0:
                        st.warning(f"您没有持有选项 {option} 的票")

    # 操作按钮
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👀 预估结果", use_container_width=True):
            probabilities_dict = dict(zip(options, probabilities))
            for option, amount in amounts.items():
                if amount > 0:
                    current_prob = probabilities_dict[option]
                    new_prob = calculate_new_probability(
                        current_prob,
                        amount,
                        vote_types[option] == "yes",
                        probabilities_dict.copy(),
                        option,
                    )
                    probabilities_dict[option] = new_prob

            st.session_state.prediction_result = probabilities_dict
            st.session_state.show_prediction = not st.session_state.show_prediction
            st.rerun()

    with col2:
        if st.button("✅ 执行操作", use_container_width=True):
            probabilities_dict = dict(zip(options, probabilities))
            for option, amount in amounts.items():
                if amount > 0:
                    if vote_types[option] == "no" and position_values.get(option, 0) < amount:
                        st.toast(f"❌ 撤票数量不能超过持有量 {position_values.get(option, 0):.1f}", icon="⚠️")
                        return

                    current_prob = probabilities_dict[option]
                    new_prob = calculate_new_probability(
                        current_prob,
                        amount,
                        vote_types[option] == "yes",
                        probabilities_dict,
                        option,
                    )

                    # 更新概率
                    prob_change = amount * 0.01 if vote_types[option] == "yes" else -amount * 0.01
                    if not update_question_probabilities(question_id, option, prob_change):
                        st.error(f"❌ 更新选项 {option} 概率失败")
                        return

                    # 更新持仓
                    position_values[option] += amount if vote_types[option] == "yes" else -amount

            # 更新所有持仓
            position_str = ",".join([str(position_values.get(opt, 0)) for opt in options])
            if not update_position(question_id, st.session_state.username, position_str):
                st.error("❌ 更新持仓失败")
                return

            # 记录投票
            for option, amount in amounts.items():
                if amount > 0:
                    vote_amount = amount if vote_types[option] == "yes" else -amount
                    if not create_vote(question_id, st.session_state.username, vote_amount, option, probabilities_dict[option]):
                        st.error(f"❌ 记录选项 {option} 投票失败")
                        return

            st.toast(f"✅ 操作成功: 投票/撤票完成", icon="🎯")
            st.session_state.show_prediction = False
            st.rerun()

    # 显示预估结果
    if st.session_state.show_prediction and st.session_state.prediction_result:
        with st.container(border=True):
            st.markdown("**🔮 预估结果**")
            pred_data = [{
                "选项": opt,
                "预估概率": f"{st.session_state.prediction_result.get(opt, 0):.1%}"
            } for opt in options]
            st.dataframe(pd.DataFrame(pred_data), hide_index=True)

# 根据状态筛选问题
def filter_questions_by_status(questions, status_filter):
    """根据状态筛选问题"""
    if status_filter == "进行中":
        return [q for q in questions if q.get("status") == "progress"]
    elif status_filter == "已结束":
        return [q for q in questions if q.get("status") == "ended"]
    elif status_filter == "过期":
        return [q for q in questions if q.get("status") == "expired"]
    return questions

# 创建问题选择字典
def create_question_selection_dict(filtered_questions):
    """创建问题选择字典"""
    return {
        f"{q['question']} {'[过期]' if q.get('status') == 'expired' else '[已结束]' if q.get('status') == 'ended' else ''}": q
        for q in filtered_questions
    }

# 处理结束问题操作
def handle_end_question(question):
    """处理结束问题操作"""
    with st.expander("🔒 结束问题"):
        st.write("**请选择胜出选项**")
        result = st.selectbox("胜出选项", question["options"].split(","))
        if st.button("确认结束"):
            if st.session_state.username == question["created_by"]:
                if end_question(question["id"], result, st.session_state.username):
                    question["result"] = result
                    question["end_at"] = datetime.now()
                    question["end_by"] = st.session_state.username
                    st.toast(f"问题已结束，胜出选项：{result}")
                    # st.rerun()
                else:
                    st.error("结束问题失败，请稍后重试")
            else:
                st.error("只有问题创建者可以结束问题")

# 投票平台页面
def voting_platform_page():
    """投票平台页面"""
    # 初始化 session_state 变量
    if "show_prediction" not in st.session_state:
        st.session_state.show_prediction = False
    if "prediction_result" not in st.session_state:
        st.session_state.prediction_result = None

    questions = list_questions()
    if not questions:
        st.warning("目前没有可用的问题")
        return

    # 添加状态筛
    status_filter = st.radio(
        "🔄 状态筛选", ["全部", "进行中", "已结束", "过期"], horizontal=True
    )

    # 筛选问题
    filtered_questions = filter_questions_by_status(questions, status_filter)
    questions_with_status = create_question_selection_dict(filtered_questions)

    if not questions_with_status:
        st.warning("没有符合条件的问题")
        return

    # 选择问题
    selected_question_title = st.selectbox("选择问题", list(questions_with_status.keys()))
    question = questions_with_status[selected_question_title]

    # 显示问题信息
    with st.container(border=True):
        display_question_info(question)

    # 处理未结束问题的操作
    if question.get("status") == "progress":
        if st.session_state.username == question["created_by"]: handle_end_question(question)
        with st.container(border=True):
            handle_voting_operation(question)

    # 显示投票历史
    with st.container(border=True):
        display_voting_history(question["id"])

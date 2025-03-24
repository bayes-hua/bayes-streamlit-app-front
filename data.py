import streamlit as st
import json
from datetime import datetime
file_name = 'session_data.json'

# 解析 datetime 字符串
def parse_datetime(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str) and 'T' in value:
                try:
                    data[key] = datetime.fromisoformat(value)
                except ValueError:
                    pass
            elif isinstance(value, (dict, list)):
                parse_datetime(value)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, (dict, list)):
                parse_datetime(item)
    return data

# 初始化 session state
def init_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = True
    if 'username' not in st.session_state:
        st.session_state.username = 'system'
    if 'role' not in st.session_state:
        st.session_state.role = 'user'
    if 'page' not in st.session_state:
        st.session_state.page = "login_page"

    # 从文件加载持久化数据
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            data = json.load(f)
            data = parse_datetime(data)
            st.session_state.questions = data.get('questions', [])  # type: ignore
            st.session_state.positions = data.get('positions', {})  # type: ignore
            st.session_state.tags = set(data.get('tags', []))  # type: ignore
            st.session_state.vote_history = data.get('vote_history', [])  # type: ignore
    except FileNotFoundError:
        # 如果文件不存在，使用默认值
        if 'questions' not in st.session_state:
            st.session_state.questions = []
        if 'positions' not in st.session_state:
            st.session_state.positions = {}
        if 'tags' not in st.session_state:
            st.session_state.tags = set()
        if 'vote_history' not in st.session_state:
            st.session_state.vote_history = []

# 序列化 datetime 和 set 类型
def serialize_data(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, set):
        return list(obj)
    elif isinstance(obj, dict):
        return {k: serialize_data(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_data(item) for item in obj]
    return obj

# 保存 session state 到文件
def save_session_data():
    data = {
        'questions': serialize_data(st.session_state.questions),
        'positions': serialize_data(st.session_state.positions),
        'tags': serialize_data(st.session_state.tags),
        'vote_history': serialize_data(st.session_state.vote_history)
    }
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 检查过期问题
def check_expired_questions():
    """检查并处理过期问题"""
    current_time = datetime.now()
    for question in st.session_state.questions:
        if 'end_at' in question and current_time > question['end_at']:
            if 'winner' not in question:  # 只处理未结束的过期问题
                # 重置概率为初始值
                total_outcomes = len(question['outcomes'])
                initial_probability = 1.0 / total_outcomes
                question['probabilities'] = {outcome: initial_probability for outcome in question['outcomes']}

                # 设置过期状态
                question['winner'] = '过期'
                question['end_by'] = '过期'
                question['end_at'] = current_time
    save_session_data()
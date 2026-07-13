"""🎭 八仙辩论 Demo"""

import streamlit as st
import openai
import os

st.set_page_config(page_title="记忆银行 · 八仙辩论", page_icon="🎭", layout="wide")

st.markdown("# 🎭 八仙辩论 · 智能体演绎")

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://litellm.git4ta.fun/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-47318")
DEBATE_MODEL = os.getenv("DEBATE_MODEL", "tencent/hy3:free")

IMMORTALS = {
    "吕洞宾": "剑仙，代表批判精神，专长逻辑拆解与归谬。",
    "铁拐李": "医仙，代表实用主义，关注理论能否落地。",
    "何仙姑": "慧仙，代表直觉智慧，长于洞察隐喻。",
    "韩湘子": "文仙，代表人文关怀，关注技术与人的关系。",
}

TOPICS = {
    "记忆的本质是什么": "从《记忆的边界》出发：记忆是存储还是重构？",
    "AI 是否该有长期记忆": "从《智能体的觉醒》出发：记忆权是否是基本权利？",
    "链上存证的意义": "从《深度发布》出发：确权是否等于垄断？",
    "文明会走向何方": "从《文明的重构》出发：技术文明 vs 人文文明",
}

with st.sidebar:
    st.markdown("### 🎭 辩论设置")
    selected_topic = st.selectbox("选择辩题", list(TOPICS.keys()))
    st.caption(TOPICS[selected_topic])
    selected_immortals = st.multiselect(
        "选择辩手", list(IMMORTALS.keys()), default=list(IMMORTALS.keys())
    )
    debate_rounds = st.slider("辩论轮数", 1, 5, 2)
    start_btn = st.button("🎬 开始辩论", type="primary", use_container_width=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

def get_prompt(topic, immortal, desc, round_num, history):
    return f"""你是辩论选手：{immortal}（{desc}）。
辩题：{topic}。第{round_num}轮。
历史：{history}
请以{immortal}风格发言，不超200字。"""

if start_btn and selected_immortals:
    st.session_state.messages = []
    placeholder = st.empty()
    for r in range(1, debate_rounds + 1):
        for im in selected_immortals:
            history = "\n".join(f"{m['role']}: {m['content']}" for m in st.session_state.messages[-4:])
            prompt = get_prompt(selected_topic, im, IMMORTALS[im], r, history)
            with placeholder.container():
                with st.chat_message(im, avatar="🎭"):
                    with st.spinner(f"{im} 思考中..."):
                        try:
                            client = openai.OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)
                            resp = client.chat.completions.create(model=DEBATE_MODEL, messages=[{"role": "user", "content": prompt}], timeout=30)
                            content = resp.choices[0].message.content
                        except Exception as e:
                            content = f"（{im} 暂时无法回答）"
                    st.markdown(f"**{im}**（第{r}轮）")
                    st.markdown(content)
            st.session_state.messages.append({"role": im, "content": content})
    placeholder.empty()
    st.success("辩论结束！")

st.divider()
st.markdown("← [返回首页](/)")

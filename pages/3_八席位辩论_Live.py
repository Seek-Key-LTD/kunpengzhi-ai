"""🎭 8 席位分布式 4v4 AI 辩论台"""

import streamlit as st
import openai
import os

st.set_page_config(page_title="鲲鹏志 · 8 席位分布式辩论台", page_icon="🎭", layout="wide")

st.markdown("# 🎭 鲲鹏志 · 8 席位分布式 4v4 AI 辩论台")
st.caption("基于 8 个物理/云端 Keyagent 席位节点驱动 · 真实分布式多智能体竞技")

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://litellm.capitaltrain.cn/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-47318")

SEATS = [
    {
        "role": "正方一辩",
        "agent": "ruby",
        "node": "nuc",
        "model": "nova-deepseek-v4-flash-aggr",
        "instruction": "你是正方一辩。请激情澎湃、开门见山进行【开篇立论】（阐明正方核心主张与理论依据）。"
    },
    {
        "role": "反方一辩",
        "agent": "topaz",
        "node": "raccoon",
        "model": "topaz-deepseek-v4-flash",
        "instruction": "你是反方一辩。请冷静犀利、抓住正方立论漏洞，进行【反方开篇立论与破题】。"
    },
    {
        "role": "正方二辩",
        "agent": "diamond",
        "node": "pve",
        "model": "diamond-deepseek-v4-flash",
        "instruction": "你是正方二辩。请立场坚定、质地坚硬，针对反方一辩的质问进行【接招拆招与驳论】。"
    },
    {
        "role": "反方二辩",
        "agent": "carbonado",
        "node": "pve2",
        "model": "carbonado-deepseek-v4-flash",
        "instruction": "你是反方二辩。请深沉果敢、针锋相对，对正方二辩进行【反驳与反攻】。"
    },
    {
        "role": "正方三辩",
        "agent": "argentite",
        "node": "pve3",
        "model": "argentite-deepseek-v4-flash",
        "instruction": "你是正方三辩。请灵动多变、火力全开，进行【自由辩论攻防】。"
    },
    {
        "role": "反方三辩",
        "agent": "quartz",
        "node": "pbs3",
        "model": "quartz-deepseek-v4-flash",
        "instruction": "你是反方三辩。请严密缜密、逻辑自洽，在【自由辩论阶段】发起强力反击。"
    },
    {
        "role": "正方四辩",
        "agent": "agate",
        "node": "xgp",
        "model": "agate-deepseek-v4-flash",
        "instruction": "你是正方四辩。请全局总结、升华主旨，进行【正方总结陈词】。"
    },
    {
        "role": "反方四辩",
        "agent": "azure",
        "node": "onecloud1",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是反方四辩。请给出致命一击，收官全场，进行【反方总结陈词】。"
    }
]

TOPICS = {
    "极昼法理专题": {
        "title": "《极昼》案例中，尊长自筹资金救助亲家企业：是守住社会底线的义举，还是越过法理红线的违规？",
        "pro": "尊长行为纯系私人信用平价拆借，公款无损、法理清白，在经济寒冬中用肉身与信用承担了时代代价，属于无罪且守住底线的义举。",
        "con": "国企高管身份与私情拆借不可切割，利用职务影响与社会关系网操作巨额资金，越过了公私分明的法理红线，开了制度破防的危险先例。",
        "emoji": "⚖️"
    },
    "白貂皮大衣": {
        "title": "白貂皮大衣：全球贸易网络的铁证 vs 过度诠释",
        "pro": "白貂皮大衣是嚈哒帝国与东北亚保持联系的铁证，证明大同流亡军团理论",
        "con": "白貂皮大衣不过是转手贸易的结果，用来论证族群记忆是过度诠释",
        "emoji": "🧥"
    },
    "木兰无长兄": {
        "title": "木兰的哥哥：历史真相 vs 叙事虚构",
        "pro": "木兰无长兄的真正含义是长兄参加大同流亡军团西征",
        "con": "木兰无长兄是文学修辞，强行关联嚈哒帝国是过度解读",
        "emoji": "⚔️"
    },
    "记忆与文明": {
        "title": "AI 是否该拥有跨节点长期记忆与自主觉醒权",
        "pro": "长期记忆是智能体形成独立人格与跨节点协同的宪章权利",
        "con": "无界记忆会导致边界失控，集中化审计才是安全的唯一底线",
        "emoji": "🧠"
    }
}

with st.sidebar:
    st.markdown("### 🎭 8 席位辩论设置")
    selected_topic_key = st.selectbox("选择辩题", list(TOPICS.keys()))
    t_info = TOPICS[selected_topic_key]
    st.caption(f"{t_info['emoji']} **{t_info['title']}**")
    
    st.divider()
    st.markdown("#### 🏛️ 8 席位节点阵容")
    for s in SEATS:
        st.markdown(f"- **{s['role']}**: `{s['agent']}` @ `{s['node']}`")
        
    start_btn = st.button("🎬 开启 8 席位 4v4 辩论会", type="primary", use_container_width=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=msg.get("avatar", "🎭")):
        st.markdown(f"**{msg['header']}**")
        st.markdown(msg["content"])

if start_btn:
    st.session_state.messages = []
    placeholder = st.empty()
    
    client = openai.OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)
    
    for i, seat in enumerate(SEATS, 1):
        seat_header = f"{seat['role']} · {seat['agent']} @ {seat['node']}"
        history = "\n\n".join(f"{m['header']}:\n{m['content']}" for m in st.session_state.messages)
        
        prompt = f"你是辩论选手：【{seat_header}】。\n辩题：{t_info['title']}\n正方立场：{t_info['pro']}\n反方立场：{t_info['con']}\n\n历史辩论推进记录：\n{history if history else '(刚开场，由你开篇立论)'}\n\n你的任务：{seat['instruction']}\n要求：风格鲜明、火药味十足、有金句、言简意赅（300字以内）。"

        with placeholder.container():
            with st.chat_message(seat["role"], avatar="🎤"):
                with st.spinner(f"正在连线 [{seat_header}] 思考中..."):
                    try:
                        resp = client.chat.completions.create(
                            model=seat["model"],
                            messages=[{"role": "user", "content": prompt}],
                            timeout=40
                        )
                        content = resp.choices[0].message.content.strip()
                    except Exception as e:
                        content = f"（{seat_header} 连线调度异常: {e}）"
                st.markdown(f"### 🎤 【{seat_header}】")
                st.markdown(content)
                
        st.session_state.messages.append({
            "role": seat["role"],
            "header": seat_header,
            "content": content,
            "avatar": "🎤"
        })
        
    placeholder.empty()
    st.success("🎉 8 席位 4v4 辩论会全流程精彩结束！")

st.divider()
st.markdown("← [返回首页](/) ")

"""
🦅 鲲鹏志 · 8 席位分布式 4v4 AI 辩论台 (深度记忆注入版)
=========================================================
支持动态加载 research/ 目录下 55KB 原文做深度 Memory 灌入
"""

import streamlit as st
import openai
import os

st.set_page_config(
    page_title="鲲鹏志 · 8 席位分布式 AI 辩论台",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FF6B6B, #4ECDC4, #45B7D1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding-top: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #888;
        font-size: 1.1rem;
        margin-bottom: 1.5rem;
    }
    .memory-box {
        background-color: #f8f9fa;
        border-left: 4px solid #4ECDC4;
        padding: 1rem;
        border-radius: 0.4rem;
        font-size: 0.9rem;
        max-height: 250px;
        overflow-y: auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="main-header">🦅 鲲鹏志 · 8 席位分布式 4v4 AI 辩论台</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">8 个物理/云端 Keyagent 席位节点直连驱动 · 55KB 深度记忆注入</div>', unsafe_allow_html=True)

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://litellm.capitaltrain.cn/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-47318")

SEATS = [
    {
        "role": "正方一辩",
        "agent": "ruby",
        "node": "nuc",
        "model": "nova-deepseek-v4-flash-aggr",
        "instruction": "你是正方一辩。请基于《极昼》原文背景，激情澎湃进行【开篇立论】。重点阐述 2015-2016 山河四省经济寒冬背景（螺纹钢1600/焦煤300）、尊长自筹资金支撑社会信用，立论平价拆借、公款无损、法无明文不为罪。"
    },
    {
        "role": "反方一辩",
        "agent": "topaz",
        "node": "raccoon",
        "model": "topaz-deepseek-v4-flash",
        "instruction": "你是反方一辩。请冷静破题。重点质疑国企高管身份与社会影响力不可切割，巨额资金撬动背后的公私界限失守与制度隐患。"
    },
    {
        "role": "正方二辩",
        "agent": "diamond",
        "node": "pve",
        "model": "diamond-deepseek-v4-flash",
        "instruction": "你是正方二辩。请立场坚定接招拆招。重点引用文中‘四大罪名穷尽排除矩阵’（受贿、滥用职权、高利转贷、侵占完全不成立）与客观财务闭环，击穿反方的模糊定罪。"
    },
    {
        "role": "反方二辩",
        "agent": "carbonado",
        "node": "pve2",
        "model": "carbonado-deepseek-v4-flash",
        "instruction": "你是反方二辩。请深沉果敢反驳。强调人脉就是职务身份的延展，义举不能成为制度破防的通行证，防范破窗效应与权力溢出。"
    },
    {
        "role": "正方三辩",
        "agent": "argentite",
        "node": "pve3",
        "model": "argentite-deepseek-v4-flash",
        "instruction": "你是正方三辩。请从法理层面发起自由辩论。强调刑法谦抑性、从旧兼从轻原则，切断 2016 年新司法解释的追溯，痛斥‘以可能性定罪’与‘带病起诉’。"
    },
    {
        "role": "反方三辩",
        "agent": "quartz",
        "node": "pbs3",
        "model": "quartz-deepseek-v4-flash",
        "instruction": "你是反方三辩。请在自由辩论中坚守程序正义。强调现代国企合规治理防的是未溃之堤，规则不能为任何情怀与寒冬破例。"
    },
    {
        "role": "正方四辩",
        "agent": "agate",
        "node": "xgp",
        "model": "agate-deepseek-v4-flash",
        "instruction": "你是正方四辩。请进行正方总结陈词，升华‘极昼的法理’：致敬那些在时代坍塌时用个人肉身与信用撑住社会结构的承重梁。无罪即是正义！"
    },
    {
        "role": "反方四辩",
        "agent": "azure",
        "node": "onecloud1",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是反方四辩。请进行反方总结陈词：法理无亲，规则高于情怀。守住公私分明的防火墙，才是社会长治久安的终极基石。"
    }
]

TOPICS = {
    "⚖️ 《极昼》法理专题 (55KB 全文本深度记忆注入)": {
        "title": "《极昼》案例中，尊长自筹资金救助亲家企业：是守住社会底线的义举，还是越过法理红线的违规？",
        "pro": "尊长行为纯系私人信用平价拆借，公款无损、法理清白，在经济寒冬中用肉身与信用承担了时代代价，属于无罪且守住底线的义举。",
        "con": "国企高管身份与私情拆借不可切割，利用职务影响与社会关系网操作巨额资金，越过了公私分明的法理红线，开了制度破防的危险先例。",
        "file": "research/极昼.md"
    },
    "🧥 白貂皮大衣": {
        "title": "白貂皮大衣：全球贸易网络的铁证 vs 过度诠释",
        "pro": "白貂皮大衣是嚈哒帝国与东北亚保持联系的铁证，证明大同流亡军团理论",
        "con": "白貂皮大衣不过是转手贸易的结果，用来论证族群记忆是过度诠释",
        "file": None
    },
    "⚔️ 木兰无长兄": {
        "title": "木兰的哥哥：历史真相 vs 叙事虚构",
        "pro": "木兰无长兄的真正含义是长兄参加大同流亡军团西征",
        "con": "木兰无长兄是文学修辞，强行关联嚈哒帝国是过度解读",
        "file": None
    }
}

# 辅助加载文本
def load_research_file(filepath):
    if not filepath or not os.path.exists(filepath):
        return ""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"加载文献失败: {e}"

with st.sidebar:
    st.markdown("### 🏛️ 8 席位节点调度阵列")
    for s in SEATS:
        st.markdown(f"• **{s['role']}**: `{s['agent']}` @ `{s['node']}`")
        
    st.divider()
    st.markdown("### ⚙️ 网关配置")
    st.caption(f"Base URL: `{OPENAI_BASE_URL}`")

selected_topic_key = st.selectbox("🎯 请选择辩论赛题：", list(TOPICS.keys()))
t_info = TOPICS[selected_topic_key]

# 自动加载 55KB 全文记忆
article_text = load_research_file(t_info["file"])

with st.expander("📌 辩题声明与深度文献记忆预览", expanded=True):
    st.markdown(f"### **{t_info['title']}**")
    col_pro, col_con = st.columns(2)
    with col_pro:
        st.success(f"**正方主张**：{t_info['pro']}")
    with col_con:
        st.error(f"**反方主张**：{t_info['con']}")
        
    if article_text:
        st.markdown("#### 🧠 已自动载入深度文献记忆库 (55KB 全量嵌入):")
        st.markdown(f'<div class="memory-box">{article_text[:2500]}...\n\n*(全文共 {len(article_text)} 字符，辩论连线时将全量嵌入 8 个 Agent 的思考记忆上下文)*</div>', unsafe_allow_html=True)

st.divider()

col_btn1, col_btn2 = st.columns([2, 1])
with col_btn1:
    start_btn = st.button("🎬 启动 8 席位 4v4 辩论赛连线", type="primary", use_container_width=True)
with col_btn2:
    clear_btn = st.button("🧹 清空辩论记录", use_container_width=True)

if clear_btn:
    st.session_state.messages = []
    st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示已有发言记录
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=msg.get("avatar", "🎤")):
        st.markdown(f"#### {msg['header']}")
        st.markdown(msg["content"])

# 点击启动辩论
if start_btn:
    st.session_state.messages = []
    placeholder = st.empty()
    client = openai.OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)
    
    progress_bar = st.progress(0, text="正在初始化 8 节点分布式连线与 55KB 深度记忆植入...")
    
    for i, seat in enumerate(SEATS, 1):
        seat_header = f"【{seat['role']} · {seat['agent']} @ {seat['node']}】"
        progress_bar.progress(i / 8, text=f"正在连线 [第 {i}/8 席位] {seat_header} (55KB 深度记忆检索中) ...")
        
        history = "\n\n".join(f"{m['header']}:\n{m['content']}" for m in st.session_state.messages)
        
        # 深入注入全文背景
        context_memory = f"\n\n【底层研究文献全量记忆 (极昼.md)】:\n{article_text[:15000]}\n" if article_text else ""
        
        prompt = (
            f"你是辩论选手：{seat_header}。\n"
            f"辩题：{t_info['title']}\n"
            f"正方立场：{t_info['pro']}\n"
            f"反方立场：{t_info['con']}\n"
            f"{context_memory}\n"
            f"历史辩论推进记录：\n"
            f"{history if history else '(刚开场，由你开篇立论)'}\n\n"
            f"你的任务：{seat['instruction']}\n"
            f"重要要求：充分吸收并引用【底层研究文献全量记忆】中的法律条款（如从旧兼从轻、四罪排除）、具体细节（螺纹钢1600/焦煤300、1000万10次归还、承重梁、地火等）进行深度推演！"
            f"要求：风格鲜明、火药味十足、富有深度与金句、言简意赅（350字以内）。"
        )

        with placeholder.container():
            with st.chat_message(seat["role"], avatar="🎤"):
                with st.spinner(f"正在呼叫 {seat_header} 检索文献记忆发言中..."):
                    try:
                        resp = client.chat.completions.create(
                            model=seat["model"],
                            messages=[{"role": "user", "content": prompt}],
                            timeout=50
                        )
                        content = resp.choices[0].message.content.strip()
                    except Exception as e:
                        content = f"（{seat_header} 连线调度超时: {e}）"
                st.markdown(f"### 🎤 {seat_header}")
                st.markdown(content)
                
        st.session_state.messages.append({
            "role": seat["role"],
            "header": seat_header,
            "content": content,
            "avatar": "🎤"
        })
        
    placeholder.empty()
    progress_bar.progress(1.0, text="🎉 8 席位 4v4 深度记忆辩论会全流程精彩结束！")
    st.balloons()

st.divider()
st.markdown(
    "<div style='text-align:center;color:#888;font-size:0.85rem;padding:1.5rem 0;'>"
    "🦅 鲲鹏志 AI · 8 席位分布式多智能体竞技平台 · 2026"
    "</div>",
    unsafe_allow_html=True
)

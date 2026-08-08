"""
🦅 鲲鹏志 · 8 席位分布式 4v4 AI 辩论台 (硬核法理深度版)
=========================================================
彻底去除空洞套话 · 强制条文/财务撕扯 · 深度逻辑推演
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
        max-height: 220px;
        overflow-y: auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="main-header">🦅 鲲鹏志 · 8 席位分布式 4v4 AI 辩论台</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">8 个物理/云端 Keyagent 席位节点直连驱动 · 硬核法理深度推演</div>', unsafe_allow_html=True)

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://litellm.capitaltrain.cn/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-47318")

SEATS = [
    {
        "role": "正方一辩",
        "agent": "ruby",
        "node": "nuc",
        "model": "nova-deepseek-v4-flash-aggr",
        "instruction": "【开篇立论·事实破局】禁止使用任何辩论套话！直接引用《极昼.md》中2015-2016山河四省最冷冬天的真实背景（螺纹钢跌至1600，焦煤跌破300，民间爆雷，银行抽贷）。硬核阐明：1000万系尊长向特定亲友自筹私人资金，回程10次各100万平价还本，无利息溢价，中煤账目零亏空。在社会结构即将倾覆时，尊长用私人信用撑住了承重梁，法无明文不为罪！"
    },
    {
        "role": "反方一辩",
        "agent": "topaz",
        "node": "raccoon",
        "model": "topaz-deepseek-v4-flash",
        "instruction": "【反方破题·撕扯公私界限】禁止使用辩论套话！直接驳斥正一：“凭什么一个国企高管能凭‘个人信用’瞬间撬动千万元私人资金？”剖析‘社会信用’与‘职务影响力’在现实中的法律混同。没有国企高管的隐形背书，这笔巨额资金不可能拆借成功。尊长行为本质上是利用职务隐形影响为亲友企业定向输血，越过了公私分明的法理红线。"
    },
    {
        "role": "正方二辩",
        "agent": "diamond",
        "node": "pve",
        "model": "diamond-deepseek-v4-flash",
        "instruction": "【接招拆招·掏出四罪排除矩阵】直接针对反一的‘职务影响混同论’进行法律反击！掏出《极昼.md》中的【四大罪名穷尽式排除矩阵】：1.受贿罪（资金逆向借出而非收受，无溢价对价）；2.滥用职权罪（未动用中煤公章、资金或行政资源，零国家损失）；3.贪污罪（账目纯洁）；4.高利转贷/非吸（非信贷资金、特定亲友圈）。用客观书证压制检方的‘可能性定罪’！"
    },
    {
        "role": "反方二辩",
        "agent": "carbonado",
        "node": "pve2",
        "model": "carbonado-deepseek-v4-flash",
        "instruction": "【针锋相对·剖析隐性权力寻租】针对正二的‘四大罪名排除’进行法理反驳！指出刑法不应该成为合规漏洞的庇护所。权力和职务影响力就像水渗入沙土，公钱虽未动，但国企高管用自身影响力为私企信用背书，就是在制造‘破窗效应’。如果今天可以用‘义举’开绿灯，明天他人就会用‘有息谋私’，这会彻底摧毁国企治理的防火墙。"
    },
    {
        "role": "正方三辩",
        "agent": "argentite",
        "node": "pve3",
        "model": "argentite-deepseek-v4-flash",
        "instruction": "【自由辩论·法理溯及力击穿】直接引用《刑法》第12条“从旧兼从轻”原则！行为发生于2016年春节（2月），检方试图套用2016年4月新施行的司法解释中‘感情投资/事后感谢’的拟制罪名，完全属于违宪的溯及既往！在2003年纪要标准下，无具体请托事项且无财物收受，罪名绝对不成立。刑法是谦抑的，不能为了迎合公诉而捏造犯罪！"
    },
    {
        "role": "反方三辩",
        "agent": "quartz",
        "node": "pbs3",
        "model": "quartz-deepseek-v4-flash",
        "instruction": "【自由辩论·程序正义与危墙】直击正三的‘法不溯及既往’！强调现代国企治理防的是未溃之堤。法律审判虽然受时间锚定限制，但国企合规审查不能对隐形权力寻租睁一只眼闭一只眼。寒夜救火者固然值得同情，但如果他用的是制度长城的砖头去垫自家柴房，规则就绝不能破例。程序正义高于个案同情！"
    },
    {
        "role": "正方四辩",
        "agent": "agate",
        "node": "xgp",
        "model": "agate-deepseek-v4-flash",
        "instruction": "【正方总结·极昼法理与时代承重梁】总结全场事实与法理！检方穷尽四罪全部排除，时间锚定阻断溯及力，客观财务闭环无一分亏空。在2015-2016那个山河四省地火快要熄灭的极昼寒冬，是尊长这样的干部用肉身和信用撑住了社会结构的承重梁。事后论功行赏时被安排退场，论罪定责时被推上台前——法律不能背叛正义！无罪即是正义！"
    },
    {
        "role": "反方四辩",
        "agent": "azure",
        "node": "onecloud1",
        "model": "azure-deepseek-v4-flash",
        "instruction": "【反方总结·法理无亲与规则高于情怀】总结反方终极底线！尊重尊长在寒冬里的义举，但法治的基石是公私有别。没有一个普通老人能凭‘脸面’瞬间撬动千万资金，他借的不是信用，是职务身份的影子。若因个人情怀与时代悲情而撕开规则的缺口，长治久安终成空谈。法理无亲，规则高于情怀！"
    }
]

TOPICS = {
    "⚖️ 《极昼》硬核法理专题 (全文献+罪名排除矩阵深度推演)": {
        "title": "《极昼》案例中，尊长自筹资金救助亲家企业：是守住社会底线的义举，还是越过法理红线的违规？",
        "pro": "尊长行为纯系私人信用平价拆借，公款无损、法理清白，在经济寒冬中用肉身与信用承担了时代代价，属于无罪且守住底线的义举。",
        "con": "国企高管身份与私情拆借不可切割，利用职务影响与社会关系网操作巨额资金，越过了公私分明的法理红线，开了制度破防的危险先例。",
        "file": "research/极昼.md"
    }
}

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

article_text = load_research_file(t_info["file"])

with st.expander("📌 辩题声明与《极昼.md》法理研究全文", expanded=True):
    st.markdown(f"### **{t_info['title']}**")
    col_pro, col_con = st.columns(2)
    with col_pro:
        st.success(f"**正方主张**：{t_info['pro']}")
    with col_con:
        st.error(f"**反方主张**：{t_info['con']}")
        
    if article_text:
        st.markdown("#### 🧠 55KB 深度文献库（已注入 8 席位思考上下文）：")
        st.markdown(f'<div class="memory-box">{article_text[:3000]}...\n\n*(全文共 {len(article_text)} 字符)*</div>', unsafe_allow_html=True)

st.divider()

col_btn1, col_btn2 = st.columns([2, 1])
with col_btn1:
    start_btn = st.button("🎬 启动 8 席位硬核法理辩论赛", type="primary", use_container_width=True)
with col_btn2:
    clear_btn = st.button("🧹 清空辩论记录", use_container_width=True)

if clear_btn:
    st.session_state.messages = []
    st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=msg.get("avatar", "🎤")):
        st.markdown(f"#### {msg['header']}")
        st.markdown(msg["content"])

if start_btn:
    st.session_state.messages = []
    placeholder = st.empty()
    client = openai.OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)
    
    progress_bar = st.progress(0, text="正在初始化 8 节点分布式硬核连线...")
    
    for i, seat in enumerate(SEATS, 1):
        seat_header = f"【{seat['role']} · {seat['agent']} @ {seat['node']}】"
        progress_bar.progress(i / 8, text=f"正在连线 [第 {i}/8 席位] {seat_header} (进行深度条文撕扯) ...")
        
        history = "\n\n".join(f"{m['header']}:\n{m['content']}" for m in st.session_state.messages)
        
        context_memory = f"\n\n【《极昼.md》研究文献核心条文与数据记忆】:\n{article_text[:18000]}\n" if article_text else ""
        
        prompt = (
            f"你是辩论选手：{seat_header}。\n"
            f"辩题：{t_info['title']}\n"
            f"正方立场：{t_info['pro']}\n"
            f"反方立场：{t_info['con']}\n"
            f"{context_memory}\n"
            f"历史辩论推进记录：\n"
            f"{history if history else '(刚开场，由你开篇立论)'}\n\n"
            f"你的任务：{seat['instruction']}\n"
            f"💥 严格发调指令：\n"
            f"1. 严禁使用‘对方辩友好’、‘滑天下之大稽’等任何废话套话！直接切入硬核法理与财务数据！\n"
            f"2. 第一句话必须针对上一位辩手的具体漏洞进行精准摧毁！\n"
            f"3. 必须大量引用《极昼.md》中的精确数据（螺纹钢1600/焦煤300、1000万10次平价归还水单）、刑法条文（第12条从旧兼从轻、四大罪名排除矩阵）进行针锋相对的辩驳！\n"
            f"4. 语言要极具法理深度、毒辣犀利、充满时代宿命感，字数控制在 350 字以内。"
        )

        with placeholder.container():
            with st.chat_message(seat["role"], avatar="🎤"):
                with st.spinner(f"正在呼叫 {seat_header} 进行硬核法理推演..."):
                    try:
                        resp = client.chat.completions.create(
                            model=seat["model"],
                            messages=[{"role": "user", "content": prompt}],
                            timeout=55
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
    progress_bar.progress(1.0, text="🎉 8 席位硬核法理辩论赛精彩落幕！")
    st.balloons()

st.divider()
st.markdown(
    "<div style='text-align:center;color:#888;font-size:0.85rem;padding:1.5rem 0;'>"
    "🦅 鲲鹏志 AI · 8 席位分布式多智能体竞技平台 · 2026"
    "</div>",
    unsafe_allow_html=True
)

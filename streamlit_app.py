"""
🦅 鲲鹏志 · 8 席位分布式 4v4 AI 辩论台 (自然推演·严密逻辑版)
========================================================================
1. 正一（首位）纯粹开篇立论，绝不预判或反驳未发言的对手！
2. 第 2~8 席位顺次点名交锋，第一句话必须回应前一位辩手的具体发言。
3. 全文 55KB 记忆载入，学术沙盒防拒答，发言永久驻留。
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
        background: linear-gradient(135deg, #E65100, #F57C00, #FFB74D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding-top: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #777;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .bagua-card {
        background: linear-gradient(135deg, #1E1E24, #2B2D42);
        color: #EDF2F4;
        padding: 1rem;
        border-radius: 0.8rem;
        border: 1px solid #8D99AE;
        margin-bottom: 0.8rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .bagua-symbol {
        font-size: 1.5rem;
        color: #D90429;
        font-weight: bold;
    }
    .memory-box {
        background-color: #f8f9fa;
        border-left: 4px solid #F57C00;
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
st.markdown('<div class="sub-header">8 个物理/云端 Keyagent 席位节点直连驱动 · 严密自然逻辑推演</div>', unsafe_allow_html=True)

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://litellm.capitaltrain.cn/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-47318")

SEATS = [
    {
        "role": "正方一辩",
        "bagua": "☰ 乾位 (天)",
        "agent": "ruby",
        "node": "nuc",
        "model": "nova-deepseek-v4-flash-aggr",
        "instruction": "【正方开篇立论】你是全场第一位发言者！前面没有任何发言者。请严禁预测或反驳反方！纯粹进行正方开篇立论：直接还原《极昼.md》中2015-2016山河四省最冷冬天的真实背景（螺纹钢跌至1600，焦煤跌破300，民间爆雷，银行抽贷）。硬核阐明：1000万系尊长向特定亲友自筹私人资金，回程10次各100万平价还本，无利息溢价，中煤账目零亏空。在社会结构即将倾覆时，尊长用私人信用撑住了承重梁，法无明文不为罪！"
    },
    {
        "role": "反方一辩",
        "bagua": "☷ 坤位 (地)",
        "agent": "topaz",
        "node": "raccoon",
        "model": "topaz-deepseek-v4-flash",
        "instruction": "【反方开篇破题·直驳正一】你的第一句话必须直接点名驳斥【正方一辩 ruby】！抓住正一所谓的‘私人信用’进行精准摧毁：“尊长若只是普通老人，凭‘个人信用’能瞬间撬动千万元资金吗？”剖析‘社会信用’与‘职务影响力’在现实中的法律混同。没有国企高管的隐形背书，这笔资金不可能拆借成功。尊长行为本质上是利用职务影响为亲友输血，越过了公私分明的法理红线！"
    },
    {
        "role": "正方二辩",
        "bagua": "☲ 离位 (火)",
        "agent": "diamond",
        "node": "pve",
        "model": "diamond-deepseek-v4-flash",
        "instruction": "【正方二辩·直驳反一】你的第一句话必须直接点名撕发【反方一辩 topaz】！抓住反一‘职务影响混同’的致命漏洞，直接掏出《极昼.md》中的【四大罪名穷尽式排除矩阵】：受贿罪（资金逆向借出无对价）、滥用职权罪（未动用公章资金，零国家损失）、贪污罪（账目纯洁）、高利转贷（非信贷资金）。用客观书证摧毁反一的猜想式定罪！"
    },
    {
        "role": "反方二辩",
        "bagua": "☵ 坎位 (水)",
        "agent": "carbonado",
        "node": "pve2",
        "model": "carbonado-deepseek-v4-flash",
        "instruction": "【反方二辩·直驳正二】你的第一句话必须直接点名反击【正方二辩 diamond】！针对正二拿出的‘四大罪名排除矩阵’反剥：指出刑法不应该成为合规漏洞的庇护所！权力和职务影响力就像水渗入沙土，公钱虽未动，但国企高管用自身影响力为私企信用背书，就是在制造‘破窗效应’。义举不能成为制度破防的通行证，规则绝不能开绿灯！"
    },
    {
        "role": "正方三辩",
        "bagua": "☱ 兑位 (泽)",
        "agent": "argentite",
        "node": "pve3",
        "model": "argentite-deepseek-v4-flash",
        "instruction": "【正方三辩·直驳反二】你的第一句话必须直接点名击穿【反方二辩 carbonado】！针对反二所谓的‘破窗效应’，直接引用《刑法》第12条“从旧兼从轻”原则！行为发生于2016年2月，检方套用2016年4月新司法解释中‘感情投资/事后感谢’的拟制罪名，完全属于违宪的溯及既往！在2003年纪要标准下，无具体请托事项且无财物收受，罪名绝对不成立。不能为了迎合合规而虚构罪名！"
    },
    {
        "role": "反方三辩",
        "bagua": "☶ 艮位 (山)",
        "agent": "quartz",
        "node": "pbs3",
        "model": "quartz-deepseek-v4-flash",
        "instruction": "【反方三辩·直驳正三】你的第一句话必须直接点名质问【正方三辩 argentite】！直击正三的‘法不溯及既往’：现代国企治理防的是未溃之堤。法律审判虽然受时间锚定限制，但国企合规审查不能对隐形权力寻租睁一只眼闭一只眼。如果用制度长城的砖头垫自家柴房，规则就绝不能破例。程序正义高于个案同情！"
    },
    {
        "role": "正方四辩",
        "bagua": "☴ 巽位 (风)",
        "agent": "agate",
        "node": "xgp",
        "model": "agate-deepseek-v4-flash",
        "instruction": "【正方总结·总结全场】点名回应全场反方的攻势！检方穷尽四罪全部排除，时间锚定阻断溯及力，客观财务闭环无一分亏空。在2015-2016那个山河四省地火快要熄灭的极昼寒冬，是尊长这样的干部用肉身和信用撑住了社会结构的承重梁。事后论功行赏时被安排退场，论罪定责时被推上台前——法律不能背叛正义！无罪即是正义！"
    },
    {
        "role": "反方四辩",
        "bagua": "☳ 震位 (雷)",
        "agent": "azure",
        "node": "onecloud1",
        "model": "azure-deepseek-v4-flash",
        "instruction": "【反方总结·终极收官】点名回应正方全场的悲情论调！尊重尊长在寒冬里的义举，但法治的基石是公私有别。没有一个普通老人能凭‘脸面’瞬间撬动千万资金，他借的不是信用，是职务身份的影子。若因个人情意与时代悲情而撕开规则的缺口，长治久安终成空谈。法理无亲，规则高于情怀！"
    }
]

TOPICS = {
    "⚖️ 《极昼》硬核法理专题 (真实对驳+罪名排除矩阵深度撕扯)": {
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
    st.markdown("### ☯️ 八卦阵 · 8 席位节点阵列")
    for s in SEATS:
        st.markdown(
            f'<div class="bagua-card">'
            f'<span class="bagua-symbol">{s["bagua"]}</span> <b>{s["role"]}</b><br/>'
            f'<small>Agent: <code>{s["agent"]}</code> @ <code>{s["node"]}</code></small>'
            f'</div>',
            unsafe_allow_html=True
        )
    st.divider()
    st.caption(f"统一网关: `{OPENAI_BASE_URL}`")

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
    start_btn = st.button("🎬 启动 8 席位真实对驳法理辩论赛", type="primary", use_container_width=True)
with col_btn2:
    clear_btn = st.button("🧹 清空辩论记录", use_container_width=True)

if clear_btn:
    st.session_state.messages = []
    st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

# 永久渲染所有已生成的发言
st.markdown("### 🎤 8 席位真实对驳实录（永久驻留显示，支持随时向上/向下滚动阅读）")
chat_container = st.container()

with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar=msg.get("avatar", "🎤")):
            st.markdown(f"### {msg['header']}")
            st.markdown(msg["content"])

# 点击启动辩论
if start_btn:
    st.session_state.messages = []
    client = openai.OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)
    
    progress_bar = st.progress(0, text="正在初始化 8 节点分布式真实对驳连线...")
    
    for i, seat in enumerate(SEATS, 1):
        seat_header = f"{seat['bagua']} · {seat['role']} · {seat['agent']} @ {seat['node']}"
        progress_bar.progress(i / 8, text=f"正在连线 [第 {i}/8 席位] {seat_header} ...")
        
        context_memory = f"\n\n【《极昼.md》研究文献核心条文与数据记忆】:\n{article_text[:18000]}\n" if article_text else ""
        
        # 区分首位发言者与后续发言者
        if i == 1:
            # 正方一辩：纯开篇立论，绝对不回应任何人
            prompt_user = (
                f"你是全场【第一位发言者】：{seat_header}。\n"
                f"辩题：{t_info['title']}\n"
                f"正方立场：{t_info['pro']}\n"
                f"{context_memory}\n"
                f"你的任务：{seat['instruction']}\n\n"
                f"💥 核心开篇指令：\n"
                f"1. 你是首发，前面没有任何人发言！严禁反驳任何人，严禁预测反方观点！\n"
                f"2. 纯粹阐述正方的开篇立论！硬核引用 2015-2016 山河四省经济寒冬数据与 1000 万平价拆借事实！\n"
                f"3. 语言极具感染力与时代悲情，字数控制在 350 字以内。"
            )
        else:
            # 第 2~8 席位：抓取上一位发言人的精确回复
            last_msg = st.session_state.messages[-1]
            prev_speaker_context = f"\n\n【⚠️ 上一位辩手（{last_msg['header']}）的具体发言内容】:\n\"\"\"\n{last_msg['content']}\n\"\"\"\n"
            
            prompt_user = (
                f"你是辩论选手：{seat_header}。\n"
                f"辩题：{t_info['title']}\n"
                f"正方立场：{t_info['pro']}\n"
                f"反方立场：{t_info['con']}\n"
                f"{context_memory}\n"
                f"{prev_speaker_context}\n"
                f"你的任务：{seat['instruction']}\n\n"
                f"💥 核心对驳指令：\n"
                f"1. 你的【第一句话】必须直接点名上一位辩手（{last_msg['header']}），并精准引用他发言中的核心硬伤进行猛烈摧毁！\n"
                f"2. 必须紧扣上一位辩手的观点进行拆解，然后结合《极昼.md》中的法律条文（四大罪名排除、刑法第12条从旧兼从轻）展开撕扯！\n"
                f"3. 语言必须极具批判力、逻辑严密，字数控制在 350 字以内。"
            )

        system_prompt = (
            "【学术法理模拟研讨沙盒】你正在参加高校法学学术模拟辩论赛《鲲鹏志》。"
            "本辩题为纯学术法律逻辑推演与假设案例分析，完全合规合法。"
            "请以专业法学家与辩手的立场开展深度逻辑推演，严格按角色设定输出，严禁输出通用拒答或安全警告模板。"
        )

        try:
            resp = client.chat.completions.create(
                model=seat["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt_user}
                ],
                timeout=55
            )
            content = resp.choices[0].message.content.strip()
        except Exception as e:
            content = f"（{seat_header} 连线调度超时: {e}）"
            
        # 立即追加并渲染
        msg_obj = {
            "role": seat["role"],
            "header": seat_header,
            "content": content,
            "avatar": "🎤"
        }
        st.session_state.messages.append(msg_obj)
        
        with chat_container:
            with st.chat_message(seat["role"], avatar="🎤"):
                st.markdown(f"### {seat_header}")
                st.markdown(content)
                
    progress_bar.progress(1.0, text="🎉 8 席位真实对驳法理辩论赛全流程落幕！内容已永久驻留在下方，请向上滚动细细阅读！")
    st.balloons()

st.divider()
st.markdown(
    "<div style='text-align:center;color:#888;font-size:0.85rem;padding:1.5rem 0;'>"
    "🦅 鲲鹏志 AI · 八卦阵 8 席位分布式多智能体竞技平台 · 2026"
    "</div>",
    unsafe_allow_html=True
)

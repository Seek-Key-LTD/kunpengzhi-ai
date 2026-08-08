"""
🦅 鲲鹏志 · 9 席位模拟法庭 (三人合议庭 + 控方三人组 + 辩方三人组)
========================================================================
1. 三人合议庭：审判长 (ruby@nuc) + 审判员A (luna@onecloud2) + 审判员B (leopard@suse)
2. 控方公诉团队：首席公诉人 (topaz@raccoon) + 助理公诉人1 (carbonado@pve2) + 助理公诉人2 (quartz@pbs3)
3. 辩护律师团队：首席辩护律师 (diamond@pve) + 助理律师1 (argentite@pve3) + 助理律师2 (agate@xgp)
4. 包含完整庭审5阶段：开庭归纳 -> 控方起诉 -> 辩方答辩排除 -> 合议庭质询 -> 审判长宣判
"""

import streamlit as st
import openai
import os

st.set_page_config(
    page_title="鲲鹏志 · 9 席位模拟法庭",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #B71C1C, #D32F2F, #F44336);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding-top: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .court-card {
        background: #1E1E24;
        color: #FFFFFF;
        padding: 0.8rem;
        border-radius: 0.6rem;
        margin-bottom: 0.6rem;
        font-size: 0.88rem;
    }
    .judge-badge { border-left: 4px solid #FFD700; }
    .prosecutor-badge { border-left: 4px solid #D32F2F; }
    .defense-badge { border-left: 4px solid #1976D2; }
    .memory-box {
        background-color: #f8f9fa;
        border-left: 4px solid #B71C1C;
        padding: 1rem;
        border-radius: 0.4rem;
        font-size: 0.9rem;
        max-height: 200px;
        overflow-y: auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="main-header">⚖️ 鲲鹏志 · 《极昼》案 9 席位模拟法庭</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">三人合议庭 + 控方三人组 + 辩方三人组 · 真实分布式多智能体法庭审理</div>', unsafe_allow_html=True)

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://litellm.capitaltrain.cn/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-47318")

# 9 席位模拟法庭阵列
COURT_SEATS = [
    {
        "stage": "一、开庭归纳焦点",
        "role": "🏛️ 审判长",
        "team": "judge",
        "agent": "ruby",
        "node": "nuc",
        "model": "nova-deepseek-v4-flash-aggr",
        "instruction": "你是本案【审判长】。请敲响法槌宣布开庭！直接归纳《极昼》案例的庭审焦点：尊长在2015-2016山河四省经济寒冬中自筹1000万平价救助亲家企业，到底属于守住社会底线的无罪义举，还是利用国企高管隐形影响力越过法理红线的犯罪？请要求控辩双方围绕《极昼.md》具体凭证与刑法条文展开举证质证！"
    },
    {
        "stage": "二、控方起诉要点",
        "role": "⚖️ 首席公诉人",
        "team": "prosecutor",
        "agent": "topaz",
        "node": "raccoon",
        "model": "topaz-deepseek-v4-flash",
        "instruction": "你是【首席公诉人】。代表控方发表起诉意见：尊长身为中煤高管，其社会信用与职务身份在法律上不可切割。普通老人无法瞬间撬动千万资金，这笔拆借本质上是利用职务影响力为私企定向输血，越过了公私红线，构成了对现代国企治理合规底线的侵犯。"
    },
    {
        "stage": "二、控方起诉要点",
        "role": "⚖️ 第一助理公诉人",
        "team": "prosecutor",
        "agent": "carbonado",
        "node": "pve2",
        "model": "carbonado-deepseek-v4-flash",
        "instruction": "你是【第一助理公诉人】。直接补充首席公诉人的意见：权力和职务影响力就像水渗入沙土，公钱虽未动，但国企高管用自身影响力为私企背书，就是在制造‘破窗效应’。义举不能成为制度破防的通行证！"
    },
    {
        "stage": "三、辩方答辩排除",
        "role": "🛡️ 首席辩护律师",
        "team": "defense",
        "agent": "diamond",
        "node": "pve",
        "model": "diamond-deepseek-v4-flash",
        "instruction": "你是【首席辩护律师】。第一句话直接点名驳斥控方的‘职务影响混同论’！掏出《极昼.md》中的【四大罪名穷尽式排除矩阵】：1.受贿罪（资金逆向借出无对价）；2.滥用职权罪（未动用公章资金，零国家损失）；3.贪污罪（账目纯洁）；4.高利转贷/非吸（非信贷资金）。用1000万10次平价还本水单书证压制控方的猜想起诉！"
    },
    {
        "stage": "三、辩方答辩排除",
        "role": "🛡️ 第一助理辩护律师",
        "team": "defense",
        "agent": "argentite",
        "node": "pve3",
        "model": "argentite-deepseek-v4-flash",
        "instruction": "你是【第一助理辩护律师】。第一句话直接点名反击控方的‘破窗效应’！直接引用《刑法》第12条“从旧兼从轻”原则：行为发生于2016年2月，控方套用2016年4月新司法解释中‘感情投资/事后感谢’的拟制罪名，完全属于违宪的溯及既往！在2003年纪要标准下，罪名绝对不成立。刑法是谦抑的，无罪即是正义！"
    },
    {
        "stage": "三、辩方答辩排除",
        "role": "🛡️ 第二助理辩护律师",
        "team": "defense",
        "agent": "agate",
        "node": "xgp",
        "model": "agate-deepseek-v4-flash",
        "instruction": "你是【第二助理辩护律师】。补强辩方辩护：还原2015-2016山河四省最冷冬天的真实悲壮背景（螺纹钢1600/焦煤300）。尊长是在社会结构即将倾覆时，用个人肉身和信用撑住了承重梁。事后论功行赏时被安排退场，论罪定责时被推上台前——法律不能背叛正义！"
    },
    {
        "stage": "四、合议庭质询",
        "role": "🏛️ 审判员 A (常情常理)",
        "team": "judge",
        "agent": "luna",
        "node": "onecloud2",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是合议庭【审判员A（侧重常理常情）】。对控辩双方进行法庭质询：追问控方‘如果一个人用自己的私人凭证、在经济危机中救助亲戚且平进平出无一分溢价都要被定罪，那法的温度何在？’同时追问辩方‘如何证明社会人脉完全脱离了职务背景？’"
    },
    {
        "stage": "四、合议庭质询",
        "role": "🏛️ 审判员 B (程序法理)",
        "team": "judge",
        "agent": "leopard",
        "node": "suse",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是合议庭【审判员B（侧重程序与实体法）】。对控辩双方进行程序质询：要求控方回答‘起诉书认定的罪名到底满足哪一条法定构成要件？’，同时要求辩方回答‘从旧兼从轻在2016年2月行为着手点的适用边界’。"
    },
    {
        "stage": "五、审判长终审宣判",
        "role": "🏛️ 审判长 (宣判)",
        "team": "judge",
        "agent": "ruby",
        "node": "nuc",
        "model": "nova-deepseek-v4-flash-aggr",
        "instruction": "你是【审判长】。请综合控辩双方辩论、四罪排除矩阵、从旧兼从轻原则以及合议庭评议结果，做出最终法庭判决！敲响法槌，宣告尊长无罪或裁定结果，并发表一份发人深省、震撼人心的法理判词！"
    }
]

def load_research_file(filepath):
    if not filepath or not os.path.exists(filepath):
        return ""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"加载文献失败: {e}"

with st.sidebar:
    st.markdown("### 🏛️ 9 席位模拟法庭构架")
    st.markdown("#### ⚖️ 三人合议庭")
    st.caption("• 审判长: `ruby` @ `nuc`")
    st.caption("• 审判员A: `luna` @ `onecloud2`")
    st.caption("• 审判员B: `leopard` @ `suse`")
    
    st.markdown("#### 🔴 控方团队 (3人)")
    st.caption("• 首席公诉: `topaz` @ `raccoon`")
    st.caption("• 公诉助理1: `carbonado` @ `pve2`")
    st.caption("• 公诉助理2: `quartz` @ `pbs3` (代)")
    
    st.markdown("#### 🔵 辩方团队 (3人)")
    st.caption("• 首席辩护: `diamond` @ `pve`")
    st.caption("• 辩护助理1: `argentite` @ `pve3`")
    st.caption("• 辩护助理2: `agate` @ `xgp`")
    
    st.divider()
    st.caption(f"网关: `{OPENAI_BASE_URL}`")

article_text = load_research_file("research/极昼.md")

with st.expander("📌 模拟法庭审理案由与《极昼.md》研究案卷", expanded=True):
    st.markdown("### **案由：尊长自筹资金救助亲家企业涉嫌滥用职权/受贿案**")
    col_pro, col_con = st.columns(2)
    with col_pro:
        st.success("**辩方无罪要点**：纯系私人信用平价拆借，公款零亏空，从旧兼从轻，四罪排除。")
    with col_con:
        st.error("**控方公诉要点**：国企高管身份与私情拆借不可切割，隐性权力寻租越过公私红线。")
        
    if article_text:
        st.markdown("#### 🧠 55KB 案卷全量写入法庭记忆库：")
        st.markdown(f'<div class="memory-box">{article_text[:2500]}...\n\n*(全文共 {len(article_text)} 字符全量载入庭审)*</div>', unsafe_allow_html=True)

st.divider()

col_btn1, col_btn2 = st.columns([2, 1])
with col_btn1:
    start_btn = st.button("⚖️ 敲响法槌 · 启动 9 席位模拟法庭审理", type="primary", use_container_width=True)
with col_btn2:
    clear_btn = st.button("🧹 清空庭审笔录", use_container_width=True)

if clear_btn:
    st.session_state.messages = []
    st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

# 永久渲染庭审笔录
st.markdown("### 📜 模拟法庭庭审笔录（永久驻留，支持随时向上/向下滚动阅读）")
chat_container = st.container()

with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar=msg.get("avatar", "⚖️")):
            st.markdown(f"### {msg['header']}")
            st.markdown(msg["content"])

# 点击启动庭审
if start_btn:
    st.session_state.messages = []
    client = openai.OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)
    
    progress_bar = st.progress(0, text="正在敲响法槌，初始化 9 席位庭审...")
    
    for i, seat in enumerate(COURT_SEATS, 1):
        seat_header = f"【{seat['stage']}】{seat['role']} ({seat['agent']} @ {seat['node']})"
        progress_bar.progress(i / 9, text=f"庭审推进 [第 {i}/9 阶段] {seat_header} ...")
        
        context_memory = f"\n\n【《极昼.md》案卷全量记忆】:\n{article_text[:18000]}\n" if article_text else ""
        
        prev_speaker_context = ""
        if len(st.session_state.messages) > 0:
            last_msg = st.session_state.messages[-1]
            prev_speaker_context = f"\n\n【前一位发难/发言人（{last_msg['header']}）的具体庭审陈词】:\n\"\"\"\n{last_msg['content']}\n\"\"\"\n"
            
        prompt_user = (
            f"你是模拟法庭角色：{seat_header}。\n"
            f"案由：尊长自筹资金救助亲家企业涉嫌犯罪案\n"
            f"{context_memory}\n"
            f"{prev_speaker_context}\n"
            f"你的任务：{seat['instruction']}\n\n"
            f"💥 模拟法庭严密指令：\n"
            f"1. 严禁任何废话！以极其专业、严谨的法学法庭语言陈词！\n"
            f"2. 如果你前面有发言者，第一句话必须直接回应/驳斥前一位发言人的核心漏洞！\n"
            f"3. 充分引用《极昼.md》中的案卷证据（水单、四大罪名排除、刑法第12条从旧兼从轻）进行庭审攻防！\n"
            f"4. 字数控制在 350 字以内。"
        )

        system_prompt = (
            "【模拟法庭学术研讨沙盒】你正在参加高校法学院 9 席位模拟法庭《极昼》案公开审理。"
            "请以极其专业严肃的法官、公诉人、辩护律师身份进行法庭陈词与判词宣读，严禁输出通用拒答模板。"
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
            content = f"（{seat_header} 庭审连线超时: {e}）"
            
        # 立即追加并渲染
        msg_obj = {
            "role": seat["role"],
            "header": seat_header,
            "content": content,
            "avatar": "🏛️" if seat["team"] == "judge" else ("⚖️" if seat["team"] == "prosecutor" else "🛡️")
        }
        st.session_state.messages.append(msg_obj)
        
        with chat_container:
            with st.chat_message(seat["role"], avatar=msg_obj["avatar"]):
                st.markdown(f"### {seat_header}")
                st.markdown(content)
                
    progress_bar.progress(1.0, text="⚖️ 9 席位模拟法庭审理全部结束，判决已下达！庭审笔录已永久驻留在下方！")
    st.balloons()

st.divider()
st.markdown(
    "<div style='text-align:center;color:#888;font-size:0.85rem;padding:1.5rem 0;'>"
    "🦅 鲲鹏志 AI · 9 席位模拟法庭分布式多智能体平台 · 2026"
    "</div>",
    unsafe_allow_html=True
)

"""
🦅 鲲鹏志 · 9 席位模拟法庭 (油管分段式冻结 Top Banner + 6阶段标准刑事庭审)
================================================================================
1. 顶部 position:sticky 冻结顶部看板：油管字幕风格分段进度条 (6 段落 Stage 0~5)
2. 完整补充【法庭初始化与准备】+【法庭调查举证】+【法庭调查质证】+【法庭辩论与质询】+【最后陈述】+【合议庭宣判】
3. 真实刑事庭审程序，9 席位分布式节点完整流转
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

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://litellm.capitaltrain.cn/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-47318")

# 6 个标准刑事庭审阶段定义
STAGES = [
    {"id": 0, "name": "0. 审判初始化", "emoji": "⚖️"},
    {"id": 1, "name": "1. 控方举证", "emoji": "🔍"},
    {"id": 2, "name": "2. 辩方质证", "emoji": "🛡️"},
    {"id": 3, "name": "3. 法庭辩论", "emoji": "⚔️"},
    {"id": 4, "name": "4. 最后陈述", "emoji": "📢"},
    {"id": 5, "name": "5. 终审宣判", "emoji": "🏛️"}
]

# 9 席位与标准庭审阶段映射
COURT_SEATS = [
    {
        "stage_id": 0,
        "stage_name": "【阶段 0 · 法庭准备与初始化】",
        "role": "🏛️ 审判长 (初始化)",
        "team": "judge",
        "agent": "ruby",
        "node": "nuc",
        "model": "nova-deepseek-v4-flash-aggr",
        "instruction": "你是本案【审判长】。请敲响法槌宣布开庭！进行法庭初始化：1. 核对被告人/尊长身份；2. 宣布案由《极昼》案例自筹资金救助亲家案；3. 介绍合议庭组成人员（审判长ruby、审判员A luna、审判员B leopard）及公诉人、辩护律师；4. 告知诉讼权利。最后宣布法庭调查正式开始！"
    },
    {
        "stage_id": 1,
        "stage_name": "【阶段 1 · 法庭调查 - 控方起诉举证】",
        "role": "⚖️ 首席公诉人",
        "team": "prosecutor",
        "agent": "topaz",
        "node": "raccoon",
        "model": "topaz-deepseek-v4-flash",
        "instruction": "你是【首席公诉人】。在法庭调查阶段宣读起诉书：尊长身为中煤高管，其社会信用与职务身份在法律上不可切割。普通老人无法瞬间撬动千万资金，这笔拆借本质上是利用职务影响力为私企定向输血，越过了公私红线，构成了对合规底线的侵犯。"
    },
    {
        "stage_id": 1,
        "stage_name": "【阶段 1 · 法庭调查 - 控方补充举证】",
        "role": "⚖️ 第一助理公诉人",
        "team": "prosecutor",
        "agent": "carbonado",
        "node": "pve2",
        "model": "carbonado-deepseek-v4-flash",
        "instruction": "你是【第一助理公诉人】。举证说明：权力和职务影响力就像水渗入沙土，公钱虽未动，但国企高管用自身影响力为私企背书，就是在制造‘破窗效应’！"
    },
    {
        "stage_id": 2,
        "stage_name": "【阶段 2 · 法庭调查 - 辩方质证与反证】",
        "role": "🛡️ 首席辩护律师",
        "team": "defense",
        "agent": "diamond",
        "node": "pve",
        "model": "diamond-deepseek-v4-flash",
        "instruction": "你是【首席辩护律师】。在法庭质证阶段直接驳斥控方证据！掏出《极昼.md》中的【四大罪名穷尽式排除矩阵】：1.受贿罪（资金逆向借出无对价）；2.滥用职权罪（未动用公章资金，零国家损失）；3.贪污罪（账目纯洁）；4.高利转贷/非吸（非信贷资金）。出示1000万10次平价还本水单，证明公款零亏空！"
    },
    {
        "stage_id": 2,
        "stage_name": "【阶段 2 · 法庭调查 - 辩方法理质证】",
        "role": "🛡️ 第一助理辩护律师",
        "team": "defense",
        "agent": "argentite",
        "node": "pve3",
        "model": "argentite-deepseek-v4-flash",
        "instruction": "你是【第一助理辩护律师】。质证控方的适用法律错误：引用《刑法》第12条“从旧兼从轻”原则，行为发生于2016年2月，控方套用2016年4月新司法解释中‘感情投资/事后感谢’的拟制罪名，属于违宪的溯及既往！在2003纪要标准下罪名绝对不成立！"
    },
    {
        "stage_id": 3,
        "stage_name": "【阶段 3 · 法庭辩论与法官质询】",
        "role": "⚖️ 第二助理公诉人",
        "team": "prosecutor",
        "agent": "quartz",
        "node": "pbs3",
        "model": "quartz-deepseek-v4-flash",
        "instruction": "你是【第二助理公诉人】。在法庭辩论阶段发言：防范隐形权力寻租是现代国企治理的核心。规则不能为个案同情打折！"
    },
    {
        "stage_id": 3,
        "stage_name": "【阶段 3 · 法庭辩论与法官质询】",
        "role": "🛡️ 第二助理辩护律师",
        "team": "defense",
        "agent": "agate",
        "node": "xgp",
        "model": "agate-deepseek-v4-flash",
        "instruction": "你是【第二助理辩护律师】。在法庭辩论阶段发言：还原2015-2016山河四省最冷冬天的真实悲壮背景（螺纹钢1600/焦煤300）。尊长是在社会结构即将倾覆时用肉身和信用撑住承重梁。法律不能背叛正义！"
    },
    {
        "stage_id": 3,
        "stage_name": "【阶段 3 · 法庭辩论与法官质询】",
        "role": "🏛️ 审判员 A (常理质询)",
        "team": "judge",
        "agent": "luna",
        "node": "onecloud2",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是合议庭【审判员A】。展开法庭质询：追问控方‘如果私人自筹资金平进平出且无一分公款损失都要定罪，法的温度何在？’同时追问辩方‘如何证明社会人脉与职务背景完全切割？’"
    },
    {
        "stage_id": 4,
        "stage_name": "【阶段 4 · 控辩最后陈述】",
        "role": "🏛️ 审判员 B (法理质询)",
        "team": "judge",
        "agent": "leopard",
        "node": "suse",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是合议庭【审判员B】。要求控辩双方做最后程序陈述：控方起诉书认定的罪名满足哪一条法定构成要件？辩方从旧兼从轻在2016年2月行为着手点的具体适用界限。"
    },
    {
        "stage_id": 5,
        "stage_name": "【阶段 5 · 合议庭评议与终审宣判】",
        "role": "🏛️ 审判长 (终审宣判)",
        "team": "judge",
        "agent": "ruby",
        "node": "nuc",
        "model": "nova-deepseek-v4-flash-aggr",
        "instruction": "你是【审判长】。请综合控辩双方辩论、四罪排除矩阵、从旧兼从轻原则以及合议庭评议结果，做出最终法庭判决！敲响法槌，宣告尊长无罪或裁定结果，发表发人深省、震撼人心的宣判判词！"
    }
]

# 当前进度的 session state
if "current_stage_id" not in st.session_state:
    st.session_state.current_stage_id = 0

# 动态生成 Top Sticky Banner CSS 与 HTML
def render_sticky_top_banner(active_stage_id):
    segments_html = ""
    for stage in STAGES:
        # 判断段落状态：已完成(green)、正在进行(gold/orange)、未开始(gray)
        if stage["id"] < active_stage_id:
            color = "#4CAF50" # 已完成
        elif stage["id"] == active_stage_id:
            color = "#FF9800" # 正在进行
        else:
            color = "#444444" # 未开始
            
        segments_html += f'<div style="flex: 1; height: 8px; border-radius: 4px; background-color: {color}; transition: all 0.3s;"></div>'
        
    titles_html = ""
    for stage in STAGES:
        style = "color: #FF9800; font-weight: bold;" if stage["id"] == active_stage_id else ("color: #81C784;" if stage["id"] < active_stage_id else "color: #777;")
        titles_html += f'<span style="{style}">{stage["emoji"]} {stage["name"]}</span>'

    banner_html = f"""
    <div style="position: sticky; top: 0rem; z-index: 99999; background: #121214; border-bottom: 2px solid #FF9800; padding: 10px 16px; margin-bottom: 1rem; border-radius: 0 0 8px 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.5);">
      <div style="display: flex; gap: 8px; margin-bottom: 8px;">
        {segments_html}
      </div>
      <div style="display: flex; justify-content: space-between; font-size: 0.82rem; overflow-x: auto;">
        {titles_html}
      </div>
    </div>
    """
    st.markdown(banner_html, unsafe_allow_html=True)

# 渲染 Top Banner
render_sticky_top_banner(st.session_state.current_stage_id)

st.markdown('<h1 style="text-align:center;color:#E65100;">⚖️ 鲲鹏志 · 《极昼》案 9 席位标准刑事法庭</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center;color:#777;">油管分段式 Top Sticky Banner + 6 阶段刑事庭审全流程</p>', unsafe_allow_html=True)

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
    
    st.markdown("#### 🔴 控方公诉团队")
    st.caption("• 首席公诉: `topaz` @ `raccoon`")
    st.caption("• 助理公诉1: `carbonado` @ `pve2`")
    st.caption("• 助理公诉2: `quartz` @ `pbs3`")
    
    st.markdown("#### 🔵 辩护律师团队")
    st.caption("• 首席辩护: `diamond` @ `pve`")
    st.caption("• 辩护助理1: `argentite` @ `pve3`")
    st.caption("• 辩护助理2: `agate` @ `xgp`")
    
    st.divider()
    st.caption(f"网关: `{OPENAI_BASE_URL}`")

article_text = load_research_file("research/极昼.md")

with st.expander("📌 标准刑事庭审 6 阶段说明与 55KB 案卷", expanded=True):
    st.markdown("### **案由：尊长自筹资金救助亲家企业涉嫌犯罪案**")
    col1, col2 = st.columns(2)
    with col1:
        st.info("**庭审程序**：0.初始化 -> 1.控方举证 -> 2.辩方质证 -> 3.法庭辩论 -> 4.最后陈述 -> 5.终审宣判")
    with col2:
        st.success("**实体法争点**：四大罪名排除矩阵、从旧兼从轻、私人信用 vs 职务影响混同。")
        
    if article_text:
        st.markdown(f'<div style="background:#f8f9fa;padding:10px;border-left:4px solid #FF9800;font-size:0.88rem;max-height:180px;overflow-y:auto;">{article_text[:2500]}...\n\n*(共 {len(article_text)} 字符全量案卷)*</div>', unsafe_allow_html=True)

st.divider()

col_btn1, col_btn2 = st.columns([2, 1])
with col_btn1:
    start_btn = st.button("⚖️ 敲响法槌 · 开启标准刑事庭审 (0~5 阶段)", type="primary", use_container_width=True)
with col_btn2:
    clear_btn = st.button("🧹 清空庭审笔录", use_container_width=True)

if clear_btn:
    st.session_state.messages = []
    st.session_state.current_stage_id = 0
    st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown("### 📜 标准刑事庭审笔录（永久驻留显示）")
chat_container = st.container()

with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar=msg.get("avatar", "⚖️")):
            st.markdown(f"### {msg['header']}")
            st.markdown(msg["content"])

if start_btn:
    st.session_state.messages = []
    st.session_state.current_stage_id = 0
    client = openai.OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)
    
    progress_bar = st.progress(0, text="正在敲响法槌，初始化法庭...")
    
    for i, seat in enumerate(COURT_SEATS, 1):
        st.session_state.current_stage_id = seat["stage_id"]
        seat_header = f"{seat['stage_name']} {seat['role']} ({seat['agent']} @ {seat['node']})"
        
        progress_bar.progress(i / len(COURT_SEATS), text=f"庭审推进 [{seat['stage_name']}] {seat['role']} ...")
        
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
            f"💥 刑事庭审严肃指令：\n"
            f"1. 以极其专业、严肃的刑事法庭语言陈词！\n"
            f"2. 如果你前面有发言者，第一句话必须直接回应/驳斥前一位发言人的核心漏洞！如果是审判长开庭初始化，则严禁反驳任何人！\n"
            f"3. 充分引用《极昼.md》中的案卷证据（水单、四大罪名排除、刑法第12条从旧兼从轻）进行庭审攻防！\n"
            f"4. 字数控制在 350 字以内。"
        )

        system_prompt = (
            "【刑事庭审学术研讨沙盒】你正在参加高校法学院 9 席位标准刑事模拟法庭《极昼》案公开审理。"
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
            content = f"（{seat_header} 连线超时: {e}）"
            
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
                
    st.session_state.current_stage_id = 5
    progress_bar.progress(1.0, text="⚖️ 刑事庭审 6 阶段全部结束，宣判下达！庭审笔录已永久驻留！")
    st.balloons()
    st.rerun()

st.divider()
st.markdown(
    "<div style='text-align:center;color:#888;font-size:0.85rem;padding:1.5rem 0;'>"
    "🦅 鲲鹏志 AI · 9 席位刑事模拟法庭平台 · 2026"
    "</div>",
    unsafe_allow_html=True
)

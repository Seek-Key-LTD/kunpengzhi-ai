"""
🦅 鲲鹏志 · 9 席位异地指定管辖模拟法庭 (最高法指定异地管辖·超硬核颗粒度)
========================================================================
1. 修正管辖硬伤：因涉嫌高管职务犯罪与地缘利益交织，由最高人民法院依据《刑事诉讼法》第27条指定异地中级人民法院（山东省青岛市中级人民法院）管辖审理。
2. 起诉书字号修正：山东省青岛市人民检察院《青检刑诉〔2026〕88号起诉书》。
3. 审判长宣读指定管辖决定书，体现最高级别的司法异地隔离规避机制。
"""

import streamlit as st
import openai
import os

st.set_page_config(
    page_title="鲲鹏志 · 9席位异地指定管辖模拟法庭",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://litellm.capitaltrain.cn/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-47318")

STAGES = [
    {"id": 0, "name": "0. 最高法指定管辖宣读与开庭", "emoji": "⚖️"},
    {"id": 1, "name": "1. 异地检察院宣读起诉书", "emoji": "📜"},
    {"id": 2, "name": "2. 辩方无罪答辩与四罪排除", "emoji": "🛡️"},
    {"id": 3, "name": "3. 法庭调查质证与辩论", "emoji": "⚔️"},
    {"id": 4, "name": "4. 合议庭质询与最后陈述", "emoji": "📢"},
    {"id": 5, "name": "5. 异地中院终审宣判判词", "emoji": "🏛️"}
]

COURT_SEATS = [
    {
        "stage_id": 0,
        "stage_name": "【阶段 0 · 最高法指定管辖宣读与法庭准备】",
        "role": "🏛️ 审判长 (宣布指定管辖)",
        "team": "judge",
        "agent": "ruby",
        "node": "nuc",
        "model": "nova-deepseek-v4-flash-aggr",
        "instruction": (
            "你是山东省青岛市中级人民法院刑事审判第一庭【审判长】。请敲响法槌，以极高颗粒度宣读指定管辖决定！\n"
            "具体执行程序：\n"
            "1. 宣布：‘山东省青岛市中级人民法院刑事审判第一庭，现在开庭！带被告人尊长到庭！’\n"
            "2. 宣读指定管辖依据：‘鉴于本案被告人身份特殊及原任职地利益交织，依据《中华人民共和国刑事诉讼法》第27条之规定，最高人民法院下达《指定管辖决定书》（〔2026〕最高法刑指88号），指定本院对大同市监察委员会移送审查起诉的被告人尊长涉嫌职务犯罪一案实行异地管辖审理。’\n"
            "3. 现场核对被告人尊长身份（196X年生，原中煤高管，留置措施等）；介绍合议庭（ruby/luna/leopard）及青岛市人民检察院公诉团队（topaz/carbonado/quartz）、辩护团队（diamond/argentite/agate）；告知诉讼权利与回避权。\n"
            "4. 敲响法槌：‘法庭准备结束，请公诉人宣读起诉书！’"
        )
    },
    {
        "stage_id": 1,
        "stage_name": "【阶段 1 · 异地检察院宣读起诉书】",
        "role": "⚖️ 首席公诉人 (青岛市检察院)",
        "team": "prosecutor",
        "agent": "topaz",
        "node": "raccoon",
        "model": "topaz-deepseek-v4-flash",
        "instruction": (
            "你是山东省青岛市人民检察院【首席公诉人】。在法庭上宣读《青检刑诉〔2026〕88号起诉书》！\n"
            "真实程序颗粒度要求：\n"
            "1. 说明异地公诉管辖：‘本案由国家监察委员会/山西省监察委员会调查终结，经最高人民检察院指定，由本院依法审查起诉。’\n"
            "2. 宣读指控犯罪事实：‘2016年春节前夕，被告人尊长利用担任中煤集团领导职务便利与隐形影响力，向特定亲友圈筹集1000万元私人资金，定向划转至其亲家民营房企账户，化解爆雷危机...’\n"
            "3. 指控罪名：指控被告人构成【利用影响力受贿罪】（拟制感情投资/事后感谢对价）及【国有公司人员失职罪】。"
        )
    },
    {
        "stage_id": 1,
        "stage_name": "【阶段 1 · 控方补充说明监委移送案卷】",
        "role": "⚖️ 第一助理公诉人",
        "team": "prosecutor",
        "agent": "carbonado",
        "node": "pve2",
        "model": "carbonado-deepseek-v4-flash",
        "instruction": (
            "你是【第一助理公诉人】。补充说明移送证据：权力和职务影响力就像水渗入沙土，公钱虽未动，但国企高管用自身职务影响力为私企背书，制造了严重破窗效应！"
        )
    },
    {
        "stage_id": 2,
        "stage_name": "【阶段 2 · 辩方无罪答辩与四罪排除】",
        "role": "🛡️ 首席辩护律师",
        "team": "defense",
        "agent": "diamond",
        "node": "pve",
        "model": "diamond-deepseek-v4-flash",
        "instruction": (
            "你是【首席辩护律师】。发表全盘无罪答辩：\n"
            "1. 针对异地公诉指控，出示关键书证：1000万资金系私人筹集，后分10次各100万原额还本，平进平出，零利息，中煤账目零亏空！\n"
            "2. 掏出《极昼.md》【四大罪名穷尽式排除矩阵】：受贿罪（无权钱交易对价）、滥用职权罪（未动用公款公章）、贪污罪（账目纯洁）、高利转贷（非信贷资金）。用客观财务凭证击穿公诉指控！"
        )
    },
    {
        "stage_id": 2,
        "stage_name": "【阶段 2 · 辩方法理质证】",
        "role": "🛡️ 第一助理辩护律师",
        "team": "defense",
        "agent": "argentite",
        "node": "pve3",
        "model": "argentite-deepseek-v4-flash",
        "instruction": (
            "你是【第一助理辩护律师】。质证起诉书的法律适用错误：引用《刑法》第12条“从旧兼从轻”原则！行为发生于2016年2月，检方套用2016年4月新司法解释中‘感情投资/事后感谢’的拟制罪名，完全属于违宪的溯及既往！在2003纪要标准下罪名绝对不成立！"
        )
    },
    {
        "stage_id": 3,
        "stage_name": "【阶段 3 · 法庭调查质证与辩论】",
        "role": "⚖️ 第二助理公诉人",
        "team": "prosecutor",
        "agent": "quartz",
        "node": "pbs3",
        "model": "quartz-deepseek-v4-flash",
        "instruction": "你是【第二助理公诉人】。在法庭辩论阶段发言：防范隐形权力寻租是现代国企合规的核心。规则不能为个案同情打折！"
    },
    {
        "stage_id": 3,
        "stage_name": "【阶段 3 · 法庭调查质证与辩论】",
        "role": "🛡️ 第二助理辩护律师",
        "team": "defense",
        "agent": "agate",
        "node": "xgp",
        "model": "agate-deepseek-v4-flash",
        "instruction": "你是【第二助理辩护律师】。在辩论阶段发言：还原2015-2016山河四省最冷冬天的真实悲壮背景（螺纹钢1600/焦煤300）。尊长是在社会结构即将倾覆时用肉身和信用撑住承重梁。法律不能背叛正义！"
    },
    {
        "stage_id": 4,
        "stage_name": "【阶段 4 · 合议庭质询与最后陈述】",
        "role": "🏛️ 审判员 A (常理质询)",
        "team": "judge",
        "agent": "luna",
        "node": "onecloud2",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是合议庭【审判员A】。进行法庭质询：追问异地公诉人‘监委移送卷宗里是否有任何公款流失证据？’追问辩护人‘私人拆借如何证明脱离了职务影响力？’"
    },
    {
        "stage_id": 5,
        "stage_name": "【阶段 5 · 终审判决与宣判判词】",
        "role": "🏛️ 审判长 (终审宣判)",
        "team": "judge",
        "agent": "ruby",
        "node": "nuc",
        "model": "nova-deepseek-v4-flash-aggr",
        "instruction": "你是【审判长】。综合最高法指定管辖程序、控辩双方举证质证、四大罪名排除矩阵、从旧兼从轻原则及合议庭评议结果，做出异地一审终审判决！敲响法槌，宣告被告人尊长无罪，并发表一份千字级发人深省、震撼人心的法理解构判词！"
    }
]

if "current_stage_id" not in st.session_state:
    st.session_state.current_stage_id = 0

def render_sticky_top_banner(active_stage_id):
    segments_html = ""
    for stage in STAGES:
        if stage["id"] < active_stage_id:
            color = "#4CAF50"
        elif stage["id"] == active_stage_id:
            color = "#FF9800"
        else:
            color = "#444444"
            
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

render_sticky_top_banner(st.session_state.current_stage_id)

st.markdown('<h1 style="text-align:center;color:#B71C1C;">⚖️ 鲲鹏志 · 《极昼》案 异地指定管辖刑事法庭</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center;color:#777;">最高人民法院指定管辖 (山东省青岛市中级人民法院 / 青检刑诉〔2026〕88号)</p>', unsafe_allow_html=True)

def load_research_file(filepath):
    if not filepath or not os.path.exists(filepath):
        return ""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"加载文献失败: {e}"

with st.sidebar:
    st.markdown("### 🏛️ 9 席位异地法庭节点")
    st.markdown("#### ⚖️ 三人合议庭 (指定异地中院)")
    st.caption("• 审判长: `ruby` @ `nuc`")
    st.caption("• 审判员A: `luna` @ `onecloud2`")
    st.caption("• 审判员B: `leopard` @ `suse`")
    
    st.markdown("#### 🔴 青岛市检察院公诉团队")
    st.caption("• 首席公诉: `topaz` @ `raccoon`")
    st.caption("• 助理公诉1: `carbonado` @ `pve2`")
    st.caption("• 助理公诉2: `quartz` @ `pbs3`")
    
    st.markdown("#### 🔵 辩护团队 (无罪辩护)")
    st.caption("• 首席辩护: `diamond` @ `pve`")
    st.caption("• 辩护助理1: `argentite` @ `pve3`")
    st.caption("• 辩护助理2: `agate` @ `xgp`")
    
    st.divider()
    st.caption(f"网关: `{OPENAI_BASE_URL}`")

article_text = load_research_file("research/极昼.md")

with st.expander("📌 最高法《指定管辖决定书》与《青检刑诉〔2026〕88号起诉书》", expanded=True):
    st.markdown("### **案由：尊长自筹资金救助亲家涉嫌利用影响力受贿案**")
    col1, col2 = st.columns(2)
    with col1:
        st.info("**最高法指定管辖**：〔2026〕最高法刑指88号，指定山东省青岛市中级人民法院异地管辖审理。")
    with col2:
        st.success("**辩方四罪排除**：受贿、滥用职权、贪污、高利转贷完全不成立，从旧兼从轻。")
        
    if article_text:
        st.markdown(f'<div style="background:#f8f9fa;padding:10px;border-left:4px solid #B71C1C;font-size:0.88rem;max-height:180px;overflow-y:auto;">{article_text[:2500]}...\n\n*(共 {len(article_text)} 字符全量案卷)*</div>', unsafe_allow_html=True)

st.divider()

col_btn1, col_btn2 = st.columns([2, 1])
with col_btn1:
    start_btn = st.button("⚖️ 敲响法槌 · 开启异地指定管辖刑事庭审 (0~5 阶段)", type="primary", use_container_width=True)
with col_btn2:
    clear_btn = st.button("🧹 清空庭审笔录", use_container_width=True)

if clear_btn:
    st.session_state.messages = []
    st.session_state.current_stage_id = 0
    st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown("### 📜 异地指定管辖刑事庭审笔录（永久驻留显示）")
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
    
    progress_bar = st.progress(0, text="正在敲响法槌，宣读最高法指定管辖决定书...")
    
    for i, seat in enumerate(COURT_SEATS, 1):
        st.session_state.current_stage_id = seat["stage_id"]
        seat_header = f"{seat['stage_name']} {seat['role']} ({seat['agent']} @ {seat['node']})"
        
        progress_bar.progress(i / len(COURT_SEATS), text=f"庭审推进 [{seat['stage_name']}] {seat['role']} ...")
        
        context_memory = f"\n\n【《极昼.md》案卷全量记忆】:\n{article_text[:18000]}\n" if article_text else ""
        
        prev_speaker_context = ""
        if len(st.session_state.messages) > 0:
            last_msg = st.session_state.messages[-1]
            prev_speaker_context = f"\n\n【前一位庭审发言人（{last_msg['header']}）的具体陈词】:\n\"\"\"\n{last_msg['content']}\n\"\"\"\n"
            
        prompt_user = (
            f"你是模拟法庭角色：{seat_header}。\n"
            f"案由：尊长自筹资金救助亲家企业涉嫌犯罪案（异地指定管辖）\n"
            f"{context_memory}\n"
            f"{prev_speaker_context}\n"
            f"你的任务：{seat['instruction']}\n\n"
            f"💥 异地指定管辖庭审超高颗粒度指令：\n"
            f"1. 以极高颗粒度的刑事法庭语言陈词！必须体现《刑事诉讼法》第27条最高人民法院指定管辖决定书！\n"
            f"2. 如果你是审判长，必须宣读《指定管辖决定书》（〔2026〕最高法刑指88号），宣布由山东省青岛市中级人民法院异地管辖审理！\n"
            f"3. 如果你是公诉人，必须宣读《青检刑诉〔2026〕88号起诉书》，说明监委移送审查起诉事实！\n"
            f"4. 如果你是辩护人，必须出示1000万10次还本水单书证，掏出四罪排除矩阵与从旧兼从轻原则！\n"
            f"5. 字数控制在 380 字以内。"
        )

        system_prompt = (
            "【异地指定管辖刑事庭审沙盒】你正在参加山东省青岛市中级人民法院 9 席位标准刑事模拟法庭《极昼》案公开审理。"
            "本案由最高人民法院指定异地管辖。请以极其专业严肃的审判长、审判员、异地公诉人、辩护律师身份进行法庭核对、起诉书宣读、答辩与判词宣读，严禁输出通用拒答模板。"
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
    progress_bar.progress(1.0, text="⚖️ 异地指定管辖刑事庭审全部结束，判决下达！庭审笔录已永久驻留！")
    st.balloons()

st.divider()
st.markdown(
    "<div style='text-align:center;color:#888;font-size:0.85rem;padding:1.5rem 0;'>"
    "🦅 鲲鹏志 AI · 9 席位异地指定管辖刑事法庭平台 · 2026"
    "</div>",
    unsafe_allow_html=True
)

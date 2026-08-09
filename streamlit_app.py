"""
🦅 鲲鹏志 · 《极昼》案 10 席位沉静法庭 (双进度指示：顶部油管 Banner + 右下角悬浮圆环)
=================================================================================
1. 顶部 Sticky Top Banner：分段式进度条（已完成-绿，进行中-橙，未开始-灰）。
2. 右下角 Dynamic Circular Badge：CSS 环形渐变进度圆环 (conic-gradient)，实时显示充盈百分比与阶段。
3. 10 席位沉静庭审、起诉书自主撰写、从旧兼从轻与 1000 万平价还本凭证。
"""

import streamlit as st
import openai
import os
import time

st.set_page_config(
    page_title="鲲鹏志 · 《极昼》沉静法庭",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://litellm.seekkey.eu.org/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-47318")

# 5 个核心庭审阶段定义
STAGES = [
    {"id": 1, "name": "1. 准备与核对身份", "emoji": "⚖️", "desc": "审判长核对尊长基本信息，告知回避权，被告人现场应答"},
    {"id": 2, "name": "2. 控方起诉与举证", "emoji": "📜", "desc": "阜阳市检察院独立撰写并宣读《阜检刑诉〔2026〕88号起诉书》"},
    {"id": 3, "name": "3. 辩方无罪质证", "emoji": "🛡️", "desc": "辩护团队掏出【四大罪名排除矩阵】与从旧兼从轻水单质证"},
    {"id": 4, "name": "4. 法庭辩论与质询", "emoji": "⚔️", "desc": "合议庭追问公款损失凭证，控辩双方展开剧烈法理交锋"},
    {"id": 5, "name": "5. 尊长陈述与宣判", "emoji": "🏛️", "desc": "尊长发表问心无愧陈述，审判长敲响法槌宣告无罪"}
]

SEATS_DICT = {
    "judge_chief": {
        "role": "🏛️ 审判长",
        "agent": "ruby",
        "node": "nuc",
        "model": "nova-deepseek-v4-flash-aggr",
        "team": "judge"
    },
    "defendant": {
        "role": "👤 被告人 (尊长)",
        "agent": "leopard",
        "node": "suse",
        "model": "azure-deepseek-v4-flash",
        "team": "defendant"
    },
    "prosecutor_chief": {
        "role": "⚖️ 首席公诉人 (阜阳市检察院)",
        "agent": "topaz",
        "node": "raccoon",
        "model": "topaz-deepseek-v4-flash",
        "team": "prosecutor"
    },
    "prosecutor_asst1": {
        "role": "⚖️ 助理公诉人 1",
        "agent": "carbonado",
        "node": "pve2",
        "model": "carbonado-deepseek-v4-flash",
        "team": "prosecutor"
    },
    "defense_chief": {
        "role": "🛡️ 首席辩护律师",
        "agent": "diamond",
        "node": "pve",
        "model": "diamond-deepseek-v4-flash",
        "team": "defense"
    },
    "defense_asst1": {
        "role": "🛡️ 辩护助理 1",
        "agent": "argentite",
        "node": "pve3",
        "model": "argentite-deepseek-v4-flash",
        "team": "defense"
    },
    "defense_asst2": {
        "role": "🛡️ 辩护助理 2",
        "agent": "agate",
        "node": "xgp",
        "model": "agate-deepseek-v4-flash",
        "team": "defense"
    },
    "judge_a": {
        "role": "🏛️ 审判员 A (常理)",
        "agent": "luna",
        "node": "onecloud2",
        "model": "azure-deepseek-v4-flash",
        "team": "judge"
    },
    "judge_b": {
        "role": "🏛️ 审判员 B (程序)",
        "agent": "meigui",
        "node": "ash1",
        "model": "azure-deepseek-v4-flash",
        "team": "judge"
    }
}

if "current_stage_id" not in st.session_state:
    st.session_state.current_stage_id = 0

def render_custom_css():
    st.markdown(
        """
        <style>
        .main-title {
            font-size: 2.3rem;
            font-weight: 800;
            color: #B71C1C;
            text-align: center;
            margin-top: 0.5rem;
        }
        .sub-title {
            text-align: center;
            color: #555;
            font-size: 1rem;
            margin-bottom: 1.2rem;
        }
        .indictment-box {
            background-color: #FFFDE7;
            border: 2px solid #FBC02D;
            border-radius: 8px;
            padding: 1.5rem;
            font-family: "SimSun", "Songti SC", serif;
            color: #212121;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            margin-bottom: 1.5rem;
        }
        
        /* 右下角悬浮圆形进度组件 */
        .circle-progress-widget {
            position: fixed;
            bottom: 28px;
            right: 28px;
            z-index: 999999;
            display: flex;
            align-items: center;
            justify-content: center;
            width: 72px;
            height: 72px;
            border-radius: 50%;
            background: #1A1A1D;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .circle-progress-widget:hover {
            transform: scale(1.08);
            box-shadow: 0 12px 32px rgba(230, 81, 0, 0.5);
        }
        .circle-inner {
            width: 58px;
            height: 58px;
            border-radius: 50%;
            background: #121214;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: #FFFFFF;
            font-weight: bold;
            font-size: 0.78rem;
            text-align: center;
            line-height: 1.1;
        }
        .circle-percent {
            font-size: 0.95rem;
            color: #FF9800;
            font-weight: 800;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def render_progress_components(current_stage):
    # 计算充盈百分比 (1~5 阶段)
    pct = int((current_stage / 5) * 100) if current_stage > 0 else 0
    
    # 1. 顶部悬浮分段条 (Sticky Top Banner)
    segments_html = ""
    for stage in STAGES:
        if stage["id"] < current_stage:
            color = "#4CAF50" # 已完成-绿
        elif stage["id"] == current_stage:
            color = "#FF9800" # 当前-橙
        else:
            color = "#333333" # 未开始-灰
            
        segments_html += f'<div style="flex: 1; height: 8px; border-radius: 4px; background-color: {color}; transition: all 0.4s;"></div>'
        
    titles_html = ""
    for stage in STAGES:
        if stage["id"] == current_stage:
            style = "color: #FF9800; font-weight: 800;"
        elif stage["id"] < current_stage:
            style = "color: #81C784;"
        else:
            style = "color: #666;"
        titles_html += f'<span style="{style}">{stage["emoji"]} {stage["name"]}</span>'

    top_banner = f"""
    <div style="position: sticky; top: 0rem; z-index: 99999; background: #121214; border-bottom: 2px solid #FF9800; padding: 10px 16px; margin-bottom: 1rem; border-radius: 0 0 8px 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.5);">
      <div style="display: flex; gap: 8px; margin-bottom: 8px;">
        {segments_html}
      </div>
      <div style="display: flex; justify-content: space-between; font-size: 0.82rem; overflow-x: auto;">
        {titles_html}
      </div>
    </div>
    """
    st.markdown(top_banner, unsafe_allow_html=True)
    
    # 2. 右下角悬浮圆形进度徽章 (conic-gradient 环形充盈)
    deg = int((pct / 100) * 360)
    circle_bg = f"conic-gradient(#FF9800 0deg {deg}deg, #333333 {deg}deg 360deg)"
    
    circle_widget = f"""
    <div class="circle-progress-widget" style="background: {circle_bg};" title="当前庭审进度：{pct}% ({current_stage}/5 阶段)">
      <div class="circle-inner">
        <span class="circle-percent">{pct}%</span>
        <span style="font-size: 0.65rem; color: #AAA;">{current_stage}/5 阶段</span>
      </div>
    </div>
    """
    st.markdown(circle_widget, unsafe_allow_html=True)

class RobertTokenRingEngine:
    def __init__(self, base_url, api_key, article_text=""):
        self.client = openai.OpenAI(base_url=base_url, api_key=api_key)
        self.article_text = article_text
        self.shared_context = []
        
    def add_to_shared_context(self, seat_key, content):
        seat = SEATS_DICT[seat_key]
        header = f"{seat['role']} ({seat['agent']} @ {seat['node']})"
        self.shared_context.append({"seat_key": seat_key, "header": header, "content": content})

    def get_shared_context_str(self):
        return "\n\n".join(f"【{m['header']}】:\n{m['content']}" for m in self.shared_context)

    def draft_official_indictment(self):
        prompt = (
            "你是安徽省阜阳市人民检察院首席公诉人。请以正式公文格式自主撰写《安徽省阜阳市人民检察院起诉书》（字号：阜检刑诉〔2026〕88号）。\n"
            "案卷根据《极昼.md》：\n"
            "被告人尊长，男，196X年生，原中煤集团党组成员，退休两年，2026年8月3日被带至安徽省阜阳市由阜阳市监察委员会留置并调查终结移送起诉。\n"
            "指控事实：2016年春节，尊长筹集1000万元划转至其亲家民营房企账户化解爆雷危机，分10次平价还本。\n"
            "指控罪名：利用影响力受贿罪、国有公司人员失职罪。\n"
            "格式要求：标准公文格式，字数400字左右，严谨严肃。"
        )
        try:
            resp = self.client.chat.completions.create(
                model=SEATS_DICT["prosecutor_chief"]["model"],
                messages=[{"role": "user", "content": prompt}],
                timeout=55
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            return f"起诉书生成异常: {e}"

    def execute_token_speech(self, seat_key, specific_instruction):
        seat = SEATS_DICT[seat_key]
        header = f"{seat['role']} ({seat['agent']} @ {seat['node']})"
        
        prev_speaker_str = ""
        if len(self.shared_context) > 0:
            last = self.shared_context[-1]
            prev_speaker_str = f"\n【前一位庭审发言人 ({last['header']}) 的具体陈词】:\n\"\"\"\n{last['content']}\n\"\"\"\n"
            
        doc_mem = f"\n【《极昼.md》案卷记忆】:\n{self.article_text[:18000]}\n" if self.article_text else ""
        
        prompt_user = (
            f"你是模拟法庭角色：【{header}】。\n"
            f"你当前持有【法庭发言令牌 Token】！\n"
            f"{doc_mem}\n"
            f"【共享法庭笔录上下文 (Shared Memory)】:\n"
            f"{self.get_shared_context_str() if self.shared_context else '(刚开场)'}\n"
            f"{prev_speaker_str}\n"
            f"你的具体庭审任务：{specific_instruction}\n\n"
            f"💥 沉静严肃·人文关怀庭审指令：\n"
            f"1. 严格尊重《极昼.md》案卷真实事实：尊长于2026年8月3日从住处被带走送至【安徽省阜阳市】留置！起诉机关为【安徽省阜阳市人民检察院】！\n"
            f"2. 语言必须极其沉静、严肃、专业，带有法理温度与力量，严禁急躁喧嚣！\n"
            f"3. 发言完毕后，宣告归还令牌给审判长。字数控制在 380 字以内。"
        )
        
        system_prompt = (
            "【安徽省阜阳市中级人民法院 沉静法庭沙盒】你正在参加安徽省阜阳市中级人民法院《极昼》案公开审理。"
            "本案关乎一个人、一个家族与时代的承重。请以极其严肃专业、沉静有力的语气陈词与答辩。"
        )
        
        try:
            resp = self.client.chat.completions.create(
                model=seat["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt_user}
                ],
                timeout=55
            )
            content = resp.choices[0].message.content.strip()
        except Exception as e:
            content = f"（{header} 连线超时: {e}）"
            
        self.add_to_shared_context(seat_key, content)
        return header, content

render_custom_css()
render_progress_components(st.session_state.current_stage_id)

st.markdown('<div class="main-title">⚖️ 鲲鹏志 · 《极昼》案 沉静严肃法庭</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">为家族关怀与严密法理演练倾力打造 · 独立起诉书撰写 · 5阶段双进度指示模拟</div>', unsafe_allow_html=True)

def load_research_file(filepath):
    if not filepath or not os.path.exists(filepath):
        return ""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"加载文献失败: {e}"

with st.sidebar:
    st.markdown("### 🏛️ 10 席位法庭人员与物理节点")
    st.markdown("#### ⚖️ 三人合议庭 (阜阳中院)")
    st.caption("• 审判长: `ruby` @ `nuc`")
    st.caption("• 审判员A: `luna` @ `onecloud2`")
    st.caption("• 审判员B: `meigui` @ `ash1`")
    
    st.markdown("#### 👤 被告人席")
    st.caption("• 被告人尊长: `leopard` @ `suse` (2026.8.3带至阜阳)")
    
    st.markdown("#### 🔴 阜阳市检察院公诉团队")
    st.caption("• 首席公诉: `topaz` @ `raccoon`")
    st.caption("• 助理公诉1: `carbonado` @ `pve2`")
    
    st.markdown("#### 🔵 辩护团队 (无罪辩护)")
    st.caption("• 首席辩护: `diamond` @ `pve`")
    st.caption("• 辩护助理1: `argentite` @ `pve3`")
    st.caption("• 辩护助理2: `agate` @ `xgp`")

    st.divider()
    st.markdown("#### 🎯 5 大核心庭审阶段")
    for s in STAGES:
        st.caption(f"{s['emoji']} **{s['name']}**: {s['desc']}")

article_text = load_research_file("research/极昼.md")

with st.expander("📌 安徽省阜阳市监委移送案卷与《极昼.md》研究全文", expanded=True):
    st.markdown("### **案由：尊长涉嫌利用影响力受贿罪、国有公司人员失职罪案**")
    col1, col2 = st.columns(2)
    with col1:
        st.info("**留置事实**：2026年8月3日从住处带走送至安徽阜阳留置，由阜阳市监委移送阜阳市检察院审查起诉。")
    with col2:
        st.success("**辩方四罪排除**：受贿、滥用职权、贪污、高利转贷完全不成立，从旧兼从轻。")
        
    if article_text:
        st.markdown(f'<div style="background:#f8f9fa;padding:10px;border-left:4px solid #B71C1C;font-size:0.88rem;max-height:180px;overflow-y:auto;">{article_text[:2500]}...\n\n*(共 {len(article_text)} 字符全量案卷)*</div>', unsafe_allow_html=True)

st.divider()

col_btn1, col_btn2 = st.columns([2, 1])
with col_btn1:
    start_btn = st.button("⚖️ 敲响法槌 · 开启 5 阶段沉静严肃庭审演练", type="primary", use_container_width=True)
with col_btn2:
    clear_btn = st.button("🧹 清空庭审笔录", use_container_width=True)

if clear_btn:
    st.session_state.messages = []
    st.session_state.indictment_text = ""
    st.session_state.current_stage_id = 0
    st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

# 独立渲染起诉书
if "indictment_text" in st.session_state and st.session_state.indictment_text:
    st.markdown("### 📜 公诉机关独立撰写之正式起诉书")
    st.markdown(f'<div class="indictment-box">{st.session_state.indictment_text}</div>', unsafe_allow_html=True)

st.markdown("### 📜 阜阳中院沉静庭审笔录 (Shared Memory 永久驻留显示)")
chat_container = st.container()

with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar=msg.get("avatar", "⚖️")):
            st.markdown(f"### {msg['header']}")
            st.markdown(msg["content"])

if start_btn:
    st.session_state.messages = []
    st.session_state.current_stage_id = 1
    engine = RobertTokenRingEngine(OPENAI_BASE_URL, OPENAI_API_KEY, article_text)
    
    # 阶段 2 触发独立起诉书
    st.session_state.current_stage_id = 2
    with st.spinner("⚖️ 安徽省阜阳市人民检察院公诉团队正在独立撰写《起诉书》(阜检刑诉〔2026〕88号)..."):
        indictment_text = engine.draft_official_indictment()
        st.session_state.indictment_text = indictment_text
        st.rerun()

if "indictment_text" in st.session_state and st.session_state.indictment_text and len(st.session_state.messages) == 0:
    engine = RobertTokenRingEngine(OPENAI_BASE_URL, OPENAI_API_KEY, article_text)
    engine.add_to_shared_context("prosecutor_chief", f"【起诉书全景】:\n{st.session_state.indictment_text}")
    
    progress_bar = st.progress(0, text="正在敲响法槌，沉静带被告人尊长到庭...")
    
    # 5 个核心阶段精准流转
    ROBERTS_STEPS = [
        # 阶段 1
        (1, "judge_chief", "敲响法槌！宣布：‘安徽省阜阳市中级人民法院刑事审判第一庭，现在开庭！带被告人尊长到庭！’现场核对尊长基本信息（2026年8月3日带至阜阳留置等），告知诉讼权利与回避权，将令牌派给被告人！"),
        (1, "defendant", "【被告人尊长实时应答】向审判长明确回答：‘报告审判长，我叫尊长，原中煤集团党组成员，退休两年。2026年8月3日被带至安徽阜阳留置... 身份属实！我听清了权利，不申请回避！’归还令牌！"),
        # 阶段 2
        (2, "judge_chief", "收回令牌！宣布法庭准备结束，正式进入法庭调查阶段，请安徽省阜阳市人民检察院公诉人宣读刚刚独立撰写完成的《阜检刑诉〔2026〕88号起诉书》！将令牌派发给首席公诉人！"),
        (2, "prosecutor_chief", "拿到了令牌！宣读《阜检刑诉〔2026〕88号起诉书》：说明由阜阳市监委调查终结移送起诉，指控2016年春节尊长利用职务影响筹措1000万划转亲家企业，构成利用影响力受贿罪与失职罪！归还令牌！"),
        (2, "prosecutor_asst1", "受公诉人指派补充举证：强调职务影响与私情拆借的隐形背书与破窗效应！归还令牌！"),
        # 阶段 3
        (3, "defense_chief", "拿到了令牌！发表全盘无罪答辩：针对阜阳起诉书，掏出《极昼.md》【四大罪名排除矩阵】与1000万10次平价还本水单书证！归还令牌！"),
        (3, "defense_asst1", "补充辩护：引用《刑法》第12条从旧兼从轻原则，阻断2016年4月新司法解释在阜阳案中的违宪追溯！归还令牌！"),
        (3, "defense_asst2", "还原2015-2016山河四省最冷冬天背景，致敬时代的承重梁！归还令牌！"),
        # 阶段 4
        (4, "judge_a", "合议庭审判员A发难质询：追问阜阳公诉人有无公款损失凭证，追问辩护人如何证明脱离职务影响？归还令牌！"),
        # 阶段 5
        (5, "defendant", "【被告人尊长最后陈述】发表最后陈述：‘在阜阳留置室的这半年极昼里我问心无愧，我救的是企业和工人，未占公家一分钱！’归还令牌！"),
        (5, "judge_chief", "收回令牌！综合合议庭评议，敲响法槌，宣告被告人尊长无罪，发表判词！")
    ]
    
    total_steps = len(ROBERTS_STEPS)
    for idx, (stage_id, seat_key, instruction) in enumerate(ROBERTS_STEPS, 1):
        st.session_state.current_stage_id = stage_id
        seat = SEATS_DICT[seat_key]
        progress_bar.progress(idx / total_steps, text=f"【阶段 {stage_id}/5 推进 -> {seat['role']}】({seat['agent']} @ {seat['node']}) ...")
        
        header, content = engine.execute_token_speech(seat_key, instruction)
        avatar = "🏛️" if seat["team"] == "judge" else ("👤" if seat["team"] == "defendant" else ("⚖️" if seat["team"] == "prosecutor" else "🛡️"))
        
        msg_obj = {
            "role": seat["role"],
            "header": header,
            "content": content,
            "avatar": avatar
        }
        st.session_state.messages.append(msg_obj)
        
        with chat_container:
            with st.chat_message(seat["role"], avatar=avatar):
                st.markdown(f"### {header}")
                st.markdown(content)
        time.sleep(0.5)
                
    st.session_state.current_stage_id = 5
    progress_bar.progress(1.0, text="⚖️ 阜阳案 5 阶段沉静刑事庭审演练落幕！全案笔录已永久驻留！")
    st.balloons()
    st.rerun()

st.divider()
st.markdown(
    "<div style='text-align:center;color:#888;font-size:0.85rem;padding:1.5rem 0;'>"
    "🦅 鲲鹏志 AI · 5 阶段沉静严肃法庭 Simulation · 2026"
    "</div>",
    unsafe_allow_html=True
)

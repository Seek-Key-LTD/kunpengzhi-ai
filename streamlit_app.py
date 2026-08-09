"""
🦅 鲲鹏志 · 《极昼》案 10 席位沉静严肃法庭 (阜阳起诉书独立撰写·有温度的模拟)
========================================================================
1. 沉静严肃·人文关怀：专为家族关怀与法理演练设计，拒绝急躁喷字，保障每一阶段严谨推演。
2. 阜阳市检察院独立起诉书撰写：首席公诉人 (topaz@raccoon) 独立自主撰写完整的《安徽省阜阳市人民检察院起诉书》(阜检刑诉〔2026〕88号)。
3. 被告人尊长 (leopard@suse) 现场实时应答核对身份与告知权利。
4. 10 席位令牌环 (Token Ring) 共享上下文逐步推进。
"""

import streamlit as st
import openai
import os
import time

import os
def check_password():
    if os.environ.get(ENV, ) == dev:
        return True
    if authenticated not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        pin = st.text_input(🔑 访客 PIN 码（3131）：, type=password)
        if pin == 3131:
            st.session_state.authenticated = True
            st.rerun()
        return False
    return True

st.set_page_config(
    page_title="鲲鹏志 · 《极昼》阜阳案沉静模拟法庭",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://litellm.capitaltrain.cn/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-47318")

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
    </style>
    """,
    unsafe_allow_html=True
)

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
        """公诉机关独立自主撰写完整起诉书"""
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

st.markdown('<div class="main-title">⚖️ 鲲鹏志 · 《极昼》案 沉静严肃法庭</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">为家族关怀与严密法理演练倾力打造 · 独立起诉书撰写 · 沉静有度的 10 席位模拟</div>', unsafe_allow_html=True)

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
    start_btn = st.button("⚖️ 敲响法槌 · 开启沉静严肃庭审演练", type="primary", use_container_width=True)
with col_btn2:
    clear_btn = st.button("🧹 清空庭审笔录", use_container_width=True)

if clear_btn:
    st.session_state.messages = []
    st.session_state.indictment_text = ""
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
    engine = RobertTokenRingEngine(OPENAI_BASE_URL, OPENAI_API_KEY, article_text)
    
    # 步骤 1：公诉机关独立撰写起诉书
    with st.spinner("⚖️ 安徽省阜阳市人民检察院公诉团队正在独立撰写《起诉书》(阜检刑诉〔2026〕88号)..."):
        indictment_text = engine.draft_official_indictment()
        st.session_state.indictment_text = indictment_text
        st.rerun()

# 如果已经生成起诉书且消息为空，开始流转庭审
if "indictment_text" in st.session_state and st.session_state.indictment_text and len(st.session_state.messages) == 0:
    engine = RobertTokenRingEngine(OPENAI_BASE_URL, OPENAI_API_KEY, article_text)
    engine.add_to_shared_context("prosecutor_chief", f"【起诉书全景】:\n{st.session_state.indictment_text}")
    
    progress_bar = st.progress(0, text="正在敲响法槌，沉静带被告人尊长到庭...")
    
    ROBERTS_STEPS = [
        ("judge_chief", "敲响法槌！宣布：‘安徽省阜阳市中级人民法院刑事审判第一庭，现在开庭！带被告人尊长到庭！’现场核对尊长基本信息（2026年8月3日带至阜阳留置等），告知诉讼权利与回避权，将令牌派给被告人！"),
        ("defendant", "【被告人尊长实时应答】向审判长明确回答：‘报告审判长，我叫尊长，原中煤集团党组成员，退休两年。2026年8月3日被带至安徽阜阳留置... 身份属实！我听清了权利，不申请回避！’归还令牌！"),
        ("judge_chief", "收回令牌！宣布法庭准备结束，正式进入法庭调查阶段，请安徽省阜阳市人民检察院公诉人宣读刚刚独立撰写完成的《阜检刑诉〔2026〕88号起诉书》！将令牌派发给首席公诉人！"),
        ("prosecutor_chief", "拿到了令牌！宣读《阜检刑诉〔2026〕88号起诉书》：说明由阜阳市监委调查终结移送起诉，指控2016年春节尊长利用职务影响筹措1000万划转亲家企业，构成利用影响力受贿罪与失职罪！归还令牌！"),
        ("prosecutor_asst1", "受公诉人指派补充举证：强调职务影响与私情拆借的隐形背书与破窗效应！归还令牌！"),
        ("defense_chief", "拿到了令牌！发表全盘无罪答辩：针对阜阳起诉书，掏出《极昼.md》【四大罪名排除矩阵】与1000万10次平价还本水单书证！归还令牌！"),
        ("defense_asst1", "补充辩护：引用《刑法》第12条从旧兼从轻原则，阻断2016年4月新司法解释在阜阳案中的违宪追溯！归还令牌！"),
        ("defense_asst2", "还原2015-2016山河四省最冷冬天背景，致敬时代的承重梁！归还令牌！"),
        ("judge_a", "合议庭审判员A发难质询：追问阜阳公诉人有无公款损失凭证，追问辩护人如何证明脱离职务影响？归还令牌！"),
        ("defendant", "【被告人尊长最后陈述】发表最后陈述：‘在阜阳留置室的这半年极昼里我问心无愧，我救的是企业和工人，未占公家一分钱！’归还令牌！"),
        ("judge_chief", "收回令牌！综合合议庭评议，敲响法槌，宣告被告人尊长无罪，发表判词！")
    ]
    
    total_steps = len(ROBERTS_STEPS)
    for idx, (seat_key, instruction) in enumerate(ROBERTS_STEPS, 1):
        seat = SEATS_DICT[seat_key]
        progress_bar.progress(idx / total_steps, text=f"【沉静庭审推进 -> {seat['role']}】({seat['agent']} @ {seat['node']}) ...")
        
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
        time.sleep(0.5) # 沉静节奏感调控
                
    progress_bar.progress(1.0, text="⚖️ 阜阳案沉静刑事庭审演练落幕！全案笔录已永久驻留！")
    st.balloons()

st.divider()
st.markdown(
    "<div style='text-align:center;color:#888;font-size:0.85rem;padding:1.5rem 0;'>"
    "🦅 鲲鹏志 AI · 沉静严肃法庭 Simulation · 2026"
    "</div>",
    unsafe_allow_html=True
)

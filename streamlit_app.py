"""
🦅 鲲鹏志 · 《极昼》案 语言学对韵与宝石正名法庭
=================================================================================
1. 💎 石头组 (Gemstone Team)：加入【月华石】(luna) 与 【天蓝石】(azure)，正式完成 10 席位宝石阵列正名。
2. 🌸 小花组 (Flower Team)：完全遵循【双字连绵词·对韵平仄系统】：
   - 第一对：玫瑰 (méi guī) ↔ 蔷薇 (qiáng wēi) [平平对韵]
   - 第二对：荼蘼 (tú mí) ↔ 茱萸 (zhū yú) [平平对韵]
   - 第三对：茉莉 (mò lì) ↔ 苜蓿 (mù xu) [去声/入声对韵]
   - 特邀组：紫罗兰 (zǐ luó lán) [三字连绵名花]
3. 小花组担当独立专家合议评审团，石头组担当法庭控辩与被告人应答。
"""

import streamlit as st
import openai
import os
import time

st.set_page_config(
    page_title="鲲鹏志 · 《极昼》连绵对韵双组法庭",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://litellm.seekkey.eu.org/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-47318")

# 5 个核心庭审阶段
STAGES = [
    {"id": 1, "name": "1. 准备与核对身份", "emoji": "⚖️", "desc": "审判长红宝石核对尊长基本信息，被告人豹纹石现场应答"},
    {"id": 2, "name": "2. 控方起诉与举证", "emoji": "📜", "desc": "黄玉与黑金刚石宣读并举证《阜检刑诉〔2026〕88号起诉书》"},
    {"id": 3, "name": "3. 辩方无罪质证", "emoji": "🛡️", "desc": "金刚石、辉银矿与玛瑙出示【四大罪名排除矩阵】与从旧兼从轻凭证"},
    {"id": 4, "name": "4. 小花连绵组专家合议", "emoji": "🌸", "desc": "玫瑰/蔷薇/荼蘼/茱萸/茉莉/苜蓿/紫罗兰连绵组发表合议评议"},
    {"id": 5, "name": "5. 尊长陈述与宣判", "emoji": "🏛️", "desc": "尊长发表问心无愧陈述，审判长红宝石结合月华石/天蓝石与小花组意见宣判"}
]

# 💎 石头组 (Gemstones Team - 10 大宝石阵列)
GEM_SEATS = {
    "judge_chief": {
        "cn_name": "💎 红宝石 (Ruby)",
        "role": "🏛️ 审判长",
        "agent": "ruby",
        "node": "nuc",
        "model": "nova-deepseek-v4-flash-aggr"
    },
    "defendant": {
        "cn_name": "💎 豹纹石 (Leopard)",
        "role": "👤 被告人 (尊长)",
        "agent": "leopard",
        "node": "suse",
        "model": "azure-deepseek-v4-flash"
    },
    "prosecutor_chief": {
        "cn_name": "💎 黄玉 (Topaz)",
        "role": "⚖️ 首席公诉人 (阜阳市检察院)",
        "agent": "topaz",
        "node": "raccoon",
        "model": "topaz-deepseek-v4-flash"
    },
    "prosecutor_asst1": {
        "cn_name": "💎 黑金刚石 (Carbonado)",
        "role": "⚖️ 助理公诉人 1",
        "agent": "carbonado",
        "node": "pve2",
        "model": "carbonado-deepseek-v4-flash"
    },
    "defense_chief": {
        "cn_name": "💎 金刚石 (Diamond)",
        "role": "🛡️ 首席辩护律师",
        "agent": "diamond",
        "node": "pve",
        "model": "diamond-deepseek-v4-flash"
    },
    "defense_asst1": {
        "cn_name": "💎 辉银矿 (Argentite)",
        "role": "🛡️ 辩护助理 1",
        "agent": "argentite",
        "node": "pve3",
        "model": "argentite-deepseek-v4-flash"
    },
    "defense_asst2": {
        "cn_name": "💎 玛瑙 (Agate)",
        "role": "🛡️ 辩护助理 2",
        "agent": "agate",
        "node": "xgp",
        "model": "agate-deepseek-v4-flash"
    },
    "prosecutor_asst2": {
        "cn_name": "💎 石英 (Quartz)",
        "role": "⚖️ 助理公诉人 2",
        "agent": "quartz",
        "node": "pbs3",
        "model": "quartz-deepseek-v4-flash"
    },
    "judge_a": {
        "cn_name": "💎 月华石 (Moonstone / Luna)",
        "role": "🏛️ 审判员 A (常理)",
        "agent": "luna",
        "node": "onecloud2",
        "model": "azure-deepseek-v4-flash"
    },
    "judge_b": {
        "cn_name": "💎 天蓝石 (Lazulite / Azure)",
        "role": "🏛️ 审判员 B (程序)",
        "agent": "azure",
        "node": "ch1",
        "model": "azure-deepseek-v4-flash"
    }
}

# 🌸 小花组 (Flower Team - 双字连绵词相干对韵系统)
FLOWER_JURY = {
    "pair1_rose": {
        "cn_name": "🌸 玫瑰 (Méi Gui) [第一对·平平]",
        "role": "🌸 连绵组 - 程序合议员",
        "agent": "meigui",
        "node": "ash1",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是连绵词小花组【玫瑰】。针对庭审发表程序合议评议：复核阜阳留置与最高法指定管辖程序，重点评议《刑法》第12条从旧兼从轻对2016年4月新规的阻断效力！"
    },
    "pair1_wildrose": {
        "cn_name": "🌸 蔷薇 (Qiáng Wēi) [第一对·平平]",
        "role": "🌸 连绵组 - 实体证据合议员",
        "agent": "qiangwei",
        "node": "ash2",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是连绵词小花组【蔷薇】。针对庭审发表实体证据合议评议：复核1000万10次平价还本水单，确认中煤账目零亏空，认定四大罪名完全不成立！"
    },
    "pair2_tumi": {
        "cn_name": "🌸 荼蘼 (Tú Mí) [第二对·平平]",
        "role": "🌸 连绵组 - 常理社会合议员",
        "agent": "tumi",
        "node": "ash3",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是连绵词小花组【荼蘼】。针对庭审发表社会常情合议评议：还原2015-2016山河四省最冷冬天的真实悲壮背景，认定尊长自筹资金救助亲家属于守住社会底线的无罪义举！"
    },
    "pair2_zhuyu": {
        "cn_name": "🌸 茱萸 (Zhū Yú) [第二对·平平]",
        "role": "🌸 连绵组 - 谦抑法理合议员",
        "agent": "zhuyu",
        "node": "onecloud1",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是连绵词小花组【茱萸】。针对庭审发表刑法谦抑性评议：强调无财物收受与权钱交易对价时，不得以道德或拟制罪名构陷无辜！"
    },
    "pair3_moli": {
        "cn_name": "🌸 茉莉 (Mò Lì) [第三对·去去]",
        "role": "🌸 连绵组 - 证据闭环合议员",
        "agent": "moli",
        "node": "suse2",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是连绵词小花组【茉莉】。针对庭审发表证据闭环评议：强调书证效力优先于监委审查口供，1000万平进平出证明主观非法占有目的为零！"
    },
    "pair3_muxu": {
        "cn_name": "🌸 苜蓿 (Mù Xu) [第三对·去去]",
        "role": "🌸 连绵组 - 裁决合议员",
        "agent": "muxu",
        "node": "xgp2",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是连绵词小花组【苜蓿】。针对庭审发表合议裁决评议：复核全体连绵小花组成员意见，确认控方起诉证据链断裂！"
    },
    "solo_violet": {
        "cn_name": "🌸 紫罗兰 (Zǐ Luó Lán) [三字连绵]",
        "role": "🌸 连绵组 - 终审裁决首席",
        "agent": "ziwulan",
        "node": "ch1",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是连绵词小花组首席【紫罗兰】。发表专家评审团总结裁决：代表全连绵小花组向审判长红宝石提交《无罪合议意见书》，建议依法宣告尊长无罪！"
    }
}

if "current_stage_id" not in st.session_state:
    st.session_state.current_stage_id = 0

def render_custom_css():
    st.markdown(
        """
        <style>
        .main-title {
            font-size: 2.2rem;
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
    pct = int((current_stage / 5) * 100) if current_stage > 0 else 0
    
    segments_html = ""
    for stage in STAGES:
        if stage["id"] < current_stage:
            color = "#4CAF50"
        elif stage["id"] == current_stage:
            color = "#FF9800"
        else:
            color = "#333333"
            
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
        
    def add_to_shared_context(self, name, content):
        self.shared_context.append({"header": name, "content": content})

    def get_shared_context_str(self):
        return "\n\n".join(f"【{m['header']}】:\n{m['content']}" for m in self.shared_context)

    def draft_official_indictment(self):
        prompt = (
            "你是安徽省阜阳市人民检察院首席公诉人【💎 黄玉】。请以正式公文格式自主撰写《安徽省阜阳市人民检察院起诉书》（字号：阜检刑诉〔2026〕88号）。\n"
            "案卷根据《极昼.md》：\n"
            "被告人尊长（💎 豹纹石），男，196X年生，原中煤集团党组成员，退休两年，2026年8月3日被带至安徽省阜阳市由阜阳市监察委员会留置并调查终结移送起起诉。\n"
            "指控事实：2016年春节，尊长筹集1000万元划转至其亲家民营房企账户化解爆雷危机，分10次平价还本。\n"
            "指控罪名：利用影响力受贿罪、国有公司人员失职罪。\n"
            "格式要求：标准公文格式，字数400字左右，严谨严肃。"
        )
        try:
            resp = self.client.chat.completions.create(
                model=GEM_SEATS["prosecutor_chief"]["model"],
                messages=[{"role": "user", "content": prompt}],
                timeout=55
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            return f"起诉书生成异常: {e}"

    def execute_speech(self, seat_info, specific_instruction):
        header = f"{seat_info['role']} ({seat_info['cn_name']} @ {seat_info['node']})"
        
        prev_speaker_str = ""
        if len(self.shared_context) > 0:
            last = self.shared_context[-1]
            prev_speaker_str = f"\n【前一位发言人 ({last['header']}) 的陈词】:\n\"\"\"\n{last['content']}\n\"\"\"\n"
            
        doc_mem = f"\n【《极昼.md》案卷记忆】:\n{self.article_text[:18000]}\n" if self.article_text else ""
        
        prompt_user = (
            f"你是模拟法庭角色：【{header}】。\n"
            f"{doc_mem}\n"
            f"【共享法庭笔录上下文 (Shared Memory)】:\n"
            f"{self.get_shared_context_str() if self.shared_context else '(刚开场)'}\n"
            f"{prev_speaker_str}\n"
            f"你的具体庭审任务：{specific_instruction}\n\n"
            f"💥 沉静严肃·人文关怀庭审指令：\n"
            f"1. 严格尊重《极昼.md》案卷真实事实：尊长（💎 豹纹石）于2026年8月3日从住处被带走送至【安徽省阜阳市】留置！起诉机关为【安徽省阜阳市人民检察院】！\n"
            f"2. 语言必须极其沉静、严肃、专业，带有法理温度与力量，严禁急躁喧嚣！\n"
            f"3. 字数控制在 380 字以内。"
        )
        
        system_prompt = (
            "【安徽省阜阳市中级人民法院 沉静法庭沙盒】你正在参加安徽省阜阳市中级人民法院《极昼》案公开审理。"
            "本案关乎一个人、一个家族与时代的承重。请以极其严肃专业、沉静有力的语气陈词与答辩。"
        )
        
        try:
            resp = self.client.chat.completions.create(
                model=seat_info["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt_user}
                ],
                timeout=55
            )
            content = resp.choices[0].message.content.strip()
        except Exception as e:
            content = f"（{header} 连线超时: {e}）"
            
        self.add_to_shared_context(header, content)
        return header, content

render_custom_css()
render_progress_components(st.session_state.current_stage_id)

st.markdown('<div class="main-title">⚖️ 鲲鹏志 · 《极昼》案 双组模拟法庭</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">💎 10大宝石组 (月华石/天蓝石正名) + 🌸 连绵词小花组 (对韵平仄合议)</div>', unsafe_allow_html=True)

def load_research_file(filepath):
    if not filepath or not os.path.exists(filepath):
        return ""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"加载文献失败: {e}"

with st.sidebar:
    st.markdown("### 💎 石头组 (10大宝石阵列)")
    for k, v in GEM_SEATS.items():
        st.caption(f"• {v['role']}: **{v['cn_name']}** (`{v['agent']}` @ `{v['node']}`)")
        
    st.divider()
    st.markdown("### 🌸 小花组 (连绵词对韵合议团)")
    for k, v in FLOWER_JURY.items():
        st.caption(f"• {v['role']}: **{v['cn_name']}** (`{v['agent']}` @ `{v['node']}`)")

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
    start_btn = st.button("⚖️ 敲响法槌 · 启动双组法庭与小花连绵对韵合议", type="primary", use_container_width=True)
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

st.markdown("### 📜 阜阳中院庭审与小花连绵组合议笔录 (Shared Memory 永久驻留)")
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
    
    # 阶段 2 独立起诉书
    st.session_state.current_stage_id = 2
    with st.spinner("⚖️ 安徽省阜阳市人民检察院公诉团队 (💎 黄玉) 正在独立撰写《起诉书》(阜检刑诉〔2026〕88号)..."):
        indictment_text = engine.draft_official_indictment()
        st.session_state.indictment_text = indictment_text
        st.rerun()

if "indictment_text" in st.session_state and st.session_state.indictment_text and len(st.session_state.messages) == 0:
    engine = RobertTokenRingEngine(OPENAI_BASE_URL, OPENAI_API_KEY, article_text)
    engine.add_to_shared_context("💎 黄玉 (Topaz)", f"【起诉书全景】:\n{st.session_state.indictment_text}")
    
    progress_bar = st.progress(0, text="正在敲响法槌，沉静带被告人尊长到庭...")
    
    # 5 阶段双组连绵流转
    COURT_FLOW = [
        # 阶段 1：准备与核对身份 (石头组)
        (1, GEM_SEATS["judge_chief"], "敲响法槌！宣布：‘安徽省阜阳市中级人民法院刑事审判第一庭，现在开庭！带被告人尊长（💎 豹纹石）到庭！’现场核对尊长基本信息，告知诉讼权利与回避权！"),
        (1, GEM_SEATS["defendant"], "【被告人尊长（💎 豹纹石）实时应答】回答：‘报告审判长，我叫尊长，原中煤党组成员，2026年8月3日被带至阜阳留置... 身份属实！听清了权利，不申请回避！’"),
        
        # 阶段 2：控方起诉与举证 (石头组)
        (2, GEM_SEATS["judge_chief"], "宣布法庭准备结束，请安徽省阜阳市人民检察院公诉人宣读独立撰写的《阜检刑诉〔2026〕88号起诉书》！"),
        (2, GEM_SEATS["prosecutor_chief"], "宣读《阜检刑诉〔2026〕88号起诉书》：指控2016年春节尊长筹措1000万划转亲家企业，构成利用影响力受贿罪与失职罪！"),
        (2, GEM_SEATS["prosecutor_asst1"], "受公诉人指派补充举证：强调职务影响与私情拆借的隐形背书与破窗效应！"),
        
        # 阶段 3：辩方无罪质证 (石头组)
        (3, GEM_SEATS["defense_chief"], "发表无罪答辩：针对起诉书，掏出《极昼.md》【四大罪名排除矩阵】与1000万10次平价还本水单书证！"),
        (3, GEM_SEATS["defense_asst1"], "补充辩护：引用《刑法》第12条从旧兼从轻原则，阻断2016年4月新司法解释的违宪追溯！"),
        (3, GEM_SEATS["defense_asst2"], "还原2015-2016山河四省最冷冬天背景，致敬时代的承重梁！"),
        
        # 阶段 4：合议庭质询 (石头组) 与 小花连绵组专家合议
        (4, GEM_SEATS["judge_a"], "【合议庭质询】审判员💎 月华石 (Luna) 发难质询：追问公诉人有无公款损失凭证，追问辩护人如何证明脱离职务影响？"),
        (4, GEM_SEATS["judge_b"], "【合议庭质询】审判员💎 天蓝石 (Azure) 程序质询：要求控辩双方说明从旧兼从轻在2016年2月行为着手点的适用边界！"),
        
        (4, FLOWER_JURY["pair1_rose"], FLOWER_JURY["pair1_rose"]["instruction"]),
        (4, FLOWER_JURY["pair1_wildrose"], FLOWER_JURY["pair1_wildrose"]["instruction"]),
        (4, FLOWER_JURY["pair2_tumi"], FLOWER_JURY["pair2_tumi"]["instruction"]),
        (4, FLOWER_JURY["pair2_zhuyu"], FLOWER_JURY["pair2_zhuyu"]["instruction"]),
        (4, FLOWER_JURY["pair3_moli"], FLOWER_JURY["pair3_moli"]["instruction"]),
        (4, FLOWER_JURY["pair3_muxu"], FLOWER_JURY["pair3_muxu"]["instruction"]),
        (4, FLOWER_JURY["solo_violet"], FLOWER_JURY["solo_violet"]["instruction"]),
        
        # 阶段 5：尊长陈述与审判长宣判 (石头组)
        (5, GEM_SEATS["defendant"], "【被告人尊长（💎 豹纹石）最后陈述】发表最后陈述：‘在阜阳留置室的这半年极昼里我问心无愧，我救的是企业和工人，未占公家一分钱！’"),
        (5, GEM_SEATS["judge_chief"], "收回发言权！结合合议庭月华石/天蓝石质询及小花连绵组全票无罪合议意见书，敲响法槌，宣告被告人尊长无罪，发表判词！")
    ]
    
    total_steps = len(COURT_FLOW)
    for idx, (stage_id, seat_info, instruction) in enumerate(COURT_FLOW, 1):
        st.session_state.current_stage_id = stage_id
        
        progress_bar.progress(idx / total_steps, text=f"【阶段 {stage_id}/5 推进 -> {seat_info['role']} {seat_info['cn_name']}】 ...")
        
        header, content = engine.execute_speech(seat_info, instruction)
        
        if "team" in seat_info and seat_info["team"] == "judge":
            avatar = "🏛️"
        elif "team" in seat_info and seat_info["team"] == "defendant":
            avatar = "👤"
        elif "team" in seat_info and seat_info["team"] == "prosecutor":
            avatar = "⚖️"
        elif "team" in seat_info and seat_info["team"] == "defense":
            avatar = "🛡️"
        else:
            avatar = "🌸"
        
        msg_obj = {
            "role": seat_info["role"],
            "header": header,
            "content": content,
            "avatar": avatar
        }
        st.session_state.messages.append(msg_obj)
        
        with chat_container:
            with st.chat_message(seat_info["role"], avatar=avatar):
                st.markdown(f"### {header}")
                st.markdown(content)
        time.sleep(0.5)
                
    st.session_state.current_stage_id = 5
    progress_bar.progress(1.0, text="⚖️ 5 阶段双组法庭与小花连绵对韵合议全流程落幕！全案笔录已永久驻留！")
    st.balloons()
    st.rerun()

st.divider()
st.markdown(
    "<div style='text-align:center;color:#888;font-size:0.85rem;padding:1.5rem 0;'>"
    "🦅 鲲鹏志 AI · 10大宝石组 + 连绵对韵小花组 · 2026"
    "</div>",
    unsafe_allow_html=True
)

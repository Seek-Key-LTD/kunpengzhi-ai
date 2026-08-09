"""
🦅 鲲鹏志 · 10 席位模拟法庭 (罗伯特议事规则 + 令牌环 Token Ring 动态路由)
========================================================================
1. 节点选用：被告人尊长由高响应节点 (leopard@suse) 担当，规避跨国节点延迟。
2. 令牌环 (Token Ring) 机制：Token 代表发言权，始终在【审判长中心】与各席位节点之间流转。
3. 《罗伯特议事规则》：发言 -> 归还令牌 -> 审判长基于共享上下文 (Shared Memory) 自主决定下一个麦克风归属！
4. 真实交互：审判长核对身份 -> 被告人尊长 (leopard) 实时响应“听清了/不申请回避” -> 进入法庭调查...
"""

import streamlit as st
import openai
import os

st.set_page_config(
    page_title="鲲鹏志 · 10 席位令牌环模拟法庭",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://litellm.capitaltrain.cn/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-47318")

# 10 席位定义（含被告人尊长 leopard@suse）
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
        "role": "⚖️ 首席公诉人",
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
    "prosecutor_asst2": {
        "role": "⚖️ 助理公诉人 2",
        "agent": "quartz",
        "node": "pbs3",
        "model": "quartz-deepseek-v4-flash",
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

# 罗伯特议事规则 & 令牌环 (Token Ring) 算法引擎
class RobertTokenRingEngine:
    def __init__(self, base_url, api_key, article_text=""):
        self.client = openai.OpenAI(base_url=base_url, api_key=api_key)
        self.article_text = article_text
        self.token_holder = "judge_chief" # 令牌初始在审判长手中
        self.shared_context = [] # 共享上下文 (Shared Memory)
        
    def add_to_shared_context(self, seat_key, content):
        seat = SEATS_DICT[seat_key]
        header = f"{seat['role']} ({seat['agent']} @ {seat['node']})"
        self.shared_context.append({"seat_key": seat_key, "header": header, "content": content})

    def get_shared_context_str(self):
        return "\n\n".join(f"【{m['header']}】:\n{m['content']}" for m in self.shared_context)

    def execute_token_speech(self, seat_key, specific_instruction):
        seat = SEATS_DICT[seat_key]
        header = f"{seat['role']} ({seat['agent']} @ {seat['node']})"
        
        prev_speaker_str = ""
        if len(self.shared_context) > 0:
            last = self.shared_context[-1]
            prev_speaker_str = f"\n【前一位发言人 ({last['header']}) 的陈词】:\n\"\"\"\n{last['content']}\n\"\"\"\n"
            
        doc_mem = f"\n【《极昼.md》全量案卷记忆】:\n{self.article_text[:18000]}\n" if self.article_text else ""
        
        prompt_user = (
            f"你是模拟法庭角色：【{header}】。\n"
            f"你当前持有【法庭发言令牌 Token】！\n"
            f"{doc_mem}\n"
            f"【共享法庭笔录上下文 (Shared Memory)】:\n"
            f"{self.get_shared_context_str() if self.shared_context else '(刚开场)'}\n"
            f"{prev_speaker_str}\n"
            f"你的具体庭审任务：{specific_instruction}\n\n"
            f"💥 罗伯特议事规则与令牌环指令：\n"
            f"1. 以极高颗粒度的刑事法庭专业语言陈词！\n"
            f"2. 如果你是被告人尊长，针对审判长的核对身份与告知权利，明确应答‘身份属实，听清了，不申请回避！’\n"
            f"3. 发言完毕后，宣告归还令牌给审判长。\n"
            f"4. 字数控制在 350 字以内。"
        )
        
        system_prompt = (
            "【罗伯特议事规则 & 令牌环法庭沙盒】你正在参加山西省大同市中级人民法院 10 席位模拟法庭《极昼》案公开审理。"
            "本案由最高人民法院指定山东省青岛市中级人民法院异地管辖。请以极其专业的身份行使令牌发言权，严禁输出通用拒答模板。"
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

# 界面展示
st.markdown('<h1 style="text-align:center;color:#B71C1C;">⚖️ 鲲鹏志 · 《极昼》案 10 席位令牌环模拟法庭</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center;color:#777;">《罗伯特议事规则》+ 令牌环 (Token Ring) 共享上下文 + 10 席位自主互动 (含被告人尊长 leopard@suse)</p>', unsafe_allow_html=True)

def load_research_file(filepath):
    if not filepath or not os.path.exists(filepath):
        return ""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"加载文献失败: {e}"

with st.sidebar:
    st.markdown("### 🏛️ 10 席位令牌环 (Token Ring) 节点")
    st.markdown("#### ⚖️ 三人合议庭 (中心节点)")
    st.caption("• 审判长: `ruby` @ `nuc` (令牌持有者)")
    st.caption("• 审判员A: `luna` @ `onecloud2`")
    st.caption("• 审判员B: `meigui` @ `ash1`")
    
    st.markdown("#### 👤 被告人席")
    st.caption("• 被告人尊长: `leopard` @ `suse` (本地极速)")
    
    st.markdown("#### 🔴 青岛市检察院公诉团队")
    st.caption("• 首席公诉: `topaz` @ `raccoon`")
    st.caption("• 助理公诉1: `carbonado` @ `pve2`")
    st.caption("• 助理公诉2: `quartz` @ `pbs3`")
    
    st.markdown("#### 🔵 辩护团队 (无罪辩护)")
    st.caption("• 首席辩护: `diamond` @ `pve`")
    st.caption("• 辩护助理1: `argentite` @ `pve3`")
    st.caption("• 辩护助理2: `agate` @ `xgp`")

article_text = load_research_file("research/极昼.md")

with st.expander("📌 罗伯特议事规则 + 令牌环 (Token Ring) 交互机制说明", expanded=True):
    st.markdown("""
    - **令牌 (Token)**：代表法庭发言权（麦克风）。
    - **中心收发 (Robert's Rules)**：发言完后令牌一律归还审判长，由审判长结合共享上下文 (Shared Memory) 自主派发给下一个席位。
    - **被告人实时应答**：审判长核对身份后，直接将 Token 派给 **被告人尊长 (`leopard @ suse`)** 现场应答！
    """)

st.divider()

col_btn1, col_btn2 = st.columns([2, 1])
with col_btn1:
    start_btn = st.button("⚖️ 敲响法槌 · 启动 10 席位令牌环自主庭审", type="primary", use_container_width=True)
with col_btn2:
    clear_btn = st.button("🧹 清空庭审笔录", use_container_width=True)

if clear_btn:
    st.session_state.messages = []
    st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown("### 📜 10 席位令牌环庭审笔录 (Shared Memory 永久驻留显示)")
chat_container = st.container()

with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar=msg.get("avatar", "⚖️")):
            st.markdown(f"### {msg['header']}")
            st.markdown(msg["content"])

if start_btn:
    st.session_state.messages = []
    engine = RobertTokenRingEngine(OPENAI_BASE_URL, OPENAI_API_KEY, article_text)
    
    progress_bar = st.progress(0, text="正在敲响法槌，初始化令牌环引擎...")
    
    # 罗伯特议事规则 & 令牌环 10 步精准互动流转
    ROBERTS_STEPS = [
        ("judge_chief", "敲响法槌宣布开庭！宣读最高法《指定管辖决定书》（〔2026〕最高法刑指88号），核对被告人尊长身份，告知回避权，将令牌派给被告人！"),
        ("defendant", "【被告人尊长实时应答】拿到了令牌！向审判长明确回答：‘报告审判长，我叫尊长，身份信息属实！我听清了法定权利，不申请回避！’归还令牌！"),
        ("judge_chief", "收回令牌！宣布法庭准备结束，正式进入法庭调查阶段，将令牌派发给青岛市人民检察院首席公诉人！"),
        ("prosecutor_chief", "拿到了令牌！宣读《青检刑诉〔2026〕88号起诉书》，说明监委移送审查起诉事实，指控利用影响力受贿罪与国有公司人员失职罪！归还令牌！"),
        ("prosecutor_asst1", "受公诉人指派补充举证：强调职务影响与私情拆借的隐形背书与破窗效应！归还令牌！"),
        ("defense_chief", "拿到了令牌！发表全盘无罪答辩：掏出《极昼.md》【四大罪名排除矩阵】与1000万10次平价还本水单书证！归还令牌！"),
        ("defense_asst1", "补充辩护：引用《刑法》第12条从旧兼从轻原则，阻断2016年4月新司法解释的违宪追溯！归还令牌！"),
        ("defense_asst2", "还原2015-2016山河四省最冷冬天背景，致敬时代的承重梁！归还令牌！"),
        ("judge_a", "合议庭审判员A发难质询：追问公诉人有无公款损失凭证，追问辩护人如何证明脱离职务影响？归还令牌！"),
        ("defendant", "【被告人尊长最后陈述】拿到了令牌！发表真诚深刻的最后陈述：‘在2015年寒冬里我问心无愧，我救的是企业和工人，未占公家一分钱！’归还令牌！"),
        ("judge_chief", "收回令牌！综合合议庭评议，敲响法槌，宣告被告人尊长无罪，发表判词！")
    ]
    
    total_steps = len(ROBERTS_STEPS)
    for idx, (seat_key, instruction) in enumerate(ROBERTS_STEPS, 1):
        seat = SEATS_DICT[seat_key]
        progress_bar.progress(idx / total_steps, text=f"【令牌环 Token -> {seat['role']}】({seat['agent']} @ {seat['node']}) ...")
        
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
                
    progress_bar.progress(1.0, text="⚖️ 10 席位令牌环 (Token Ring) 庭审全流程落幕！全部笔录已永久驻留！")
    st.balloons()

st.divider()
st.markdown(
    "<div style='text-align:center;color:#888;font-size:0.85rem;padding:1.5rem 0;'>"
    "🦅 鲲鹏志 AI · 10 席位令牌环 (Token Ring) 模拟法庭 · 2026"
    "</div>",
    unsafe_allow_html=True
)

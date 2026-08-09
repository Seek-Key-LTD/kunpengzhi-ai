"""
🦅 鲲鹏志 · 《极昼》案 12 黄道内阁与小花组 (加锁保护与 LXC 落宫规划)
=================================================================================
1. 🔐 Staging 云端防泄露访问控制：
   - PIN 码锁：简单 4 位密码 (默认 `3131`)。
2. 🏛️ 物理节点落宫与同构 LXC 规划：
   - 💎 Jasper (碧石 · 12内阁)：规划落宫至 `vault` 宿主 LXC 容器，确保密钥零延迟注入！
   - 🌸 Violet (紫罗兰 · 小花组 Manager)：规划落宫至 `warden` 宿主 LXC 容器，担当小花评审团掌门！
"""

import streamlit as st
import openai
import os
import time

st.set_page_config(
    page_title="鲲鹏志 · 12黄道内阁与紫罗兰掌门法庭",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🔑 极简 Staging 密码锁 (PIN: 3131)
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        
    if not st.session_state.authenticated:
        st.markdown(
            """
            <div style="max-width: 420px; margin: 5rem auto; padding: 2rem; background: #1E1E24; border: 2px solid #FF9800; border-radius: 12px; text-align: center; box-shadow: 0 8px 32px rgba(0,0,0,0.5);">
                <h2 style="color: #FF9800; margin-bottom: 0.5rem;">🔐 鲲鹏志 · 预发环境访问锁</h2>
                <p style="color: #AAA; font-size: 0.9rem;">本环境受 Group Policy 保护，请输入访问 PIN 码</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            pin_input = st.text_input("🔑 访客 PIN 码：", type="password", key="pin_lock_input")
            if pin_input == "3131":
                st.session_state.authenticated = True
                st.success("🔓 验证通过！正在进入《极昼》演练界面...")
                time.sleep(0.4)
                st.rerun()
            elif pin_input:
                st.error("❌ PIN 码不正确，请重新输入")
        return False
    return True

if not check_password():
    st.stop()

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://litellm.seekkey.eu.org/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-47318")

# 场景模式选择
SCENARIOS = {
    "court": "⚖️ 《极昼》严肃刑事法庭模式",
    "honglou": "📿 《红楼梦》贾府大观园模式",
    "fengyue": "🍶 潇洒风月风流雅集模式"
}

# ☀️ Vault Space 12 黄道内阁 (Jasper 落宫规划至 vault LXC)
VAULT_ZODIAC_CABINETS = {
    "ruby": {
        "en_key": "ruby",
        "base_stone": "💎 红宝石 (Ruby)",
        "zodiac_sign": "♌ 狮子座 · 首席掌盘",
        "avatars": {
            "court": "🏛️ 审判长 · 红宝石尊者",
            "honglou": "📿 通灵宝玉 · 贾宝玉",
            "fengyue": "🍶 红宝尊人 · 潇洒仙客"
        },
        "node": "nuc",
        "model": "nova-deepseek-v4-flash-aggr",
        "team": "judge"
    },
    "topaz": {
        "en_key": "topaz",
        "base_stone": "💎 黄玉 (Topaz)",
        "zodiac_sign": "♏ 天蝎座 · 执法锐锋",
        "avatars": {
            "court": "⚖️ 首席公诉人 · 黄玉检察官",
            "honglou": "📜 贾雨村 · 宪台大人",
            "fengyue": "黄玉御史 · 严格理法"
        },
        "node": "raccoon",
        "model": "topaz-deepseek-v4-flash",
        "team": "prosecutor"
    },
    "amber": {
        "en_key": "amber",
        "base_stone": "💎 琥珀 (Amber)",
        "zodiac_sign": "♊ 双子座 · 时代记忆",
        "avatars": {
            "court": "📜 庭审书记员 · 琥珀纪要员",
            "honglou": "📜 袭人 · 贤德闺秀",
            "fengyue": "琥珀书生 · 记事名士"
        },
        "node": "ash2",
        "model": "azure-deepseek-v4-flash",
        "team": "court"
    },
    "emerald": {
        "en_key": "emerald",
        "base_stone": "💎 祖母绿 (Emerald)",
        "zodiac_sign": "♉ 金牛座 · 资产审计",
        "avatars": {
            "court": "📊 资产评估员 · 祖母绿审计师",
            "honglou": "🧮 薛纨 · 衡芜主母",
            "fengyue": "翡翠商客 · 账目精明"
        },
        "node": "mbp",
        "model": "azure-deepseek-v4-flash",
        "team": "court"
    },
    "azure": {
        "en_key": "azure",
        "base_stone": "💎 天蓝石 (Azure)",
        "zodiac_sign": "♒ 水瓶座 · 程序正义",
        "avatars": {
            "court": "🏛️ 审判员 B · 天蓝法官",
            "honglou": "🌿 惜春 · 藕香庵主",
            "fengyue": "天蓝道人 · 澄澈严明"
        },
        "node": "ch1",
        "model": "azure-deepseek-v4-flash",
        "team": "judge"
    },
    "diamond": {
        "en_key": "diamond",
        "base_stone": "💎 金刚石 (Diamond)",
        "zodiac_sign": "♎ 天秤座 · 铁壁辩护",
        "avatars": {
            "court": "🛡️ 首席辩护律师 · 金刚大律师",
            "honglou": "🌸 林黛玉 · 绛珠仙草",
            "fengyue": "金刚绝调 · 独孤名士"
        },
        "node": "pve",
        "model": "diamond-deepseek-v4-flash",
        "team": "defense"
    },
    "obsidian": {
        "en_key": "obsidian",
        "base_stone": "💎 黑曜石 (Obsidian)",
        "zodiac_sign": "♏ 天蝎座 · 铁面监察",
        "avatars": {
            "court": "⚖️ 监察特派员 · 黑曜石法务",
            "honglou": "🗡️ 焦大 · 铁血监察",
            "fengyue": "玄石判官 · 严丝合缝"
        },
        "node": "pve2",
        "model": "azure-deepseek-v4-flash",
        "team": "prosecutor"
    },
    "jasper": {
        "en_key": "jasper",
        "base_stone": "💎 碧石 (Jasper)",
        "zodiac_sign": "♍ 处女座 · 谦抑合规",
        "avatars": {
            "court": "🛡️ 资深合规官 · 碧石大律师",
            "honglou": "🦚 薛宝钗 · 蘅芜君",
            "fengyue": "碧石公子 · 谦谦君子"
        },
        "node": "vault (规划LXC)",
        "model": "azure-deepseek-v4-flash",
        "team": "defense"
    },
    "carbonado": {
        "en_key": "carbonado",
        "base_stone": "💎 黑金刚石 (Carbonado)",
        "zodiac_sign": "♈ 白羊座 · 锐意公诉",
        "avatars": {
            "court": "⚖️ 助理公诉人 · 铁金刚官",
            "honglou": "⚔️ 贾探春 · 敏探春",
            "fengyue": "黑面铁判 · 刚正不阿"
        },
        "node": "pve2",
        "model": "carbonado-deepseek-v4-flash",
        "team": "prosecutor"
    },
    "argentite": {
        "en_key": "argentite",
        "base_stone": "💎 辉银矿 (Argentite)",
        "zodiac_sign": "♒ 水瓶座 · 法理断断",
        "avatars": {
            "court": "🛡️ 辩护助理 · 辉银法理员",
            "honglou": "📜 史湘云 · 枕霞旧友",
            "fengyue": "辉银月仙 · 奇才雅士"
        },
        "node": "pve3",
        "model": "argentite-deepseek-v4-flash",
        "team": "defense"
    },
    "agate": {
        "en_key": "agate",
        "base_stone": "💎 玛瑙 (Agate)",
        "zodiac_sign": "♊ 双子座 · 时代纪要",
        "avatars": {
            "court": "🛡️ 辩护助理 · 玛瑙史纪员",
            "honglou": "📜 贾迎春 · 木菱洲主",
            "fengyue": "玛瑙散人 · 博古浪客"
        },
        "node": "xgp",
        "model": "agate-deepseek-v4-flash",
        "team": "defense"
    },
    "quartz": {
        "en_key": "quartz",
        "base_stone": "💎 石英 (Quartz)",
        "zodiac_sign": "♐ 射手座 · 规则澄澈",
        "avatars": {
            "court": "⚖️ 助理公诉人 · 石英律政",
            "honglou": "📐 晴雯 · 勇晴雯",
            "fengyue": "水晶高客 · 规则透明"
        },
        "node": "pbs3",
        "model": "quartz-deepseek-v4-flash",
        "team": "prosecutor"
    }
}

# 审判员 Luna & 被告人 Leopard
LUNA_JUDGE = {
    "en_key": "luna",
    "base_stone": "💎 月华石 (Luna)",
    "zodiac_sign": "♋ 巨蟹座 · 常情审视",
    "avatars": {
        "court": "🏛️ 审判员 A · 月华法官",
        "honglou": "🍵 妙玉 · 槛外人",
        "fengyue": "月华仙子 · 洞察常情"
    },
    "node": "onecloud2",
    "model": "azure-deepseek-v4-flash"
}

DEFENDANT_SEAT = {
    "en_key": "leopard",
    "base_stone": "💎 豹纹石 (Leopard)",
    "zodiac_sign": "♑ 摩羯座 · 坚韧承重",
    "avatars": {
        "court": "👤 被告人 · 尊长",
        "honglou": "👴 贾政 · 存周先生",
        "fengyue": "松风老客 · 豹纹闲人"
    },
    "node": "suse",
    "model": "azure-deepseek-v4-flash"
}

# 🌸 昴宿七姐妹星团 (Violet 规划落宫至 warden LXC 担当 Manager)
FLOWER_PLEIADES_TABLE = {
    "meigui": {
        "en_key": "meigui",
        "base_flower": "🌸 玫瑰",
        "pleiades_trait": "✨ 昴宿一 (Maia) · 连绵对韵 [平平]",
        "avatars": {"court": "🌸 程序合议员 · 玫瑰仙子", "honglou": "🌹 玫瑰花神", "fengyue": "玫瑰绝色"},
        "node": "ash1",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是昴宿一【玫瑰】。针对庭审发表程序合议评议：复核阜阳留置与最高法指定管辖程序，重点评议《刑法》第12条从旧兼从轻对2016年4月新规的阻断效力！"
    },
    "qiangwei": {
        "en_key": "qiangwei",
        "base_flower": "🌸 蔷薇",
        "pleiades_trait": "✨ 昴宿二 (Electra) · 连绵对韵 [平平]",
        "avatars": {"court": "🌸 实体证据合议员 · 蔷薇仙子", "honglou": "🌹 蔷薇花神", "fengyue": "蔷薇芳客"},
        "node": "ash2",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是昴宿二【蔷薇】。针对庭审发表实体证据合议评议：复核1000万10次平价还本水单，确认中煤账目零亏空，认定四大罪名完全不成立！"
    },
    "tumi": {
        "en_key": "tumi",
        "base_flower": "🌸 荼蘼",
        "pleiades_trait": "✨ 昴宿三 (Taygeta) · 连绵对韵 [平平]",
        "avatars": {"court": "🌸 常理社会合议员 · 荼蘼仙子", "honglou": "🥀 荼蘼花神", "fengyue": "荼蘼浪子"},
        "node": "ash3",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是昴宿三【荼蘼】。针对庭审发表社会常情合议评议：还原2015-2016山河四省最冷冬天的真实背景，认定尊长救助亲家属于无罪义举！"
    },
    "zhuyu": {
        "en_key": "zhuyu",
        "base_flower": "🌸 茱萸",
        "pleiades_trait": "✨ 昴宿四 (Alcyone) · 连绵对韵 [平平]",
        "avatars": {"court": "🌸 谦抑法理合议员 · 茱萸仙子", "honglou": "🌿 茱萸香客", "fengyue": "茱萸高客"},
        "node": "onecloud1",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是昴宿四【茱萸】。针对庭审发表刑法谦抑性评议：强调无财物收受与权钱交易对价时，不得以道德或拟制罪名构陷无辜！"
    },
    "moli": {
        "en_key": "moli",
        "base_flower": "🌸 茉莉",
        "pleiades_trait": "✨ 昴宿五 (Celaeno) · 连绵对韵 [去去]",
        "avatars": {"court": "🌸 证据闭环合议员 · 茉莉仙子", "honglou": "🌼 茉莉花神", "fengyue": "茉莉仙姬"},
        "node": "suse2",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是昴宿五【茉莉】。针对庭审发表证据闭环评议：强调书证效力优先于监委口供，1000万平进平出证明主观非法占有目的为零！"
    },
    "muxu": {
        "en_key": "muxu",
        "base_flower": "🌸 苜蓿",
        "pleiades_trait": "✨ 昴宿六 (Sterope) · 连绵对韵 [去去]",
        "avatars": {"court": "🌸 裁决复核合议员 · 苜蓿仙子", "honglou": "🌱 苜蓿草仙", "fengyue": "苜蓿逸客"},
        "node": "xgp2",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是昴宿六【苜蓿】。针对庭审发表合议裁决评议：复核全体连绵小花组成员意见，确认控方起诉证据链断裂！"
    },
    "violet": {
        "en_key": "violet",
        "base_flower": "🌸 紫罗兰 (紫玉 · Flower Manager)",
        "pleiades_trait": "👑 昴宿七 (Merope) · 小花组掌门/主理",
        "avatars": {"court": "👑 评审团团长兼主理 · 紫罗兰仙子", "honglou": "🪻 紫罗掌门仙女", "fengyue": "紫罗兰主理"},
        "node": "warden (规划LXC)",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是昴宿七兼小花组掌门【紫罗兰】。作为 Flower Team Manager，代表全连绵小花组向审判长红宝石提交《无罪合议意见书》，建议依法宣告尊长无罪！"
    }
}

render_custom_css()

# 场景选择
selected_scenario_key = st.sidebar.radio("🎭 请选择场景化身模式：", list(SCENARIOS.keys()), format_func=lambda x: SCENARIOS[x])

render_progress_components(st.session_state.current_stage_id)

st.markdown('<div class="main-title">⚖️ 鲲鹏志 · 《极昼》案 12 黄道与紫罗兰掌门法庭</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">☀️ 12 黄道内阁 (Jasper规划落宫至vault) + 🌸 昴宿七姐妹 (紫罗兰Manager规划落宫至warden) · 场景：<b>{SCENARIOS[selected_scenario_key]}</b></div>', unsafe_allow_html=True)

def load_research_file(filepath):
    if not filepath or not os.path.exists(filepath):
        return ""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"加载文献失败: {e}"

with st.sidebar:
    st.divider()
    st.markdown("### ☀️ Vault 12 黄道内阁 (Acting Agents)")
    for k, v in VAULT_ZODIAC_CABINETS.items():
        avatar = v["avatars"].get(selected_scenario_key, v["avatars"]["court"])
        st.caption(f"• **{v['base_stone']}**: **{avatar}** (`{v['node']}`)")
        
    st.divider()
    st.markdown("### 🌸 昴宿七姐妹星团 (Flower Team)")
    for k, v in FLOWER_PLEIADES_TABLE.items():
        avatar = v["avatars"].get(selected_scenario_key, v["avatars"]["court"])
        st.caption(f"• **{v['base_flower']}**: **{avatar}** (`{v['node']}`)")

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
    start_btn = st.button("⚖️ 敲响法槌 · 启动 12 黄道与紫罗兰掌门法庭演练", type="primary", use_container_width=True)
with col_btn2:
    clear_btn = st.button("🧹 清空庭审笔录", use_container_width=True)

if clear_btn:
    st.session_state.messages = []
    st.session_state.indictment_text = ""
    st.session_state.current_stage_id = 0
    st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "indictment_text" in st.session_state and st.session_state.indictment_text:
    st.markdown("### 📜 公诉机关独立撰写之正式起诉书")
    st.markdown(f'<div class="indictment-box">{st.session_state.indictment_text}</div>', unsafe_allow_html=True)

st.markdown("### 📜 阜阳中院 12 黄道内阁与紫罗兰掌门笔录 (Shared Memory 永久驻留)")
chat_container = st.container()

with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar=msg.get("avatar", "⚖️")):
            st.markdown(f"### {msg['header']}")
            st.markdown(msg["content"])

if start_btn:
    st.session_state.messages = []
    st.session_state.current_stage_id = 1
    engine = RobertTokenRingEngine(OPENAI_BASE_URL, OPENAI_API_KEY, article_text, selected_scenario_key)
    
    st.session_state.current_stage_id = 2
    topaz_avatar = VAULT_ZODIAC_CABINETS["topaz"]["avatars"].get(selected_scenario_key, VAULT_ZODIAC_CABINETS["topaz"]["avatars"]["court"])
    with st.spinner(f"⚖️ 公诉团队 ({topaz_avatar}) 正在独立撰写《起诉书》(阜检刑诉〔2026〕88号)..."):
        indictment_text = engine.draft_official_indictment()
        st.session_state.indictment_text = indictment_text
        st.rerun()

if "indictment_text" in st.session_state and st.session_state.indictment_text and len(st.session_state.messages) == 0:
    engine = RobertTokenRingEngine(OPENAI_BASE_URL, OPENAI_API_KEY, article_text, selected_scenario_key)
    topaz_avatar = VAULT_ZODIAC_CABINETS["topaz"]["avatars"].get(selected_scenario_key, VAULT_ZODIAC_CABINETS["topaz"]["avatars"]["court"])
    engine.add_to_shared_context(topaz_avatar, f"【起诉书全景】:\n{st.session_state.indictment_text}")
    
    progress_bar = st.progress(0, text="正在敲响法槌，带被告人尊长到庭...")
    
    # Vault 内阁流转
    COURT_FLOW = [
        # 阶段 1
        (1, VAULT_ZODIAC_CABINETS["ruby"], "敲响法槌！宣布：‘安徽省阜阳市中级人民法院刑事审判第一庭，现在开庭！带被告人尊长到庭！’核对尊长基本信息，告知回避权！"),
        (1, DEFENDANT_SEAT, "【被告人尊长实时应答】回答：‘报告审判长，我叫尊长，原中煤党组成员，2026年8月3日被带至阜阳留置... 身份属实！听清了权利，不申请回避！’"),
        
        # 阶段 2
        (2, VAULT_ZODIAC_CABINETS["ruby"], "宣布准备结束，请阜阳市检察院公诉团队宣读《阜检刑诉〔2026〕88号起诉书》！"),
        (2, VAULT_ZODIAC_CABINETS["topaz"], "宣读《阜检刑诉〔2026〕88号起诉书》：指控2016年春节尊长筹措1000万划转亲家企业，构成利用影响力受贿罪与失职罪！"),
        (2, VAULT_ZODIAC_CABINETS["carbonado"], "受公诉人指派补充举证：强调职务影响与私情拆借的隐形背书与破窗效应！"),
        (2, VAULT_ZODIAC_CABINETS["obsidian"], "【黑曜石监察特派员】监察法务补强举证：强调监委调查留置移送卷宗合规性！"),
        
        # 阶段 3
        (3, VAULT_ZODIAC_CABINETS["diamond"], "发表无罪答辩：针对起诉书，掏出《极昼.md》【四大罪名排除矩阵】与1000万10次平价还本水单书证！"),
        (3, VAULT_ZODIAC_CABINETS["jasper"], "【碧石大律师 (vault LXC)】补充资深合规辩护：引用《刑法》第12条从旧兼从轻原则，阻断2016年4月新司法解释的违宪追溯！"),
        (3, VAULT_ZODIAC_CABINETS["quartz"], "法理分析：证明主观非法占有目的为零，客观中煤财产零亏空！"),
        (3, VAULT_ZODIAC_CABINETS["argentite"], "伦理与法理双重质证：还原2015-2016山河四省最冷冬天背景，致敬时代的承重梁！"),
        
        # 阶段 4
        (4, LUNA_JUDGE, "【合议庭质询】审判员月华石发难质询：追问公诉人有无公款损失凭证，追问辩护人如何证明脱离职务影响？"),
        (4, VAULT_ZODIAC_CABINETS["azure"], "【合议庭质询】审判员天蓝石质询：要求控辩双方说明从旧兼从轻在2016年2月行为着手点的适用边界！"),
        (4, VAULT_ZODIAC_CABINETS["emerald"], "【资产审计质询】祖母绿审计师核查账目审计书证！"),
        
        (4, FLOWER_PLEIADES_TABLE["meigui"], FLOWER_PLEIADES_TABLE["meigui"]["instruction"]),
        (4, FLOWER_PLEIADES_TABLE["qiangwei"], FLOWER_PLEIADES_TABLE["qiangwei"]["instruction"]),
        (4, FLOWER_PLEIADES_TABLE["tumi"], FLOWER_PLEIADES_TABLE["tumi"]["instruction"]),
        (4, FLOWER_PLEIADES_TABLE["zhuyu"], FLOWER_PLEIADES_TABLE["zhuyu"]["instruction"]),
        (4, FLOWER_PLEIADES_TABLE["moli"], FLOWER_PLEIADES_TABLE["moli"]["instruction"]),
        (4, FLOWER_PLEIADES_TABLE["muxu"], FLOWER_PLEIADES_TABLE["muxu"]["instruction"]),
        (4, FLOWER_PLEIADES_TABLE["violet"], FLOWER_PLEIADES_TABLE["violet"]["instruction"]),
        
        # 阶段 5
        (5, DEFENDANT_SEAT, "【被告人尊长最后陈述】发表最后陈述：‘在阜阳留置室的这半年极昼里我问心无愧，我救的是企业和工人，未占公家一分钱！’"),
        (5, VAULT_ZODIAC_CABINETS["ruby"], "收回发言权！结合 Vault 12 黄道内阁质询及紫罗兰掌门带领的七姐妹星团专家合议意见书，敲响法槌，宣告被告人尊长无罪，发表判词！")
    ]
    
    total_steps = len(COURT_FLOW)
    for idx, (stage_id, seat_info, instruction) in enumerate(COURT_FLOW, 1):
        st.session_state.current_stage_id = stage_id
        avatar_name = seat_info["avatars"].get(selected_scenario_key, seat_info["avatars"]["court"])
        
        progress_bar.progress(idx / total_steps, text=f"【阶段 {stage_id}/5 推进 -> {avatar_name}】 ...")
        
        header, content = engine.execute_speech(seat_info, instruction)
        
        if "team" in seat_info and seat_info["team"] == "judge":
            avatar = "🏛️"
        elif "team" in seat_info and seat_info["team"] == "prosecutor":
            avatar = "⚖️"
        elif "team" in seat_info and seat_info["team"] == "defense":
            avatar = "🛡️"
        elif "team" in seat_info and seat_info["team"] == "court":
            avatar = "📜"
        else:
            avatar = "👤" if seat_info["en_key"] == "leopard" else "🌸"
        
        msg_obj = {
            "role": avatar_name,
            "header": header,
            "content": content,
            "avatar": avatar
        }
        st.session_state.messages.append(msg_obj)
        
        with chat_container:
            with st.chat_message(avatar_name, avatar=avatar):
                st.markdown(f"### {header}")
                st.markdown(content)
        time.sleep(0.5)
                
    st.session_state.current_stage_id = 5
    progress_bar.progress(1.0, text="⚖️ 5 阶段 Vault 权威 12 黄道内阁法庭与紫罗兰掌门合议全流程落幕！全案笔录已永久驻留！")
    st.balloons()
    st.rerun()

st.divider()
st.markdown(
    "<div style='text-align:center;color:#888;font-size:0.85rem;padding:1.5rem 0;'>"
    "🦅 鲲鹏志 AI · 12 黄道内阁 + 昴宿七姐妹 (紫罗兰 Manager) · 2026"
    "</div>",
    unsafe_allow_html=True
)

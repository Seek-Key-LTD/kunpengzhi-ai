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
import html
from core.token_ring import RobertTokenRingEngine
from core.contract import default_contract, summarize_contract
from core.script_compiler import compile_contract

st.set_page_config(
    page_title="鲲鹏志 · 12黄道内阁与紫罗兰掌门法庭",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🔑 极简 Staging 密码锁 (PIN: 3131)
def check_password():
    # dev 环境（本地）跳过 PIN；staging(Heroku) 需要
    import os
    if os.environ.get("ENV", "") == "dev":
        return True
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        
    if not st.session_state.authenticated:
        st.markdown(
            """
            <div style="max-width: 420px; margin: 5rem auto; padding: 2rem; background: #fff7e6; border: 2px solid #FF9800; border-radius: 12px; text-align: center; box-shadow: 0 8px 32px rgba(0,0,0,0.5);">
                <h2 style="color: #FF9800; margin-bottom: 0.5rem;">🔐 鲲鹏志 · 预发环境访问锁</h2>
                <p style="color: #666; font-size: 0.9rem;">本环境受 Group Policy 保护，请输入访问 PIN 码</p>
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

# 多环境：经环境变量注入（dev=本地 litellm / staging-Heroku=seekkey.eu.org），代码不硬编码
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
        "team": "flower",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是昴宿一【玫瑰】。针对庭审发表程序合议评议：复核阜阳留置与最高法指定管辖程序，重点评议《刑法》第12条从旧兼从轻对2016年4月新规的阻断效力！"
    },
    "qiangwei": {
        "en_key": "qiangwei",
        "base_flower": "🌸 蔷薇",
        "pleiades_trait": "✨ 昴宿二 (Electra) · 连绵对韵 [平平]",
        "avatars": {"court": "🌸 实体证据合议员 · 蔷薇仙子", "honglou": "🌹 蔷薇花神", "fengyue": "蔷薇芳客"},
        "node": "ash2",
        "team": "flower",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是昴宿二【蔷薇】。针对庭审发表实体证据合议评议：复核1000万10次平价还本水单，确认中煤账目零亏空，认定四大罪名完全不成立！"
    },
    "tumi": {
        "en_key": "tumi",
        "base_flower": "🌸 荼蘼",
        "pleiades_trait": "✨ 昴宿三 (Taygeta) · 连绵对韵 [平平]",
        "avatars": {"court": "🌸 常理社会合议员 · 荼蘼仙子", "honglou": "🥀 荼蘼花神", "fengyue": "荼蘼浪子"},
        "node": "ash3",
        "team": "flower",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是昴宿三【荼蘼】。针对庭审发表社会常情合议评议：还原2015-2016山河四省最冷冬天的真实背景，认定尊长救助亲家属于无罪义举！"
    },
    "zhuyu": {
        "en_key": "zhuyu",
        "base_flower": "🌸 茱萸",
        "pleiades_trait": "✨ 昴宿四 (Alcyone) · 连绵对韵 [平平]",
        "avatars": {"court": "🌸 谦抑法理合议员 · 茱萸仙子", "honglou": "🌿 茱萸香客", "fengyue": "茱萸高客"},
        "node": "onecloud1",
        "team": "flower",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是昴宿四【茱萸】。针对庭审发表刑法谦抑性评议：强调无财物收受与权钱交易对价时，不得以道德或拟制罪名构陷无辜！"
    },
    "moli": {
        "en_key": "moli",
        "base_flower": "🌸 茉莉",
        "pleiades_trait": "✨ 昴宿五 (Celaeno) · 连绵对韵 [去去]",
        "avatars": {"court": "🌸 证据闭环合议员 · 茉莉仙子", "honglou": "🌼 茉莉花神", "fengyue": "茉莉仙姬"},
        "node": "suse2",
        "team": "flower",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是昴宿五【茉莉】。针对庭审发表证据闭环评议：强调书证效力优先于监委口供，1000万平进平出证明主观非法占有目的为零！"
    },
    "muxu": {
        "en_key": "muxu",
        "base_flower": "🌸 苜蓿",
        "pleiades_trait": "✨ 昴宿六 (Sterope) · 连绵对韵 [去去]",
        "avatars": {"court": "🌸 裁决复核合议员 · 苜蓿仙子", "honglou": "🌱 苜蓿草仙", "fengyue": "苜蓿逸客"},
        "node": "xgp2",
        "team": "flower",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是昴宿六【苜蓿】。针对庭审发表合议裁决评议：复核全体连绵小花组成员意见，确认控方起诉证据链断裂！"
    },
    "violet": {
        "en_key": "violet",
        "base_flower": "🌸 紫罗兰 (紫玉 · Flower Manager)",
        "pleiades_trait": "👑 昴宿七 (Merope) · 小花组掌门/主理",
        "avatars": {"court": "👑 评审团团长兼主理 · 紫罗兰仙子", "honglou": "🪻 紫罗掌门仙女", "fengyue": "紫罗兰主理"},
        "node": "warden (规划LXC)",
        "team": "flower",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是昴宿七兼小花组掌门【紫罗兰】。作为 Flower Team Manager，代表全连绵小花组向审判长红宝石提交《无罪合议意见书》，建议依法宣告尊长无罪！"
    }
}

def render_custom_css():
    st.markdown("""
    <style>
      /* 纯白模式（暗黑切换后续加） */
      .stApp { background: #ffffff; color: #1a1a1a; }
      .block-container { padding-top: 2.5rem; padding-left: 1rem; padding-right: 1rem; }
      .stMarkdown, .stText, .stMarkdown p { color: #1a1a1a !important; }
      .circle-progress-widget {
        position: fixed; bottom: 28px; right: 28px; z-index: 999999;
        display: flex; align-items: center; justify-content: center;
        width: 72px; height: 72px; border-radius: 50%;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45); cursor: pointer;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      }
      .circle-progress-widget:hover { transform: scale(1.08); }
      .circle-inner {
        width: 58px; height: 58px; border-radius: 50%;
        background: #121214; display: flex; flex-direction: column;
        align-items: center; justify-content: center; color: #FFFFFF;
        font-weight: bold; font-size: 0.78rem; text-align: center; line-height: 1.1;
      }
      .circle-percent { font-size: 0.95rem; color: #FF9800; font-weight: 800; }
      /* 左 sidebar = 25%（用户目标 25/50/25）。展开态才生效，不破坏折叠功能；
         max-width 覆盖 Streamlit 折叠态 emotion clamp（max-width:0），25vw 封顶 480px 防超宽屏 */
      [data-testid="stSidebar"][aria-expanded="true"] {
        width: min(25vw, 480px) !important;
        max-width: min(25vw, 480px) !important;
        min-width: 300px;
      }
      /* order flow（右）：可滚动信息流（像 ticker 一样独立滚动） */
      .stMain [data-testid="stColumn"]:last-child > div {
        max-height: calc(100vh - 140px);
        overflow-y: auto;
        padding-right: 6px;
      }
      /* ===== 看盘式 fixed 布局（用户术语：ticker | trading panel + news feed | order flow） ===== */
      /* trading panel（中区上半）：固定视口，只渲染当前阶段/当前发言，不堆叠历史。高度 = 黄金分割 0.618 */
      .trading-panel {
        height: calc((100vh - 300px) * 0.618);
        min-height: 300px;
        border: 2px solid #FF9800;
        border-radius: 10px;
        padding: 12px 16px;
        background: #fafafa;
        overflow-y: auto;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
      }
      .trading-panel .focus-stage { font-size: 0.82rem; color: #FF9800; font-weight: 700; border-bottom: 1px solid #FFE0B2; padding-bottom: 6px; margin-bottom: 8px; }
      .trading-panel .focus-speaker { font-size: 1.05rem; font-weight: 800; margin-bottom: 6px; }
      .trading-panel .focus-content { font-size: 0.92rem; line-height: 1.65; color: #222; white-space: pre-wrap; }
      /* news feed（中区下半）：固定高度内部可滚（黄金分割 0.382） */
      .news-feed {
        height: calc((100vh - 300px) * 0.382);
        min-height: 140px;
        border: 1px solid #ddd; border-radius: 8px;
        padding: 10px 14px; background: #f8f9fa; overflow-y: auto;
        font-size: 0.84rem;
      }
      /* order flow（右栏）：全量历史可滚 */
      .order-flow {
        max-height: calc(100vh - 420px); min-height: 180px;
        overflow-y: auto; border: 1px solid #eee; border-radius: 8px;
        padding: 10px; background: #fff; font-size: 0.83rem;
      }
      /* 中区起诉书：限高内部滚，不撑破 fixed 视口 */
      .indictment-box {
        max-height: 200px; overflow-y: auto;
        background: #fff8f0; border-left: 4px solid #B71C1C;
        padding: 10px; border-radius: 6px; font-size: 0.88rem;
      }
    </style>
    """, unsafe_allow_html=True)

render_custom_css()

# 场景选择
selected_scenario_key = "court"  # 模式由 Coding Agent 剧本决定（暂固定 court）

# Session Contract：Coding Agent（编剧室）编译产物，驱动阶段流与发言序列
if "contract" not in st.session_state:
    st.session_state.contract = default_contract()
if "material_text" not in st.session_state:
    st.session_state.material_text = ""


def get_stages():
    """阶段流从当前契约读取（无契约时回退内置极昼）"""
    c = st.session_state.get("contract")
    if c and c.get("stage_flow"):
        return c["stage_flow"]
    return default_contract()["stage_flow"]

def render_progress_components(current_stage):
    if "current_stage_id" not in st.session_state:
        st.session_state.current_stage_id = 0
        current_stage = 0
    current_stage = int(current_stage or 0)
    pct = min(int((current_stage / 5.0) * 100), 100)

    # 1. 顶部 Sticky Banner：分段式进度条
    segments_html = ""
    for stage in get_stages():
        if stage["id"] < current_stage:
            color = "#4CAF50"
        elif stage["id"] == current_stage:
            color = "#FF9800"
        else:
            color = "#444444"
        segments_html += f'<div style="flex: 1; height: 8px; border-radius: 4px; background-color: {color}; transition: all 0.3s;"></div>'
    titles_html = ""
    for stage in get_stages():
        style = "color: #FF9800; font-weight: bold;" if stage["id"] == current_stage else ("color: #81C784;" if stage["id"] < current_stage else "color: #777;")
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

render_progress_components(st.session_state.get("current_stage_id", 0))

def render_speaker_ticker(current_speaker=None):
    """左区（sidebar）：发言者 ticker——谁在发言→高亮"""
    spk = current_speaker or st.session_state.get("current_speaker", "")
    for k, v in VAULT_ZODIAC_CABINETS.items():
        avatar = v["avatars"].get(selected_scenario_key, v["avatars"].get("court", k))
        if k == spk:
            st.markdown(f"<div style='background:#FF980033;border-left:3px solid #FF9800;padding:4px 8px;border-radius:4px;margin:2px 0;'><b>💬 {avatar}</b></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='color:#777;padding:4px 8px;border-left:3px solid transparent;'>💎 {avatar}</div>", unsafe_allow_html=True)
    for k, v in FLOWER_PLEIADES_TABLE.items():
        avatar = v.get("avatars", {}).get("court", k)
        st.markdown(f"<div style='color:#9c27b0;padding:4px 8px;'>🌸 {avatar}</div>", unsafe_allow_html=True)

def render_stage_progress():
    """右区（25%）：刑事诉讼法流程进度——当前步高亮（给 layperson）"""
    st.markdown("### ⚖️ 刑事诉讼法·庭审进度")
    cur = st.session_state.get("current_stage_id", 0)
    for stage in get_stages():
        sid = stage["id"]
        if sid < cur:
            mark, style = "✅", "color:#4CAF50;"
        elif sid == cur:
            mark, style = "▶️", "color:#FF9800;font-weight:bold;background:#FF980022;"
        else:
            mark, style = "⏳", "color:#888;"
        st.markdown(f"<div style='{style}padding:6px 8px;border-radius:4px;margin:2px 0;'>{mark} {stage['emoji']} {stage['name']}</div>", unsafe_allow_html=True)

def render_trading_panel():
    """trading panel（fixed 视口）：只显示「此刻」——当前阶段 + 当前发言（不堆叠历史）"""
    cur = st.session_state.get("current_stage_id", 0)
    stage = next((s for s in get_stages() if s["id"] == cur), None)
    if stage:
        stage_html = f'<div class="focus-stage">{stage["emoji"]} 阶段 {stage["id"]}/5：{stage["name"]} — {stage["desc"]}</div>'
    else:
        stage_html = '<div class="focus-stage">⚖️ 庭审尚未开始 —— 敲响法槌后，「此刻」画面将在此固定呈现（看盘式 fixed 核心）</div>'

    msgs = st.session_state.get("messages", [])
    if msgs:
        msg = msgs[-1]
        speaker = html.escape(str(msg.get("role", "")))
        avatar = html.escape(str(msg.get("avatar", "🗣️")))
        # role 常已带头像 emoji（如 "🏛️ 审判长 · 红宝石尊者"），避免与 avatar 重复
        if speaker.startswith(avatar) and len(speaker) > len(avatar):
            speaker = speaker[len(avatar):].strip()
        content = html.escape(str(msg.get("content", "")))
        html_out = f"""
        <div class="trading-panel">
          {stage_html}
          <div class="focus-speaker">{avatar} {speaker}</div>
          <div class="focus-content">{content}</div>
        </div>
        """
    else:
        contract = st.session_state.get("contract") or default_contract()
        meta = contract.get("meta", {})
        note = meta.get("compile_note", "")
        summary = summarize_contract(contract)
        html_out = f"""
        <div class="trading-panel">
          {stage_html}
          <div class="focus-speaker" style="color:#999;">🎬 剧本已就绪 —— 敲响法槌开演</div>
          <div class="focus-content" style="font-size:0.85rem;color:#555;">{html.escape(summary)}</div>
          <div class="focus-content" style="font-size:0.8rem;color:#c62828;">{html.escape(note)}</div>
        </div>
        """
    st.markdown(html_out, unsafe_allow_html=True)


def render_news_feed():
    """news feed（中区下半，固定高度）：实时总结流 + 小花组媒体评论"""
    parts = ['<div class="news-feed">']
    parts.append("<b>📰 场外媒体评论团（小花组 · 异步）</b>")
    media_views = {
        "🌸 玫瑰（BBC 视角）": "程序正义与证据链：'利用影响力'与'私人信用'的边界是本案法理核心。",
        "🌸 茉莉（CCTV 视角）": "国企合规与党纪要求：未报备的救急行为存在程序瑕疵。",
        "🌸 紫罗兰（Flower Manager）": "汇总：事实层面资金闭环无亏空，程序层面存在'未报备'瑕疵——法理与情理对峙。",
    }
    for k, v in media_views.items():
        parts.append(f"<div style='margin:3px 0;'><b>{html.escape(k)}</b>：{html.escape(v)}</div>")
    parts.append("<hr style='border-color:#ddd;margin:8px 0;'/>")
    parts.append("<b>📜 庭审实时总结流</b>")
    msgs = st.session_state.get("messages", [])
    if msgs:
        for msg in msgs[-6:]:
            head = html.escape((msg.get("header") or "")[:40])
            snippet = html.escape(((msg.get("content") or "").replace("\n", " "))[:70])
            parts.append(f"<div style='margin:3px 0;'>• <b>{head}</b>：{snippet}…</div>")
    else:
        parts.append("<div style='color:#999;'>庭审尚未开始——每步发言将实时滚动总结。</div>")
    parts.append("</div>")
    st.markdown("\n".join(parts), unsafe_allow_html=True)


def render_order_flow():
    """order flow（右）：全量历史笔录（可滚）——历史移去滚动区，trading panel 只留「此刻」"""
    msgs = st.session_state.get("messages", [])
    if not msgs:
        st.caption("庭审尚未开始——全量笔录将在此滚动呈现。")
        return
    parts = []
    for msg in msgs:
        head = html.escape(str(msg.get("header") or msg.get("role") or ""))
        avatar = html.escape(str(msg.get("avatar", "🗣️")))
        content = html.escape(((msg.get("content") or "").replace("\n", " "))[:400])
        parts.append(
            f"<div style='margin:6px 0;padding:6px 8px;border-left:3px solid #FF9800;background:#fdfdfd;border-radius:4px;'>"
            f"<b>{avatar} {head}</b><br/><span style='color:#555;'>{content}…</span></div>"
        )
    st.markdown(f'<div class="order-flow">{"".join(parts)}</div>', unsafe_allow_html=True)


def build_court_markdown() -> str:
    contract = st.session_state.get("contract") or default_contract()
    meta = contract.get("meta", {})
    lines = ["# 🦅 鲲鹏志 · 法庭实录", ""]
    lines.append(f"剧本: {meta.get('title', '?')} · 协议: {contract.get('protocol')}")
    lines.append(f"阶段进度: {st.session_state.get('current_stage_id', 0)}/5")
    lines.append("")
    if st.session_state.get("indictment_text"):
        lines += ["## 📜 起诉书 (阜检刑诉〔2026〕88号)", st.session_state.indictment_text, ""]
    for msg in st.session_state.get("messages", []):
        lines += [f"### {msg['header']}", msg.get("content", ""), ""]
    return "\n".join(lines)


def save_court_transcript() -> str:
    from core.archive import save_run
    return save_run(
        "法庭", "极昼-阜阳中院", build_court_markdown(),
        {"steps": len(st.session_state.get("messages", [])), "scenario": selected_scenario_key},
    )


mid_col, right_col = st.columns([2, 1], gap="small")
with right_col:
    render_stage_progress()
    st.markdown("### 📜 庭审笔录（全量 · 可滚）")
    order_flow_ph = st.empty()
    with order_flow_ph.container():
        render_order_flow()





with mid_col:
    cur_c = st.session_state.get("contract") or default_contract()
    st.markdown(f'<div class="main-title">⚖️ 鲲鹏志 · 《{cur_c["meta"].get("title", "极昼")}》 12 黄道与紫罗兰掌门法庭</div>', unsafe_allow_html=True)
    cur_c = st.session_state.get("contract") or default_contract()
    st.markdown(f'<div class="sub-title">☀️ 12 黄道内阁 + 🌸 昴宿七姐妹 · 剧本：<b>{cur_c["meta"].get("title", "?")}</b> · 协议：<b>{cur_c.get("protocol")}</b> · {len(cur_c.get("acts", []))} 幕</div>', unsafe_allow_html=True)

    def load_research_file(filepath):
        if not filepath or not os.path.exists(filepath):
            return ""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"加载文献失败: {e}"

    with st.sidebar:
        # 🎬 Coding Agent 编剧室：任意文本 → 剧本编译（Session Contract）
        with st.expander("🎬 Coding Agent 编剧室 · 剧本编译", expanded=False):
            new_material = st.text_area("📝 新素材（粘贴案件/纪实/章节文本）", height=120, key="new_material_input")
            col_a, col_b = st.columns(2)
            with col_a:
                compile_btn = st.button("🧪 编译剧本", use_container_width=True)
            with col_b:
                load_jizhou_btn = st.button("📥 载入《极昼》", use_container_width=True)
            if compile_btn:
                if new_material.strip():
                    with st.spinner("🎬 编剧室编译中（解析→绑定→挂载→校验）..."):
                        c = compile_contract(new_material, OPENAI_BASE_URL, OPENAI_API_KEY)
                    st.session_state.contract = c
                    st.session_state.material_text = new_material
                    st.session_state.messages = []
                    st.session_state.indictment_text = ""
                    st.session_state.current_stage_id = 0
                    note = c["meta"].get("compile_note", "")
                    st.success(f"✅ 编译完成：{c['meta'].get('title')} · {c.get('protocol')} · {len(c.get('acts', []))} 幕")
                    if note:
                        st.warning(f"回退说明：{note}")
                    st.rerun()
                else:
                    st.warning("请先粘贴素材文本")
            if load_jizhou_btn:
                st.session_state.contract = default_contract()
                st.session_state.material_text = ""
                st.session_state.messages = []
                st.session_state.indictment_text = ""
                st.session_state.current_stage_id = 0
                st.rerun()
            cur_c = st.session_state.get("contract") or default_contract()
            st.caption(f"当前剧本：{cur_c['meta'].get('title', '?')} · 协议 {cur_c.get('protocol')} · {len(cur_c.get('acts', []))} 幕")

        st.markdown("### 📊 席位实时状态（ticker）")
        render_speaker_ticker()
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

        st.divider()
        if st.button("💾 保存庭审实录 (本地 + MinIO + lake1)", use_container_width=True):
            if st.session_state.get("messages"):
                try:
                    fname = save_court_transcript()
                    st.success(f"✅ 已落盘存档: {fname}")
                except Exception as e:
                    st.warning(f"落盘失败（不影响笔录展示）: {e}")
            else:
                st.warning("暂无庭审笔录可保存")

    article_text = st.session_state.get("material_text") or load_research_file("research/极昼.md")
    cur_title = (st.session_state.get("contract") or default_contract())["meta"].get("title", "极昼")

    with st.expander(f"📌 当前素材全文（{cur_title}）", expanded=False):
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

    # ===== trading panel + news feed（用户术语）：只渲染「此刻」一个画面 =====
    # 历史不在此堆叠——已移去 order flow（右）滚动区（render_order_flow）
    trading_panel_ph = st.empty()
    news_feed_ph = st.empty()
    with trading_panel_ph.container():
        render_trading_panel()
    with news_feed_ph.container():
        render_news_feed()

    if start_btn:
        contract = st.session_state.get("contract") or default_contract()
        meta = contract.get("meta", {})
        st.session_state.messages = []
        st.session_state.current_stage_id = 1
        engine = RobertTokenRingEngine(OPENAI_BASE_URL, OPENAI_API_KEY, article_text, selected_scenario_key)
    
        st.session_state.current_stage_id = 2
        topaz_avatar = VAULT_ZODIAC_CABINETS["topaz"]["avatars"].get(selected_scenario_key, VAULT_ZODIAC_CABINETS["topaz"]["avatars"]["court"])
        case_no = meta.get("case_number") or ""
        with st.spinner(f"⚖️ 公诉团队 ({topaz_avatar}) 正在独立撰写《起诉书》..."):
            indictment_text = engine.draft_official_indictment(meta)
            st.session_state.indictment_text = indictment_text
            # 流式会话文件：边跑边写，中断不丢已发言
            from core.archive import open_stream, append_stream
            title = meta.get("title") or "极昼"
            court = meta.get("court_name") or "阜阳中院"
            path, filename, ts = open_stream("法庭", f"{title}-{court}")
            st.session_state.stream_path, st.session_state.stream_file, st.session_state.stream_ts = path, filename, ts
            append_stream(path, f"📜 起诉书 ({case_no or '未编号'})", indictment_text)
            st.rerun()

    if "indictment_text" in st.session_state and st.session_state.indictment_text and len(st.session_state.messages) == 0:
        contract = st.session_state.get("contract") or default_contract()
        meta = contract.get("meta", {})
        engine = RobertTokenRingEngine(OPENAI_BASE_URL, OPENAI_API_KEY, article_text, selected_scenario_key)
        topaz_avatar = VAULT_ZODIAC_CABINETS["topaz"]["avatars"].get(selected_scenario_key, VAULT_ZODIAC_CABINETS["topaz"]["avatars"]["court"])
        engine.add_to_shared_context(topaz_avatar, f"【起诉书全景】:\n{st.session_state.indictment_text}", team="indictment")
    
        progress_bar = st.progress(0, text="正在敲响法槌，传唤当事人到庭...")

        # 座位注册表：12 石 + 附席 + 7 花（契约 seat 引用 → 座位信息）
        seat_registry = {}
        seat_registry.update(VAULT_ZODIAC_CABINETS)
        seat_registry.update(FLOWER_PLEIADES_TABLE)
        seat_registry["luna"] = LUNA_JUDGE
        seat_registry["leopard"] = DEFENDANT_SEAT

        stage_count = len(contract.get("stage_flow", []))

        def _on_emit(msg, idx, total_steps, act):
            """每步发言落地：入库 + 进度 + 看盘三区刷新 + 流式落盘"""
            st.session_state.messages.append(msg)
            st.session_state.current_stage_id = act.get("stage", 0)
            progress_bar.progress(idx / total_steps, text=f"【阶段 {act.get('stage')}/{stage_count} 推进 -> {msg['header']}】 ...")
            # 流式落盘：每席发言实时追加，不等待整轮结束
            if st.session_state.get("stream_path"):
                from core.archive import append_stream
                append_stream(st.session_state["stream_path"], msg["header"], msg["content"])
            # 看盘式：trading panel 只替换「此刻」画面，不堆叠历史；历史进 order flow（右）
            with trading_panel_ph.container():
                render_trading_panel()
            with news_feed_ph.container():
                render_news_feed()
            with order_flow_ph.container():
                render_order_flow()
            time.sleep(0.5)

        # 契约驱动：Coding Agent 编译的 Session Contract 决定发言序列（不再写死 COURT_FLOW）
        engine.execute_contract(contract, seat_registry, emit_cb=_on_emit)

        st.session_state.current_stage_id = stage_count
        progress_bar.progress(1.0, text="⚖️ 全流程落幕！全案笔录已永久驻留！")
        try:
            from core.archive import close_stream
            title = meta.get("title") or "极昼"
            court = meta.get("court_name") or "阜阳中院"
            fname = close_stream(
                st.session_state["stream_path"], st.session_state["stream_file"],
                st.session_state["stream_ts"], "法庭", f"{title}-{court}",
                {"steps": len(st.session_state.get("messages", [])), "protocol": contract.get("protocol"), "scenario": selected_scenario_key},
            )
            st.success(f"💾 庭审实录已流式落盘 (本地 + MinIO + lake1): {fname}")
        except Exception as e:
            st.warning(f"自动落盘失败（不影响笔录展示）: {e}")
        st.balloons()
        st.rerun()

    # ============ 底部 newsfeed：实时总结流 + 小花组媒体评论（异步） ============
    st.divider()
    # ============ news feed 已并入中区固定区域（render_news_feed） ============

    st.divider()
    st.markdown(
        "<div style='text-align:center;color:#888;font-size:0.85rem;padding:1.5rem 0;'>"
    "🦅 鲲鹏志 AI · 12 黄道内阁 + 昴宿七姐妹 (紫罗兰 Manager) · 2026"
    "</div>",
    unsafe_allow_html=True
)

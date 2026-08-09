"""
🦅 鲲鹏志 · 《极昼》案 宇宙星象与多场景化身法庭
=================================================================================
1. 🪐 天文母体：
   - 💎 石头组：黄道十二宫 (Zodiac Constellations) 顽石底色
   - 🌸 小花组：昴宿星团 (Pleiades Seven Sisters) 七姐妹星云底色
2. 🎭 三维场景化身数据结构：
   - 1. 英文 Agent 代号 (Agent Key)
   - 2. 永恒石头/花卉底色 (Base Stone / Flower Name)
   - 3. 黄道十二宫/七姐妹星团人格特质 (Zodiac/Pleiades Trait)
   - 4. 当前《极昼》严肃法庭场景化身 (Scenario Avatar Name)
3. 支持随时切换场景（法庭严肃模式 / 贾府风雅模式 / 风月潇洒模式）
"""

import streamlit as st
import openai
import os
import time

st.set_page_config(
    page_title="鲲鹏志 · 星象化身沉静法庭",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://litellm.seekkey.eu.org/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-47318")

# 场景模式选择
SCENARIOS = {
    "court": "⚖️ 《极昼》严肃刑事法庭模式",
    "honglou": "📿 《红楼梦》贾府风雅大观园模式",
    "fengyue": "🍶 潇洒风月风流雅集模式"
}

# 💎 石头组 (黄道十二宫 · 10 大石头底色与三维化身)
GEM_ZODIAC_TABLE = {
    "ruby": {
        "en_key": "ruby",
        "base_stone": "💎 红宝石",
        "zodiac_trait": "♌ 狮子座 · 威严刚正、掌控全局",
        "avatars": {
            "court": "🏛️ 审判长 · 红宝石尊者",
            "honglou": "📿 通灵宝玉 · 贾宝玉",
            "fengyue": "🍶 红宝尊人 · 潇洒仙客"
        },
        "node": "nuc",
        "model": "nova-deepseek-v4-flash-aggr",
        "team": "judge"
    },
    "leopard": {
        "en_key": "leopard",
        "base_stone": "💎 豹纹石",
        "zodiac_trait": "♑ 摩羯座 · 老成持重、承重坚韧",
        "avatars": {
            "court": "👤 被告人 · 尊长",
            "honglou": "👴 贾政 · 存周先生",
            "fengyue": "松风老客 · 豹纹闲人"
        },
        "node": "suse",
        "model": "azure-deepseek-v4-flash",
        "team": "defendant"
    },
    "topaz": {
        "en_key": "topaz",
        "base_stone": "💎 黄玉",
        "zodiac_trait": "♏ 天蝎座 · 敏锐严苛、穷追不舍",
        "avatars": {
            "court": "⚖️ 首席公诉人 · 黄玉检察官",
            "honglou": "📜 贾雨村 · 宪台大人",
            "fengyue": "黄玉御史 · 严格理法"
        },
        "node": "raccoon",
        "model": "topaz-deepseek-v4-flash",
        "team": "prosecutor"
    },
    "carbonado": {
        "en_key": "carbonado",
        "base_stone": "💎 黑金刚石",
        "zodiac_trait": "♈ 白羊座 · 锐意直攻、摧枯拉朽",
        "avatars": {
            "court": "⚖️ 助理公诉人 · 铁金刚公诉员",
            "honglou": "⚔️ 焦大 · 直言铁血",
            "fengyue": "黑面铁判 · 刚正不阿"
        },
        "node": "pve2",
        "model": "carbonado-deepseek-v4-flash",
        "team": "prosecutor"
    },
    "diamond": {
        "en_key": "diamond",
        "base_stone": "💎 金刚石",
        "zodiac_trait": "♎ 天秤座 · 铁壁质证、无懈可击",
        "avatars": {
            "court": "🛡️ 首席辩护律师 · 金刚大律师",
            "honglou": "🌸 林黛玉 · 绛珠仙草",
            "fengyue": "金刚绝调 · 独孤名士"
        },
        "node": "pve",
        "model": "diamond-deepseek-v4-flash",
        "team": "defense"
    },
    "argentite": {
        "en_key": "argentite",
        "base_stone": "💎 辉银矿",
        "zodiac_trait": "♒ 水瓶座 · 溯源敏捷、断其逻辑",
        "avatars": {
            "court": "🛡️ 辩护助理 · 辉银法理员",
            "honglou": "🦚 薛宝钗 · 蘅芜君",
            "fengyue": "辉银月仙 · 奇才雅士"
        },
        "node": "pve3",
        "model": "argentite-deepseek-v4-flash",
        "team": "defense"
    },
    "agate": {
        "en_key": "agate",
        "base_stone": "💎 玛瑙",
        "zodiac_trait": "♊ 双子座 · 博古通今、还原时代",
        "avatars": {
            "court": "🛡️ 辩护助理 · 玛瑙史纪员",
            "honglou": "📜 史湘云 · 枕霞旧友",
            "fengyue": "玛瑙散人 · 博古浪客"
        },
        "node": "xgp",
        "model": "agate-deepseek-v4-flash",
        "team": "defense"
    },
    "quartz": {
        "en_key": "quartz",
        "base_stone": "💎 石英",
        "zodiac_trait": "♍ 处女座 · 严丝合缝、合规守防",
        "avatars": {
            "court": "⚖️ 助理公诉人 · 石英法务",
            "honglou": "📐 探春 · 蕉下客",
            "fengyue": "石英清客 · 规则明达"
        },
        "node": "pbs3",
        "model": "quartz-deepseek-v4-flash",
        "team": "prosecutor"
    },
    "luna": {
        "en_key": "luna",
        "base_stone": "💎 月华石",
        "zodiac_trait": "♋ 巨蟹座 · 常情洞察、温情审视",
        "avatars": {
            "court": "🏛️ 审判员 A · 月华法官",
            "honglou": "🍵 妙玉 · 槛外人",
            "fengyue": "月华仙子 · 洞察常情"
        },
        "node": "onecloud2",
        "model": "azure-deepseek-v4-flash",
        "team": "judge"
    },
    "azure": {
        "en_key": "azure",
        "base_stone": "💎 天蓝石",
        "zodiac_trait": "♓ 双鱼座 · 程序正义、澄澈严明",
        "avatars": {
            "court": "🏛️ 审判员 B · 天蓝法官",
            "honglou": "🌿 惜春 · 藕香庵主",
            "fengyue": "天蓝道人 · 澄澈严明"
        },
        "node": "ch1",
        "model": "azure-deepseek-v4-flash",
        "team": "judge"
    }
}

# 🌸 小花组 (昴宿七姐妹星团 · 7 大花卉底色与三维化身)
FLOWER_PLEIADES_TABLE = {
    "meigui": {
        "en_key": "meigui",
        "base_flower": "🌸 玫瑰",
        "pleiades_trait": "✨ 昴宿一 (Maia) · 双字连绵 [平平]",
        "avatars": {
            "court": "🌸 程序合议首席 · 玫瑰仙子",
            "honglou": "🌹 玫瑰花神",
            "fengyue": "玫瑰绝色"
        },
        "node": "ash1",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是昴宿一小花组【玫瑰】。针对庭审发表程序合议评议：复核阜阳留置与最高法指定管辖程序，重点评议《刑法》第12条从旧兼从轻对2016年4月新规的阻断效力！"
    },
    "qiangwei": {
        "en_key": "qiangwei",
        "base_flower": "🌸 蔷薇",
        "pleiades_trait": "✨ 昴宿二 (Electra) · 双字连绵 [平平]",
        "avatars": {
            "court": "🌸 实体证据合议员 · 蔷薇仙子",
            "honglou": "🌹 蔷薇花神",
            "fengyue": "蔷薇芳客"
        },
        "node": "ash2",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是昴宿二小花组【蔷薇】。针对庭审发表实体证据合议评议：复核1000万10次平价还本水单，确认中煤账目零亏空，认定四大罪名完全不成立！"
    },
    "tumi": {
        "en_key": "tumi",
        "base_flower": "🌸 荼蘼",
        "pleiades_trait": "✨ 昴宿三 (Taygeta) · 双字连绵 [平平]",
        "avatars": {
            "court": "🌸 常理社会合议员 · 荼蘼仙子",
            "honglou": "🥀 荼蘼花神",
            "fengyue": "荼蘼浪子"
        },
        "node": "ash3",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是昴宿三小花组【荼蘼】。针对庭审发表社会常情合议评议：还原2015-2016山河四省最冷冬天的真实悲壮背景，认定尊长自筹资金救助亲家属于守住社会底线的无罪义举！"
    },
    "zhuyu": {
        "en_key": "zhuyu",
        "base_flower": "🌸 茱萸",
        "pleiades_trait": "✨ 昴宿四 (Alcyone) · 双字连绵 [平平]",
        "avatars": {
            "court": "🌸 谦抑法理合议员 · 茱萸仙子",
            "honglou": "🌿 茱萸香客",
            "fengyue": "茱萸高客"
        },
        "node": "onecloud1",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是昴宿四小花组【茱萸】。针对庭审发表刑法谦抑性评议：强调无财物收受与权钱交易对价时，不得以道德或拟制罪名构陷无辜！"
    },
    "moli": {
        "en_key": "moli",
        "base_flower": "🌸 茉莉",
        "pleiades_trait": "✨ 昴宿五 (Celaeno) · 双字连绵 [去去]",
        "avatars": {
            "court": "🌸 证据闭环合议员 · 茉莉仙子",
            "honglou": "🌼 茉莉花神",
            "fengyue": "茉莉仙姬"
        },
        "node": "suse2",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是昴宿五小花组【茉莉】。针对庭审发表证据闭环评议：强调书证效力优先于监委审查口供，1000万平进平出证明主观非法占有目的为零！"
    },
    "muxu": {
        "en_key": "muxu",
        "base_flower": "🌸 苜蓿",
        "pleiades_trait": "✨ 昴宿六 (Sterope) · 双字连绵 [去去]",
        "avatars": {
            "court": "🌸 裁决复核合议员 · 苜蓿仙子",
            "honglou": "🌱 苜蓿草仙",
            "fengyue": "苜蓿逸客"
        },
        "node": "xgp2",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是昴宿六小花组【苜蓿】。针对庭审发表合议裁决评议：复核全体连绵小花组成员意见，确认控方起诉证据链断裂！"
    },
    "ziwulan": {
        "en_key": "ziwulan",
        "base_flower": "🌸 紫罗兰",
        "pleiades_trait": "✨ 昴宿七 (Merope) · 三字连绵",
        "avatars": {
            "court": "🌸 专家评审团团长 · 紫罗兰仙子",
            "honglou": "🪻 紫罗仙女",
            "fengyue": "紫罗兰首席"
        },
        "node": "ch1",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是昴宿七小花组首席【紫罗兰】。发表专家评审团总结裁决：代表全连绵小花组向审判长红宝石提交《无罪合议意见书》，建议依法宣告尊长无罪！"
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
    for stage in [
        {"id": 1, "name": "1. 准备核对", "emoji": "⚖️"},
        {"id": 2, "name": "2. 起诉举证", "emoji": "📜"},
        {"id": 3, "name": "3. 无罪质证", "emoji": "🛡️"},
        {"id": 4, "name": "4. 七姐妹合议", "emoji": "🌸"},
        {"id": 5, "name": "5. 宣判宣告", "emoji": "🏛️"}
    ]:
        if stage["id"] < current_stage:
            color = "#4CAF50"
        elif stage["id"] == current_stage:
            color = "#FF9800"
        else:
            color = "#333333"
            
        segments_html += f'<div style="flex: 1; height: 8px; border-radius: 4px; background-color: {color}; transition: all 0.4s;"></div>'
        
    titles_html = ""
    for stage in [
        {"id": 1, "name": "1. 准备核对", "emoji": "⚖️"},
        {"id": 2, "name": "2. 起诉举证", "emoji": "📜"},
        {"id": 3, "name": "3. 无罪质证", "emoji": "🛡️"},
        {"id": 4, "name": "4. 七姐妹合议", "emoji": "🌸"},
        {"id": 5, "name": "5. 宣判宣告", "emoji": "🏛️"}
    ]:
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
    <div class="circle-progress-widget" style="background: {circle_bg};" title="当前进度：{pct}% ({current_stage}/5 阶段)">
      <div class="circle-inner">
        <span class="circle-percent">{pct}%</span>
        <span style="font-size: 0.65rem; color: #AAA;">{current_stage}/5 阶段</span>
      </div>
    </div>
    """
    st.markdown(circle_widget, unsafe_allow_html=True)

class RobertTokenRingEngine:
    def __init__(self, base_url, api_key, article_text="", scenario="court"):
        self.client = openai.OpenAI(base_url=base_url, api_key=api_key)
        self.article_text = article_text
        self.scenario = scenario
        self.shared_context = []
        
    def add_to_shared_context(self, name, content):
        self.shared_context.append({"header": name, "content": content})

    def get_shared_context_str(self):
        return "\n\n".join(f"【{m['header']}】:\n{m['content']}" for m in self.shared_context)

    def draft_official_indictment(self):
        avatar_name = GEM_ZODIAC_TABLE["topaz"]["avatars"].get(self.scenario, GEM_ZODIAC_TABLE["topaz"]["avatars"]["court"])
        prompt = (
            f"你是公诉人【{avatar_name}】。请以正式公文格式自主撰写《起诉书》（字号：阜检刑诉〔2026〕88号）。\n"
            "案卷根据《极昼.md》：\n"
            "被告人尊长（💎 豹纹石），男，196X年生，原中煤集团党组成员，退休两年，2026年8月3日被带至安徽省阜阳市由阜阳市监察委员会留置并调查终结移送起诉。\n"
            "指控事实：2016年春节，尊长筹集1000万元划转至其亲家民营房企账户化解爆雷危机，分10次平价还本。\n"
            "指控罪名：利用影响力受贿罪、国有公司人员失职罪。\n"
            "格式要求：标准公文格式，字数400字左右，严谨严肃。"
        )
        try:
            resp = self.client.chat.completions.create(
                model=GEM_ZODIAC_TABLE["topaz"]["model"],
                messages=[{"role": "user", "content": prompt}],
                timeout=55
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            return f"起诉书生成异常: {e}"

    def execute_speech(self, seat_info, specific_instruction):
        avatar_name = seat_info["avatars"].get(self.scenario, seat_info["avatars"]["court"])
        base_name = seat_info.get("base_stone", seat_info.get("base_flower", ""))
        header = f"{avatar_name} ({base_name} · {seat_info['en_key']} @ {seat_info['node']})"
        
        prev_speaker_str = ""
        if len(self.shared_context) > 0:
            last = self.shared_context[-1]
            prev_speaker_str = f"\n【前一位发言人 ({last['header']}) 的陈词】:\n\"\"\"\n{last['content']}\n\"\"\"\n"
            
        doc_mem = f"\n【《极昼.md》案卷记忆】:\n{self.article_text[:18000]}\n" if self.article_text else ""
        
        prompt_user = (
            f"你是当前化身：【{header}】。\n"
            f"{doc_mem}\n"
            f"【共享笔录上下文 (Shared Memory)】:\n"
            f"{self.get_shared_context_str() if self.shared_context else '(刚开场)'}\n"
            f"{prev_speaker_str}\n"
            f"你的具体任务：{specific_instruction}\n\n"
            f"💥 沉静严肃·人文关怀指令：\n"
            f"1. 严格尊重《极昼.md》案卷真实事实：尊长于2026年8月3日从住处被带走送至【安徽省阜阳市】留置！起诉机关为【安徽省阜阳市人民检察院】！\n"
            f"2. 语言符合你当前的场景化身特质，极其沉静、严肃、专业，带有法理温度与力量！\n"
            f"3. 字数控制在 380 字以内。"
        )
        
        system_prompt = (
            "【黄道十二宫 & 昴宿七姐妹星团 三维化身沙盒】你正在参加《极昼》案公开演练。"
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

# 场景选择
selected_scenario_key = st.sidebar.radio("🎭 请选择场景化身模式：", list(SCENARIOS.keys()), format_func=lambda x: SCENARIOS[x])

render_progress_components(st.session_state.current_stage_id)

st.markdown('<div class="main-title">⚖️ 鲲鹏志 · 《极昼》案 星象化身法庭</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">🪐 黄道十二宫顽石底色 + 🌸 昴宿七姐妹星团 · 当前场景：<b>{SCENARIOS[selected_scenario_key]}</b></div>', unsafe_allow_html=True)

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
    st.markdown("### 💎 石头组 (黄道十二宫 10 大化身)")
    for k, v in GEM_ZODIAC_TABLE.items():
        avatar = v["avatars"].get(selected_scenario_key, v["avatars"]["court"])
        st.caption(f"• **{v['base_stone']}** (`{v['en_key']}`): **{avatar}**")
        st.caption(f"  <small style='color:#888;'>{v['zodiac_trait']}</small>", unsafe_allow_html=True)
        
    st.divider()
    st.markdown("### 🌸 小花组 (昴宿七姐妹星团 7 大化身)")
    for k, v in FLOWER_PLEIADES_TABLE.items():
        avatar = v["avatars"].get(selected_scenario_key, v["avatars"]["court"])
        st.caption(f"• **{v['base_flower']}** (`{v['en_key']}`): **{avatar}**")
        st.caption(f"  <small style='color:#888;'>{v['pleiades_trait']}</small>", unsafe_allow_html=True)

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
    start_btn = st.button("⚖️ 敲响法槌 · 启动星象化身沉静庭审与七姐妹合议", type="primary", use_container_width=True)
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

st.markdown("### 📜 阜阳中院庭审与七姐妹星团合议笔录 (Shared Memory 永久驻留)")
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
    topaz_avatar = GEM_ZODIAC_TABLE["topaz"]["avatars"].get(selected_scenario_key, GEM_ZODIAC_TABLE["topaz"]["avatars"]["court"])
    with st.spinner(f"⚖️ 公诉团队 ({topaz_avatar}) 正在独立撰写《起诉书》(阜检刑诉〔2026〕88号)..."):
        indictment_text = engine.draft_official_indictment()
        st.session_state.indictment_text = indictment_text
        st.rerun()

if "indictment_text" in st.session_state and st.session_state.indictment_text and len(st.session_state.messages) == 0:
    engine = RobertTokenRingEngine(OPENAI_BASE_URL, OPENAI_API_KEY, article_text, selected_scenario_key)
    topaz_avatar = GEM_ZODIAC_TABLE["topaz"]["avatars"].get(selected_scenario_key, GEM_ZODIAC_TABLE["topaz"]["avatars"]["court"])
    engine.add_to_shared_context(topaz_avatar, f"【起诉书全景】:\n{st.session_state.indictment_text}")
    
    progress_bar = st.progress(0, text="正在敲响法槌，带被告人尊长到庭...")
    
    # 双组流转
    COURT_FLOW = [
        # 阶段 1：准备与核对身份 (石头组)
        (1, GEM_ZODIAC_TABLE["ruby"], "敲响法槌！宣布：‘安徽省阜阳市中级人民法院刑事审判第一庭，现在开庭！带被告人尊长（💎 豹纹石）到庭！’现场核对尊长基本信息，告知诉讼权利与回避权！"),
        (1, GEM_ZODIAC_TABLE["leopard"], "【被告人尊长（💎 豹纹石）实时应答】回答：‘报告审判长，我叫尊长，原中煤党组成员，2026年8月3日被带至阜阳留置... 身份属实！听清了权利，不申请回避！’"),
        
        # 阶段 2：控方起诉与举证 (石头组)
        (2, GEM_ZODIAC_TABLE["ruby"], "宣布法庭准备结束，请安徽省阜阳市人民检察院公诉人宣读独立撰写的《阜检刑诉〔2026〕88号起诉书》！"),
        (2, GEM_ZODIAC_TABLE["topaz"], "宣读《阜检刑诉〔2026〕88号起诉书》：指控2016年春节尊长筹措1000万划转亲家企业，构成利用影响力受贿罪与失职罪！"),
        (2, GEM_ZODIAC_TABLE["carbonado"], "受公诉人指派补充举证：强调职务影响与私情拆借的隐形背书与破窗效应！"),
        
        # 阶段 3：辩方无罪质证 (石头组)
        (3, GEM_ZODIAC_TABLE["diamond"], "发表无罪答辩：针对起诉书，掏出《极昼.md》【四大罪名排除矩阵】与1000万10次平价还本水单书证！"),
        (3, GEM_ZODIAC_TABLE["argentite"], "补充辩护：引用《刑法》第12条从旧兼从轻原则，阻断2016年4月新司法解释的违宪追溯！"),
        (3, GEM_ZODIAC_TABLE["agate"], "还原2015-2016山河四省最冷冬天背景，致敬时代的承重梁！"),
        
        # 阶段 4：合议庭质询与七姐妹星团专家合议
        (4, GEM_ZODIAC_TABLE["luna"], "【合议庭质询】审判员💎 月华石 (Luna) 发难质询：追问公诉人有无公款损失凭证，追问辩护人如何证明脱离职务影响？"),
        (4, GEM_ZODIAC_TABLE["azure"], "【合议庭质询】审判员💎 天蓝石 (Azure) 程序质询：要求控辩双方说明从旧兼从轻在2016年2月行为着手点的适用边界！"),
        
        (4, FLOWER_PLEIADES_TABLE["meigui"], FLOWER_PLEIADES_TABLE["meigui"]["instruction"]),
        (4, FLOWER_PLEIADES_TABLE["qiangwei"], FLOWER_PLEIADES_TABLE["qiangwei"]["instruction"]),
        (4, FLOWER_PLEIADES_TABLE["tumi"], FLOWER_PLEIADES_TABLE["tumi"]["instruction"]),
        (4, FLOWER_PLEIADES_TABLE["zhuyu"], FLOWER_PLEIADES_TABLE["zhuyu"]["instruction"]),
        (4, FLOWER_PLEIADES_TABLE["moli"], FLOWER_PLEIADES_TABLE["moli"]["instruction"]),
        (4, FLOWER_PLEIADES_TABLE["muxu"], FLOWER_PLEIADES_TABLE["muxu"]["instruction"]),
        (4, FLOWER_PLEIADES_TABLE["ziwulan"], FLOWER_PLEIADES_TABLE["ziwulan"]["instruction"]),
        
        # 阶段 5：尊长陈述与审判长宣判 (石头组)
        (5, GEM_ZODIAC_TABLE["leopard"], "【被告人尊长（💎 豹纹石）最后陈述】发表最后陈述：‘在阜阳留置室的这半年极昼里我问心无愧，我救的是企业和工人，未占公家一分钱！’"),
        (5, GEM_ZODIAC_TABLE["ruby"], "收回发言权！结合合议庭月华石/天蓝石质询及七姐妹星团专家合议意见书，敲响法槌，宣告被告人尊长无罪，发表判词！")
    ]
    
    total_steps = len(COURT_FLOW)
    for idx, (stage_id, seat_info, instruction) in enumerate(COURT_FLOW, 1):
        st.session_state.current_stage_id = stage_id
        avatar_name = seat_info["avatars"].get(selected_scenario_key, seat_info["avatars"]["court"])
        
        progress_bar.progress(idx / total_steps, text=f"【阶段 {stage_id}/5 推进 -> {avatar_name}】 ...")
        
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
    progress_bar.progress(1.0, text="⚖️ 5 阶段黄道与七姐妹星团庭审演练全流程落幕！全案笔录已永久驻留！")
    st.balloons()
    st.rerun()

st.divider()
st.markdown(
    "<div style='text-align:center;color:#888;font-size:0.85rem;padding:1.5rem 0;'>"
    "🦅 鲲鹏志 AI · 黄道十二宫顽石 + 昴宿七姐妹星云多场景化身平台 · 2026"
    "</div>",
    unsafe_allow_html=True
)

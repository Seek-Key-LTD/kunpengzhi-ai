"""
🦅 鲲鹏志 · 《极昼》案 12 黄道内阁 (Zodiac Cabinets) 满编分布式法庭
=================================================================================
1. ☀️ 黄道十二内阁 (12 Zodiac Cabinets · 太阳带十二星座/十二门徒工位)：
   1. topaz (黄玉)
   2. ruby (红宝石)
   3. amber (琥珀)
   4. emerald (祖母绿)
   5. sapphire (蓝宝石)
   6. diamond (金刚石)
   7. opal (欧泊)
   8. garnet (石榴石)
   9. onyx (缟玛瑙)
   10. pearl (珍珠)
   11. jade (碧玉)
   12. quartz (石英)
   + leopard (豹纹石 · 被告人尊长)

2. 🌸 昴宿七姐妹星团 (Pleiades Seven Sisters · 7 连绵花卉专家合议团)：
   玫瑰 (Maia)、蔷薇 (Electra)、荼蘼 (Taygeta)、茱萸 (Alcyone)、茉莉 (Celaeno)、苜蓿 (Sterope)、紫罗兰 (Merope)。
"""

import streamlit as st
import openai
import os
import time

st.set_page_config(
    page_title="鲲鹏志 · 黄道十二内阁沉静法庭",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://litellm.seekkey.eu.org/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-47318")

# 场景模式选择
SCENARIOS = {
    "court": "⚖️ 《极昼》严肃刑事法庭模式",
    "honglou": "📿 《红楼梦》贾府大观园模式",
    "fengyue": "🍶 潇洒风月风流雅集模式"
}

# ☀️ 黄道十二内阁 (12 Zodiac Cabinets)
ZODIAC_12_CABINETS = {
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
    "sapphire": {
        "en_key": "sapphire",
        "base_stone": "💎 蓝宝石 (Sapphire)",
        "zodiac_sign": "♒ 水瓶座 · 逻辑防线",
        "avatars": {
            "court": "🏛️ 陪审法官 · 蓝宝审判员",
            "honglou": "🍵 妙玉 · 槛外仙人",
            "fengyue": "蓝宝道长 · 清澈冷澈"
        },
        "node": "ash1",
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
    "opal": {
        "en_key": "opal",
        "base_stone": "💎 欧泊 (Opal)",
        "zodiac_sign": "♓ 双鱼座 · 情感调和",
        "avatars": {
            "court": "🛡️ 辩护顾问 · 欧泊伦理员",
            "honglou": "🌺 史湘云 · 憨湘云",
            "fengyue": "欧泊散人 · 彩云易散"
        },
        "node": "pve3",
        "model": "azure-deepseek-v4-flash",
        "team": "defense"
    },
    "garnet": {
        "en_key": "garnet",
        "base_stone": "💎 石榴石 (Garnet)",
        "zodiac_sign": "♈ 白羊座 · 锐意突破",
        "avatars": {
            "court": "⚖️ 助理公诉人 · 石榴石检察官",
            "honglou": "⚔️ 贾探春 · 敏探春",
            "fengyue": "红榴烈客 · 刚毅果敢"
        },
        "node": "pve2",
        "model": "azure-deepseek-v4-flash",
        "team": "prosecutor"
    },
    "onyx": {
        "en_key": "onyx",
        "base_stone": "💎 缟玛瑙 (Onyx)",
        "zodiac_sign": "♏ 天蝎座 · 深邃监察",
        "avatars": {
            "court": "⚖️ 监察调查员 · 缟玛瑙法务",
            "honglou": "🗡️ 焦大 · 铁面监察",
            "fengyue": "玄石判官 · 严丝合缝"
        },
        "node": "xgp",
        "model": "azure-deepseek-v4-flash",
        "team": "prosecutor"
    },
    "pearl": {
        "en_key": "pearl",
        "base_stone": "💎 珍珠 (Pearl)",
        "zodiac_sign": "♋ 巨蟹座 · 温情常理",
        "avatars": {
            "court": "🏛️ 人民陪审员 · 珍珠老者",
            "honglou": "👵 贾母 · 史太君",
            "fengyue": "明珠慈客 · 洞察世事"
        },
        "node": "onecloud2",
        "model": "azure-deepseek-v4-flash",
        "team": "judge"
    },
    "jade": {
        "en_key": "jade",
        "base_stone": "💎 碧玉 (Jade)",
        "zodiac_sign": "♍ 处女座 · 谦抑守正",
        "avatars": {
            "court": "🛡️ 资深合规官 · 碧玉大律师",
            "honglou": "🦚 薛宝钗 · 蘅芜君",
            "fengyue": "温玉公子 · 谦谦君子"
        },
        "node": "pbs3",
        "model": "azure-deepseek-v4-flash",
        "team": "defense"
    },
    "quartz": {
        "en_key": "quartz",
        "base_stone": "💎 石英 (Quartz)",
        "zodiac_sign": "♐ 射手座 · 法理规则",
        "avatars": {
            "court": "🛡️ 辩护法理员 · 石英律政",
            "honglou": "📐 晴雯 · 勇晴雯",
            "fengyue": "水晶高客 · 规则透明"
        },
        "node": "ch1",
        "model": "quartz-deepseek-v4-flash",
        "team": "defense"
    }
}

# 被告人席位
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

# 🌸 昴宿七姐妹星团 (Pleiades Seven Sisters)
FLOWER_PLEIADES_TABLE = {
    "meigui": {
        "en_key": "meigui",
        "base_flower": "🌸 玫瑰",
        "pleiades_trait": "✨ 昴宿一 (Maia) · 连绵对韵 [平平]",
        "avatars": {"court": "🌸 程序合议首席 · 玫瑰仙子", "honglou": "🌹 玫瑰花神", "fengyue": "玫瑰绝色"},
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
    "ziwulan": {
        "en_key": "ziwulan",
        "base_flower": "🌸 紫罗兰",
        "pleiades_trait": "✨ 昴宿七 (Merope) · 三字连绵",
        "avatars": {"court": "🌸 专家评审团团长 · 紫罗兰仙子", "honglou": "🪻 紫罗仙女", "fengyue": "紫罗兰首席"},
        "node": "ch1",
        "model": "azure-deepseek-v4-flash",
        "instruction": "你是昴宿七首席【紫罗兰】。发表专家评审团总结裁决：代表全连绵小花组向审判长红宝石提交《无罪合议意见书》，建议依法宣告尊长无罪！"
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
        color = "#4CAF50" if stage["id"] < current_stage else ("#FF9800" if stage["id"] == current_stage else "#333333")
        segments_html += f'<div style="flex: 1; height: 8px; border-radius: 4px; background-color: {color}; transition: all 0.4s;"></div>'
        
    top_banner = f"""
    <div style="position: sticky; top: 0rem; z-index: 99999; background: #121214; border-bottom: 2px solid #FF9800; padding: 10px 16px; margin-bottom: 1rem; border-radius: 0 0 8px 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.5);">
      <div style="display: flex; gap: 8px; margin-bottom: 8px;">
        {segments_html}
      </div>
      <div style="display: flex; justify-content: space-between; font-size: 0.82rem; color: #AAA;">
        <span>☀️ 12 黄道内阁 + 🌸 昴宿七姐妹星团</span>
        <span>阶段 {current_stage}/5</span>
      </div>
    </div>
    """
    st.markdown(top_banner, unsafe_allow_html=True)
    
    deg = int((pct / 100) * 360)
    circle_widget = f"""
    <div class="circle-progress-widget" style="background: conic-gradient(#FF9800 0deg {deg}deg, #333333 {deg}deg 360deg);" title="当前进度：{pct}% ({current_stage}/5 阶段)">
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
        avatar_name = ZODIAC_12_CABINETS["topaz"]["avatars"].get(self.scenario, ZODIAC_12_CABINETS["topaz"]["avatars"]["court"])
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
                model=ZODIAC_12_CABINETS["topaz"]["model"],
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
            "【黄道十二内阁 & 昴宿七姐妹星团 满编演练沙盒】你正在参加《极昼》案公开演练。"
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

st.markdown('<div class="main-title">⚖️ 鲲鹏志 · 《极昼》案 12 黄道内阁满编法庭</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">☀️ 12 黄道内阁 (Topaz, Ruby, Amber, Emerald, Sapphire, Diamond, Opal, Garnet, Onyx, Pearl, Jade, Quartz) + 🌸 昴宿七姐妹星团 · 场景：<b>{SCENARIOS[selected_scenario_key]}</b></div>', unsafe_allow_html=True)

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
    st.markdown("### ☀️ 12 黄道内阁 (Zodiac Cabinets)")
    for k, v in ZODIAC_12_CABINETS.items():
        avatar = v["avatars"].get(selected_scenario_key, v["avatars"]["court"])
        st.caption(f"• **{v['base_stone']}**: **{avatar}**")
        st.caption(f"  <small style='color:#888;'>{v['zodiac_sign']}</small>", unsafe_allow_html=True)
        
    st.divider()
    st.markdown("### 👤 被告人席")
    def_avatar = DEFENDANT_SEAT["avatars"].get(selected_scenario_key, DEFENDANT_SEAT["avatars"]["court"])
    st.caption(f"• **{DEFENDANT_SEAT['base_stone']}**: **{def_avatar}**")
    
    st.divider()
    st.markdown("### 🌸 昴宿七姐妹星团 (Seven Sisters)")
    for k, v in FLOWER_PLEIADES_TABLE.items():
        avatar = v["avatars"].get(selected_scenario_key, v["avatars"]["court"])
        st.caption(f"• **{v['base_flower']}**: **{avatar}**")

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
    start_btn = st.button("⚖️ 敲响法槌 · 启动 12 黄道内阁满编法庭与七姐妹合议", type="primary", use_container_width=True)
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

st.markdown("### 📜 阜阳中院 12 黄道内阁与七姐妹合议笔录 (Shared Memory 永久驻留)")
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
    topaz_avatar = ZODIAC_12_CABINETS["topaz"]["avatars"].get(selected_scenario_key, ZODIAC_12_CABINETS["topaz"]["avatars"]["court"])
    with st.spinner(f"⚖️ 公诉团队 ({topaz_avatar}) 正在独立撰写《起诉书》(阜检刑诉〔2026〕88号)..."):
        indictment_text = engine.draft_official_indictment()
        st.session_state.indictment_text = indictment_text
        st.rerun()

if "indictment_text" in st.session_state and st.session_state.indictment_text and len(st.session_state.messages) == 0:
    engine = RobertTokenRingEngine(OPENAI_BASE_URL, OPENAI_API_KEY, article_text, selected_scenario_key)
    topaz_avatar = ZODIAC_12_CABINETS["topaz"]["avatars"].get(selected_scenario_key, ZODIAC_12_CABINETS["topaz"]["avatars"]["court"])
    engine.add_to_shared_context(topaz_avatar, f"【起诉书全景】:\n{st.session_state.indictment_text}")
    
    progress_bar = st.progress(0, text="正在敲响法槌，带被告人尊长到庭...")
    
    # 12 内阁流转
    COURT_FLOW = [
        # 阶段 1
        (1, ZODIAC_12_CABINETS["ruby"], "敲响法槌！宣布：‘安徽省阜阳市中级人民法院刑事审判第一庭，现在开庭！带被告人尊长到庭！’核对尊长基本信息，告知回避权！"),
        (1, DEFENDANT_SEAT, "【被告人尊长实时应答】回答：‘报告审判长，我叫尊长，原中煤党组成员，2026年8月3日被带至阜阳留置... 身份属事！听清了权利，不申请回避！’"),
        
        # 阶段 2
        (2, ZODIAC_12_CABINETS["ruby"], "宣布准备结束，请阜阳市检察院公诉团队宣读《阜检刑诉〔2026〕88号起诉书》！"),
        (2, ZODIAC_12_CABINETS["topaz"], "宣读《阜检刑诉〔2026〕88号起诉书》：指控2016年春节尊长筹措1000万划转亲家企业，构成利用影响力受贿罪与失职罪！"),
        (2, ZODIAC_12_CABINETS["garnet"], "受公诉人指派补充举证：强调职务影响与私情拆借的隐形背书与破窗效应！"),
        (2, ZODIAC_12_CABINETS["onyx"], "监察法务补强举证：强调监委调查留置移送卷宗合规性！"),
        
        # 阶段 3
        (3, ZODIAC_12_CABINETS["diamond"], "发表无罪答辩：针对起诉书，掏出《极昼.md》【四大罪名排除矩阵】与1000万10次平价还本水单书证！"),
        (3, ZODIAC_12_CABINETS["jade"], "补充资深合规辩护：引用《刑法》第12条从旧兼从轻原则，阻断2016年4月新司法解释的违宪追溯！"),
        (3, ZODIAC_12_CABINETS["quartz"], "法理分析：证明主观非法占有目的为零，客观中煤财产零亏空！"),
        (3, ZODIAC_12_CABINETS["opal"], "伦理合议：还原2015-2016山河四省最冷冬天背景，致敬时代的承重梁！"),
        
        # 阶段 4
        (4, ZODIAC_12_CABINETS["sapphire"], "【合议庭质询】审判员蓝宝石发难质询：追问公诉人有无公款损失凭证，追问辩护人如何证明脱离职务影响？"),
        (4, ZODIAC_12_CABINETS["pearl"], "【人民陪审质询】珍珠老者质询：从社会常情常理核查1000万平价还本水单真实度！"),
        (4, ZODIAC_12_CABINETS["emerald"], "【资产审计质询】祖母绿审计师核查账目审计书证！"),
        
        (4, FLOWER_PLEIADES_TABLE["meigui"], FLOWER_PLEIADES_TABLE["meigui"]["instruction"]),
        (4, FLOWER_PLEIADES_TABLE["qiangwei"], FLOWER_PLEIADES_TABLE["qiangwei"]["instruction"]),
        (4, FLOWER_PLEIADES_TABLE["tumi"], FLOWER_PLEIADES_TABLE["tumi"]["instruction"]),
        (4, FLOWER_PLEIADES_TABLE["zhuyu"], FLOWER_PLEIADES_TABLE["zhuyu"]["instruction"]),
        (4, FLOWER_PLEIADES_TABLE["moli"], FLOWER_PLEIADES_TABLE["moli"]["instruction"]),
        (4, FLOWER_PLEIADES_TABLE["muxu"], FLOWER_PLEIADES_TABLE["muxu"]["instruction"]),
        (4, FLOWER_PLEIADES_TABLE["ziwulan"], FLOWER_PLEIADES_TABLE["ziwulan"]["instruction"]),
        
        # 阶段 5
        (5, DEFENDANT_SEAT, "【被告人尊长最后陈述】发表最后陈述：‘在阜阳留置室的这半年极昼里我问心无愧，我救的是企业和工人，未占公家一分钱！’"),
        (5, ZODIAC_12_CABINETS["ruby"], "收回发言权！结合 12 黄道内阁质询及七姐妹星团专家合议意见书，敲响法槌，宣告被告人尊长无罪，发表判词！")
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
    progress_bar.progress(1.0, text="⚖️ 5 阶段 12 黄道内阁满编法庭与七姐妹星团合议全流程落幕！全案笔录已永久驻留！")
    st.balloons()
    st.rerun()

st.divider()
st.markdown(
    "<div style='text-align:center;color:#888;font-size:0.85rem;padding:1.5rem 0;'>"
    "🦅 鲲鹏志 AI · 12 黄道内阁 (Zodiac Cabinets) + 昴宿七姐妹星云满编平台 · 2026"
    "</div>",
    unsafe_allow_html=True
)

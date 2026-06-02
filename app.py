"""
鲲鹏志 · 内容驱动辩论系统 v4.6
====================================
Moneyball 数据驱动辩论：
- Vectorize RAG: 原文 + 历史辩论实录
- 双教练通过历史数据迭代进步
- 每场辩论后自动归档
- 罗伯特议事规则，议事长归纳交锋
- 书面语转口头语，TTS 缝合播放
- 霞鹜文楷字体
- 教练策略在 UI 上按需显示
- 显示 RAG 检索到的原文
- **增加辩论进度和阶段性提示**
"""

import chainlit as cl
import os
import asyncio
import json
import logging
import uuid
import re
from typing import Optional, List, Dict
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(message)s")
log = logging.getLogger("kunpengzhi")

# ─── 配置 ─────────────────────────────────────────
DEBATE_MODEL = os.getenv("DEBATE_MODEL", "gemini-2.5-flash")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:4000/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-47318")
TTS_VOICE = os.getenv("TTS_VOICE", "zh-CN-YunxiNeural")
TTS_ENABLED = os.getenv("TTS_ENABLED", "true").lower() == "true"
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
R2_BUCKET = os.getenv("R2_BUCKET", "kunpengzhi-tts")
R2_PUBLIC_BASE = os.getenv("R2_PUBLIC_BASE", "https://kunpengzhi-debate.seekkey.eu.org")

TYPE_SPEED_MS = int(os.getenv("TYPE_SPEED_MS", "50")) # 正文打字速度
POEM_SPEED_MS = 80 # 定场诗慢推速度
INTRO_SPEED_MS = 100 # 引子更慢


# ─── 内容检索 ────────────────────────────────────
from core.retriever import BookRetriever


# ─── R2 存储 ─────────────────────────────────────

class R2Store:
    @staticmethod
    async def upload(key: str, data: bytes) -> bool:
        if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
            return False
        import httpx
        url = (f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}"
               f"/r2/buckets/{R2_BUCKET}/objects/{key}")
        async with httpx.AsyncClient() as c:
            r = await c.put(url, headers={"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"},
                            content=data, timeout=30)
            return r.status_code == 200 and r.json().get("success", False)

    @staticmethod
    def public_url(key: str) -> str:
        return f"{R2_PUBLIC_BASE}/{key}"


# ─── TTS ──────────────────────────────────────────

class TTSEngine:
    VOICES = {"zh-CN-YunxiNeural": "云希（男声）", "zh-CN-YunyangNeural": "云扬（男声）",
              "zh-CN-XiaoxiaoNeural": "晓晓（女声）", "zh-CN-XiaoyiNeural": "晓伊（女声）"}

    def __init__(self, voice: str = TTS_VOICE):
        self.voice = voice

    @staticmethod
    def strip_markdown(text: str) -> str:
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'\1', text)
        text = re.sub(r'#+\s*', '', text)
        text = text.replace('【', '').replace('】', '')
        text = re.sub(r'`([^`]+)`', r'\1', text)
        text = re.sub(r'\[([^]]+)]\([^)]+\)', r'\1', text)
        text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    async def to_oral(self, text: str) -> str:
        if len(text) < 20:
            return text
        try:
            prompt = f"请把以下辩论书面稿改写成自然的口头语，就像人在正常说话。\n要求：长句拆短句，加语气词（啊、吧、呢、嘛），去掉书面套话，不要任何格式符号，纯文字。\n直接输出改写结果，不要加说明。\n\n原文：\n{text[:1800]}\n\n改写："
            import openai
            client = openai.AsyncOpenAI(base_url=os.getenv("OPENAI_BASE_URL"), api_key=os.getenv("OPENAI_API_KEY"))
            resp = await client.chat.completions.create(model=DEBATE_MODEL,
                messages=[{"role": "user", "content": prompt}], timeout=15)
            result = resp.choices[0].message.content.strip()
            return result if len(result) > 10 else text
        except Exception as e:
            log.warning(f"Oralize fail: {e}")
            return text

    async def generate(self, text: str, tag: str, idx: int, tmp_paths: Optional[list] = None) -> Optional[str]:
        if not text or len(text.strip()) < 5:
            return None
        try:
            clean = self.strip_markdown(text)
            oral = await self.to_oral(clean) or clean[:2000]
            final = self.strip_markdown(oral)[:2000] or clean[:2000]
            import edge_tts
            key = f"tts/debate_{idx:03d}_{uuid.uuid4().hex[:8]}.mp3"
            tmp = f"/tmp/{uuid.uuid4().hex}.mp3"
            await edge_tts.Communicate(final, self.voice).save(tmp)
            if not os.path.exists(tmp):
                return None
            if tmp_paths is not None:
                tmp_paths.append(tmp)
            with open(tmp, "rb") as f:
                data = f.read()
            ok = await R2Store.upload(key, data)
            if ok:
                log.info(f"🔊 TTS: {tag}")
                return R2Store.public_url(key)
        except Exception as e:
            log.error(f"TTS fail {tag}: {e}")
        return None

    async def stitch_audio(self, paths: List[str]) -> Optional[str]:
        if len(paths) == 0:
            return None
        try:
            from pydub import AudioSegment
            combined = AudioSegment.empty()
            for p in paths:
                if os.path.exists(p) and os.path.getsize(p) > 100:
                    combined += AudioSegment.from_mp3(p)
                    combined += AudioSegment.silent(duration=300)
            if len(combined) > 0:
                out = f"/tmp/辩论全录_{uuid.uuid4().hex[:8]}.mp3"
                combined.export(out, format="mp3", bitrate="48k")
                with open(out, "rb") as f:
                    data = f.read()
                key = f"tts/debate_full_{uuid.uuid4().hex[:8]}.mp3"
                ok = await R2Store.upload(key, data)
                for p in paths:
                    try:
                        os.remove(p)
                    except:
                        pass
                os.remove(out)
                if ok:
                    log.info(f"🎧 辩论全录: {len(data)} bytes")
                    return R2Store.public_url(key)
        except Exception as e:
            log.warning(f"Stitch fail: {e}")
        return None


# ─── 辩题库 ──────────────────────────────────────

TOPICS = {
    "1": {"title": "白貂皮大衣：全球贸易网络的铁证 vs 过度诠释",
          "pro": "白貂皮大衣是嚈哒帝国与东北亚保持联系的铁证",
          "con": "白貂皮大衣是转手贸易的结果，族群记忆是过度诠释",
          "abstract": "北魏正光元年（520年），一件白貂皮大衣从波斯经嚈哒帝国辗转至北魏宫廷。"},
    "2": {"title": "木兰的哥哥：历史真相 vs 叙事虚构",
          "pro": "木兰无长兄的真正含义是长兄参加了大同流亡军团西征",
          "con": "木兰无长兄是文学修辞，强行关联嚈哒帝国是过度解读",
          "abstract": "《木兰辞》中'阿爷无大儿，木兰无长兄'——是文学加工还是史实线索？"},
    "3": {"title": "产权分割理论：安史之乱的经济学本质",
          "pro": "安史之乱=大股东收购母公司，产权理论是利器",
          "con": "用企业并购解释安史之乱是削足适履",
          "abstract": "公元755年安禄山起兵范阳。节度使制度制造了代理人困境。"},
}

SPEAKER_POEMS = {
    "正方一辩": """【乾 ☰ · 吕洞宾 —— 鹊桥仙】\n一柄纯阳宝剑，寒芒乍现，辞却九重天阙。人间自古情难尽，斩不绝、红尘恩怨。醉扶吕祖，清吟太白，试问纯阳生灭。道心点破鹊桥边，化作了、清风明月。""",
    "反方一辩": """【坤 ☷ · 何仙姑 —— 卷珠帘】\n手执碧水青莲步玉沙。云散处、现仙家。不染红尘半点，珠帘高卷，缥缈看流霞。弱水三千空浪迹。心似月、净无瑕。一缕香风归去，高唐梦醒，独坐守瑶华。""",
    "正方二辩": """【艮 ☶ · 张果老 —— 临江仙】\n倒骑毛驴江渚上，朝行碧海苍梧。手扣通玄渔鼓道情孤。古今多少事，盲眼看虚无。莫问老翁年几许，曾陪尧舜双枯。冷眼公卿尽泥涂。乾坤装入壳，一杖任徐驱。""",
    "反方二辩": """【兑 ☱ · 韩湘子 —— 苏幕遮】\n紫金箫，清怨起。声振灵樾，音动微茫里。碧海苍梧飞仙履。一曲横吹，截断江河水。少年郎，心不死。踏遍群山，笑看红尘死。万古沧桑皆入耳。渔鼓声沉，唯有仙音在。""",
    "正方三辩": """【离 ☲ · 汉钟离 —— 一剪梅】\n手摇芭蕉宝扇夜气清。急鼓初催，乐奏公卿。满堂金翠转头空，大汉将军，解甲归蓬。一展神风雾隐腾。莫问流光，冷眼输赢。任他樱桃红透时，几度春风，老了仙翁。""",
    "反方三辩": """【坎 ☵ · 蓝采和 —— 西江月】\n手执叠板花篮，盛来满槛春风。竹板声声戏顽童，醉倒长街乱冢。几点山前疏雨，半宵稻海鸣虫。算来贫贱与公侯，都是南柯一梦。""",
    "正方四辩": """【震 ☳ · 曹国舅 —— 虞美人】\n掌中云阳玉笏何时了？权柄如罂粟。满城开遍美人花，谁解红衣妖艳、是鸩家。雕栏玉砌生尸骨，大梦惊吞吐。老夫脱却大朝衣，洗净满身浮毒、白云归。""",
    "反方四辩": """【巽 ☴ · 铁拐李 —— 卜算子】\n背负太极葫芦落红尘，拐杖惊风雨。莫笑形骸至贱躯，壶里乾坤寓。酒肉任穿肠，不肯栖寒树。待到悬壶济世时，散作山前雾。""",
}

POEM_SPEED_MS = 80   # ms/字
INTRO_SPEED_MS = 100  # 引子更慢

DEBATE_ROLES = [
    ("正方一辩", "开篇立论"), ("反方一辩", "开篇立论"),
    ("正方二辩", "驳论"), ("反方二辩", "驳论"),
    ("正方三辩", "自由辩论"), ("反方三辩", "自由辩论"),
    ("正方四辩", "总结陈词"), ("反方四辩", "总结陈词"),
]


# ─── Vectorize RAG ──────────────────────────────

from core.vectorize import get_relevant_chunks, index_sources, vectorize_query, embed


# ─── 教练系统（Moneyball 数据驱动）──────────────

class DebateCoach:
    @staticmethod
    async def generate_pre_strategy(
        topic_id: str,
        book_content: str,
        side: str,  # "pro" or "con"
        past_debates: str = "",
    ) -> str:
        """
        教练阅读原文 + 历史辩论记录（Moneyball 数据驱动），输出赛前策略
        """
        t = TOPICS.get(topic_id, TOPICS["1"])
        stance_label = f"正方（支持：{t['pro']}）" if side == "pro" else f"反方（反对：{t['con']}）"

        past_section = ""
        if past_debates:
            past_section = f"""
## 历史辩论参考（Moneyball 数据）
以下是从之前辩论中提取的相关内容，请分析哪些策略有效、哪些被对方攻破：

{past_debates[:3000]}
"""

        prompt = f"""
你是一名资深辩论教练。你的队伍即将参加一场 4v4 辩论赛。

## 辩题
{t['title']}

## 你的阵营
{stance_label}

## 原文参考
{book_content[:6000]}

{past_section}

## 任务
请输出一份 pre-flight check 和战略分析，包含：

1. **辩题深度解析** — 阐述这个辩题在《鲲鹏志》的整个宏大叙事中处于什么关键节点？为什么要辩论它？有何重要意义？
2. **核心论据** — 原文中哪些段落/证据可以支撑你的立场？每一条论据都要标注原文出处。
3. **对方可能的攻击点** — 对方可能会引用哪些段落攻击你？如何防守？
4. **历史教训** — 如果之前有人辩过类似论点，哪些策略有效、哪些被反方破过？
5. **战术布置** — 四个辩手各自应该侧重什么？一辩立论应引用什么？二辩驳论应针对什么？三辩自由辩论应抓住什么？四辩总结应升华什么？

要求：每条论据都要有原文引用。教练的分析必须深刻，有战略高度。
"""
        import openai
        client = openai.AsyncOpenAI(base_url=os.getenv("OPENAI_BASE_URL"), api_key=os.getenv("OPENAI_API_KEY"))
        resp = await client.chat.completions.create(model=DEBATE_MODEL,
            messages=[{"role": "user", "content": prompt}])
        return resp.choices[0].message.content


# ─── 单轮辩论 ────────────────────────────────────

async def debate_round(topic_id: str, role: str, stage: str,
                       book_content: str, pro_strat: str, con_strat: str,
                       history: str) -> str:
    t = TOPICS.get(topic_id, TOPICS["1"])
    side = "正方" if "正方" in role else "反方"
    stance = t["pro"] if "正方" in role else t["con"]
    opponent = "正方" if "反方" in role else "反方"
    coach = pro_strat if "正方" in role else con_strat

    last_section = ""
    if history.strip():
        last_section = f"\n## 上一位发言\n{history.strip()[-2000:]}\n⚠️ 必须直接回应上一位发言者的核心论点。\n"

    prompt = f"""
你是一名 4v4 辩论赛的辩手。

## 你是谁
- 角色: {role}（{stage}） 阵营: {side} 立场: {stance} 对手: {opponent}

## 原文参考
{book_content[:4000]}

## 教练策略
{coach[:2000]}

{last_section}

## 要求
- 以「{role}」开头
- 必须直接回应上一位（开场则立论）
- 引用原文出处
- 风格犀利，400字以内

现在发言：
"""
    import openai
    client = openai.AsyncOpenAI(base_url=os.getenv("OPENAI_BASE_URL"), api_key=os.getenv("OPENAI_API_KEY"))
    return await client.chat.completions.create(
        model=DEBATE_MODEL, messages=[{"role": "user", "content": prompt}], stream=True)


# ─── 议事长 ──────────────────────────────────────

class Chair:
    @staticmethod
    async def summarize(topic_id: str, last_role: str, last_text: str,
                        prev_role: str, prev_text: str) -> str:
        t = TOPICS.get(topic_id, TOPICS["1"])
        prompt = f"辩论归纳：\n辩题：{t['title']}\n上轮：{prev_role}说{prev_text[:500]}\n本轮：{last_role}说{last_text[:500]}\n\n用80字归纳交锋焦点。"
        import openai
        client = openai.AsyncOpenAI(base_url=os.getenv("OPENAI_BASE_URL"), api_key=os.getenv("OPENAI_API_KEY"))
        resp = await client.chat.completions.create(model=DEBATE_MODEL,
            messages=[{"role": "user", "content": prompt}])
        return resp.choices[0].message.content


# ─── 辩论实录存档 ──────────────────────────────

async def save_and_index_transcript(topic_id: str, history: str, pro_strat: str, con_strat: str):
    """
    辩论结束后：保存到 R2 (md 文件) + 索引到 Vectorize
    Moneyball: 策略和辩论实录都索引进去，供教练未来学习
    """
    try:
        t = TOPICS.get(topic_id, TOPICS["1"])
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        title_safe = re.sub(r'[^a-zA-Z0-9_一-龥]', '', t['title'][:20])

        transcript_md = f"""# 🦅 鲲鹏志 · 辩论实录

辩题: {t['title']}
时间: {ts}
模型: {DEBATE_MODEL}

## 正方策略
{pro_strat}

## 反方策略
{con_strat}

## 辩论全文
{history}
"""
        key = f"debates/辩论实录_{title_safe}_{ts}.md"
        await R2Store.upload(key, transcript_md.encode())

        # 索引到 Vectorize
        # 索引内容: 辩论全文 + 双方策略
        index_text = history[:5000] + "\n\n## 正方策略\n" + pro_strat[:2000] + "\n\n## 反方策略\n" + con_strat[:2000]
        await index_sources({f"辩论实录/{title_safe}_{ts}": index_text},
                           source_type="debate")
        log.info(f"📝 辩论已归档: {key}")
    except Exception as e:
        log.warning(f"Archive fail: {e}")


# ─── 主席 Chainlit 流式 ──────────────────────────

async def run_debate_stream(msg: cl.Message, topic_id: str) -> list:
    t = TOPICS.get(topic_id, TOPICS["1"])

    # 1. 加载原文（本地→GitHub→Vectorize）
    chapters_data = await BookRetriever.load_relevant_chapters(topic_id)
    book_content = BookRetriever.extract_relevant(chapters_data) if chapters_data else ""

    # 2. 检索历史辩论数据（Moneyball）
    past_debates = ""
    try:
        # 向量搜索历史辩论，找到与当前辩题相关的记录
        debate_matches = await vectorize_query(t["title"], top_k=5)
        if debate_matches:
            past_lines = []
            for m in debate_matches:
                if m.get("source", "").startswith("辩论实录"):
                    # 原始的 debate full text 存储在 Vectorize 的 text 字段中，这里取出来
                    # 注意：text[:300] 是索引时的摘要，不是全文
                    past_lines.append(f"- **{m['source'].replace('辩论实录/', '').replace('_', ' ')}** (相似度: {m['score']:.3f})\n  {m.get('text', '')[:300]}")
            if past_lines:
                past_debates = "\n".join(past_lines)
                log.info(f"📊 Moneyball: 找到 {len(past_lines)} 条历史辩论")
    except Exception as e:
        log.warning(f"Moneyball query fail: {e}")

    # ── 阶段 1/4: 原文检索结果显示 ──
    if book_content:
        for ch in f"📖 **原文检索结果**:\n\n{book_content}\n\n---\n\n":
            await msg.stream_token(ch)
            await asyncio.sleep(8 / 1000) # 原文显示速度稍慢
        await asyncio.sleep(0.5) # 显示完原文停顿

    else:
        for ch in "⚠️ **未能从书库或历史辩论中检索到相关原文。请确保书库已索引。**\n\n":
            await msg.stream_token(ch)
            await asyncio.sleep(6 / 1000)
        await asyncio.sleep(0.5)

    await cl.Message(content="**[进度: 1/4] 原文检索完成，教练正在研读并制定策略...**\n").send()

    # ── 阶段 2/4: 双教练并行 ──
    log.info("🏋️ 教练分析中...")
    pro_strat, con_strat = await asyncio.gather(
        DebateCoach.generate_pre_strategy(topic_id, book_content, "pro", past_debates),
        DebateCoach.generate_pre_strategy(topic_id, book_content, "con", past_debates),
    )
    log.info(f"✅ 策略完成: pro={len(pro_strat)}c con={len(con_strat)}c")

    # 存储完整策略到 user_session
    cl.user_session.set("pro_strat", pro_strat)
    cl.user_session.set("con_strat", con_strat)
    cl.user_session.set("topic_title", t["title"])

    # 显示教练策略摘要 + 查看按钮
    actions = [
        cl.Action(name="show_coach_briefing", value="show_briefing", label="📊 查看教练策略", payload="show_briefing")
    ]
    await cl.Message(content="**[进度: 2/4] 教练策略已部署，辩论即将开始...**", actions=actions).send()

    # ── 阶段 3/4: 辩论进行中 ──
    await msg.stream_token("🏛️ **议事长**: 欢迎来到鲲鹏志辩论现场！本场辩论采用罗伯特议事规则。\n"
                           "每轮发言后麦克风交还议事长，由议事长归纳交锋，确保辩论焦点清晰。\n"
                           "双方辩手将围绕辩题展开激烈交锋，并引用《鲲鹏志》书库原文。\n\n")
    await asyncio.sleep(INTRO_SPEED_MS / 1000 * 30) # 模拟更慢的开场白

    history = ""
    last_role, last_text = "", ""
    prev_role, prev_text = "", ""
    round_idx = 0
    tts_tasks = []
    tmp_paths = []

    for role, stage in DEBATE_ROLES:
        round_idx += 1
        # 总共 8 轮辩论，加上开场白，可以粗略认为 9 个环节
        total_stages = len(DEBATE_ROLES) + 1 # +1 for final summary

        # 议事长归纳（非首轮）
        if round_idx > 1:
            summary = await Chair.summarize(topic_id, last_role, last_text, prev_role, prev_text)
            for ch in f"\n\n🏛️ **议事长**: {summary}\n":
                await msg.stream_token(ch)
                await asyncio.sleep(6 / 1000) # 议事长语速稍慢
            await asyncio.sleep(0.5)

        if last_role:
            prev_role, prev_text = last_role, last_text

        # 主席传麦
        side_color = "🔴" if "正方" in role else "🔵"
        for ch in f"\n\n🎙️ **主席**: **[进度: {round_idx}/{total_stages}]** {side_color} 有请 {role}（{stage}）——\n":
            await msg.stream_token(ch)
            await asyncio.sleep(5 / 1000) # 主席语速

        # 八仙定场诗
        poem = SPEAKER_POEMS.get(role, "") # 使用 SPEAKER_POEMS
        if poem:
            for pch in poem:
                await msg.stream_token(pch)
                await asyncio.sleep(POEM_SPEED_MS / 1000)
            await msg.stream_token("\n\n")
            await asyncio.sleep(0.3)

        # 生成该轮
        stream = await debate_round(topic_id, role, stage, book_content, pro_strat, con_strat, history)
        round_text = ""
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                round_text += delta.content
                for ch in delta.content:
                    await msg.stream_token(ch)
                    await asyncio.sleep(TYPE_SPEED_MS / 1000)

        history += f"\n\n【{role}】{round_text.strip()}"
        last_role, last_text = role, round_text.strip()

        if round_text.strip():
            await asyncio.sleep(0.5)
            if TTS_ENABLED:
                t = asyncio.ensure_future(
                    TTSEngine().generate(
                        re.sub(r"^【[^】]+】\s*", "", round_text).strip(),
                        role, round_idx, tmp_paths))
                tts_tasks.append(t)

    # 议事长最终总结
    if last_role and last_text:
        final_summary = await Chair.summarize(topic_id, last_role, last_text, prev_role, prev_text)
        for ch in f"\n\n🏛️ **议事长总结**: {final_summary}\n":
            await msg.stream_token(ch)
            await asyncio.sleep(6 / 1000)

    await msg.stream_token("\n\n---\n✅ **辩论结束**")
    await msg.send()

    # ── 阶段 4/4: 音频处理与存档 ──
    tts_url = None
    if tts_tasks:
        log.info(f"⏳ 等待 {len(tts_tasks)} 段 TTS...")
        await asyncio.gather(*tts_tasks)
        stitched = await TTSEngine().stitch_audio(tmp_paths)
        if stitched:
            tts_url = stitched
            await cl.Message(content=f"## 🎧 完整辩论录音\n\n<audio controls src='{stitched}' style='width:100%'></audio>").send()
        else:
            await cl.Message(content="ℹ️ 语音合成失败，跳过。").send()
    else:
        await cl.Message(content="ℹ️ 语音生成跳过（TTS 未开启或内容过短）。").send()

    await cl.Message(content="**[进度: 4/4] 辩论全程已归档。请查看上方录音回放。**").send()

    # 存档 + 索引 (现在 Vectorize 已经支持)
    asyncio.ensure_future(save_and_index_transcript(topic_id, history, pro_strat, con_strat))

    return [tts_url] if tts_url else []


@cl.action_callback("show_coach_briefing")
async def show_coach_briefing(action: cl.Action):
    log.info("Coach briefing button clicked")
    pro_strat = cl.user_session.get("pro_strat")
    con_strat = cl.user_session.get("con_strat")
    topic_title = cl.user_session.get("topic_title")

    if not pro_strat or not con_strat:
        await cl.Message(content="教练策略未找到，请重试辩论。").send()
        return

    await cl.Message(content=f"""
## 🕵️ **教练策略全貌：{topic_title}**

---

### 🔴 **正方教练：战略部署**
{pro_strat}

---

### 🔵 **反方教练：战略部署**
{con_strat}

""").send()

    await action.remove() # 移除点击过的按钮


# ─── Chainlit ─────────────────────────────────────

@cl.password_auth_callback
def auth_callback(username: str, password: str):
    valid_users = {
        "84621942@qq.com": "1314",
        "ben@git4ta.fun": "3131",
    }
    env_pwd = os.getenv("APP_PASSWORD")
    if env_pwd and password == env_pwd:
        return cl.User(identifier=username)
        
    if username in valid_users and valid_users[username] == password:
        return cl.User(identifier=username)
    return None

@cl.on_chat_start
async def start():
    await cl.Message(content="""🦅 **鲲鹏志 · Moneyball 数据驱动辩论**

## 辩题库
1️⃣ 白貂皮大衣：全球贸易铁证 vs 过度诠释
2️⃣ 木兰的哥哥：历史真相 vs 叙事虚构
3️⃣ 产权分割理论：安史之乱的经济学本质

每场辩论实录自动存档，教练通过历史数据迭代进步 📊
输入数字开始！
"""
    ).send()

@cl.on_message
async def main(message: cl.Message):
    topic_id = message.content.strip()
    topic = TOPICS.get(topic_id)
    if not topic:
        await cl.Message(content="请选择 1、2 或 3").send()
        return

    msg = cl.Message(content=f"🎯 **辩题**: {topic['title']}\n\n")
    if topic["abstract"]:
        for ch in f"📖 **背景**: {topic['abstract']}\n\n":
            await msg.stream_token(ch)
            await asyncio.sleep(8 / 1000)

    if TTS_ENABLED:
        for ch in "🔊 **语音模式已开启**\n\n":
            await msg.stream_token(ch)
            await asyncio.sleep(10 / 1000)

    log.info(f"🎯 辩题: {topic['title']}")
    await run_debate_stream(msg, topic_id)
    log.info(f"✅ 完成: {topic['title']}")

if __name__ == "__main__":
    print("鲲鹏志 v4.6 · chainlit run app.py")

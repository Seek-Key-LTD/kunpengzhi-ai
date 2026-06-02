"""
鲲鹏志 · 内容驱动辩论系统 v4.0
====================================
Moneyball 数据驱动辩论：
- Vectorize RAG: 原文 + 历史辩论实录
- 双教练通过历史数据迭代进步
- 每场辩论后自动归档
"""

import chainlit as cl
import os
import asyncio
import json
import logging
import uuid
import re
from typing import Optional, List
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
TYPE_SPEED_MS = int(os.getenv("TYPE_SPEED_MS", "50"))
SIGIL_SPEED_MS = 80


# ─── 内容检索 ────────────────────────────────────
from core.retriever import BookRetriever


# ─── R2 ──────────────────────────────────────────

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
        return text.strip()

    async def to_oral(self, text: str) -> str:
        if len(text) < 20:
            return text
        try:
            prompt = f"请把以下文字改写成自然的口头语。\n要求：长句拆短句，加语气词（啊、吧、呢、嘛），去掉书面套话，**不要任何格式符号**，纯文字。\n\n原文：\n{text[:1800]}\n\n改写："
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

SPEAKER_SIGILS = {
    "正方一辩": "☰ 吕洞宾·纯阳剑·道心点破鹊桥边", "反方一辩": "☷ 何仙姑·碧水莲·一缕香风归去瑶华",
    "正方二辩": "☶ 张果老·渔鼓·古今多少事盲眼看虚无", "反方二辩": "☱ 韩湘子·紫金箫·一曲横吹截断江河水",
    "正方三辩": "☲ 汉钟离·芭蕉扇·任他樱桃红透老了仙翁", "反方三辩": "☵ 蓝采和·花竹板·贫贱与公侯南柯一梦",
    "正方四辩": "☳ 曹国舅·云阳笏·洗净满身浮毒白云归", "反方四辩": "☴ 铁拐李·太极葫·待到悬壶济世散作山前雾",
}

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
        topic_id: str, book_content: str, side: str,
        past_debates: str = "",
    ) -> str:
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
输出 pre-flight check：

1. **核心论据** — 每条标注原文出处
2. **对方可能的攻击点** — 如何防守？
3. **历史教训** — 如果之前有人辩过类似论点，哪些策略有效、哪些被反方破过？
4. **战术布置** — 四个辩手各自侧重什么？

要求：每条论据都要有原文引用。
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
你是一名 4v4 辩论赛辩手。

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
    """辩论结束后：保存到 R2 + 索引到 Vectorize"""
    try:
        t = TOPICS.get(topic_id, TOPICS["1"])
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 保存全文到 R2
        transcript = f"""# 🦅 鲲鹏志 · 辩论实录

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
        key = f"debates/辩论实录_{t['title'][:12]}_{ts}.md"
        await R2Store.upload(key, transcript.encode())

        # 索引到 Vectorize
        await index_sources({f"辩论实录/{ts}": history[:5000] + "\n\n## 正方策略\n" + pro_strat[:2000] + "\n\n## 反方策略\n" + con_strat[:2000]},
                           source_type="debate")
        log.info(f"📝 辩论已归档: {key}")
    except Exception as e:
        log.warning(f"Archive fail: {e}")


# ─── 主席 Chainlit 流式 ──────────────────────────

async def run_debate_stream(msg: cl.Message, topic_id: str) -> list:
    t = TOPICS.get(topic_id, TOPICS["1"])

    # 1. 加载原文（本地→GitHub→Vectorize）
    retriever = BookRetriever()
    chapters = await retriever.load_relevant_chapters(topic_id)
    book_content = retriever.extract_relevant(chapters) if chapters else ""

    # 2. 查历史辩论数据（Moneyball）
    past_debates = ""
    try:
        debate_matches = await vectorize_query(t["title"], top_k=5)
        if debate_matches:
            past_lines = []
            for m in debate_matches:
                if m.get("source", "").startswith("辩论实录"):
                    past_lines.append(f"- [{m['source']}] (匹配度: {m['score']:.3f})\n  {m.get('text', '')[:300]}")
            if past_lines:
                past_debates = "\n".join(past_lines)
                log.info(f"📊 Moneyball: {len(past_lines)} 条历史辩论")
    except Exception as e:
        log.warning(f"Moneyball query fail: {e}")

    # ── 原文梗概 ──
    if chapters:
        synopsis = f"已加载 {len(chapters)} 份相关材料"
        for s_ch in f"📖 **原文**: {synopsis}\n\n":
            await msg.stream_token(s_ch)
            await asyncio.sleep(6 / 1000)
    else:
        for s_ch in "⚠️ **未加载到原文，请先索引书库**\n\n":
            await msg.stream_token(s_ch)
            await asyncio.sleep(6 / 1000)

    # ── 双教练并行 ──
    log.info("🏋️ 教练分析中...")
    pro_strat, con_strat = await asyncio.gather(
        DebateCoach.generate_pre_strategy(topic_id, book_content, "pro", past_debates),
        DebateCoach.generate_pre_strategy(topic_id, book_content, "con", past_debates),
    )
    log.info(f"✅ 策略完成: pro={len(pro_strat)}c con={len(con_strat)}c")

    # 显示教练策略摘要
    await msg.stream_token(f"\n🏛️ **正方教练策略**: {pro_strat[:150]}...\n")
    await asyncio.sleep(0.3)
    await msg.stream_token(f"🏛️ **反方教练策略**: {con_strat[:150]}...\n\n")
    await asyncio.sleep(0.3)

    # ── 辩论开始 ──
    await msg.stream_token("🎙️ **辩论开始（罗伯特议事规则）**\n\n")
    await asyncio.sleep(0.5)

    history = ""
    last_role, last_text = "", ""
    prev_role, prev_text = "", ""
    round_idx = 0
    tts_tasks = []
    tmp_paths = []

    for role, stage in DEBATE_ROLES:
        round_idx += 1

        # 议事长归纳
        if prev_role and prev_text and last_role and last_text:
            summary = await Chair.summarize(topic_id, last_role, last_text, prev_role, prev_text)
            for ch in f"\n\n🏛️ **议事长**: {summary}\n":
                await msg.stream_token(ch)
                await asyncio.sleep(5 / 1000)
            await asyncio.sleep(0.3)

        if last_role:
            prev_role, prev_text = last_role, last_text

        # 主席传麦
        side_color = "🔴" if "正方" in role else "🔵"
        for ch in f"\n\n🎙️ **主席**: {side_color} 请 {role}（{stage}）\n":
            await msg.stream_token(ch)
            await asyncio.sleep(4 / 1000)

        sigil = SPEAKER_SIGILS.get(role, "")
        if sigil:
            for sch in sigil:
                await msg.stream_token(sch)
                await asyncio.sleep(SIGIL_SPEED_MS / 1000)
            await msg.stream_token("\n\n")
            await asyncio.sleep(0.2)

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
            await asyncio.sleep(0.4)
            if TTS_ENABLED:
                t = asyncio.ensure_future(
                    TTSEngine().generate(
                        re.sub(r"^【[^】]+】\s*", "", round_text).strip(),
                        role, round_idx, tmp_paths))
                tts_tasks.append(t)

    # 议事长最终
    if last_role and last_text:
        final_summary = await Chair.summarize(topic_id, last_role, last_text, prev_role, prev_text)
        await msg.stream_token(f"\n\n🏛️ **议事长总结**: {final_summary}")

    await msg.stream_token("\n\n---\n✅ **辩论结束**")
    await msg.send()

    # ─ TTS ─
    tts_url = None
    if tts_tasks:
        log.info(f"⏳ 等待 {len(tts_tasks)} 段 TTS...")
        await asyncio.gather(*tts_tasks)
        stitched = await TTSEngine().stitch_audio(tmp_paths)
        if stitched:
            tts_url = stitched
            await cl.Message(content=f"## 🎧 完整辩论录音\n\n<audio controls src='{stitched}' style='width:100%'></audio>").send()
        else:
            await cl.Message(content="ℹ️ 语音合成跳过").send()

    # ─ 存档 + 索引 ─
    asyncio.ensure_future(save_and_index_transcript(topic_id, history, pro_strat, con_strat))

    return [tts_url] if tts_url else []


# ─── Chainlit ─────────────────────────────────────

@cl.password_auth_callback
def auth_callback(username: str, password: str):
    pwd = os.getenv("APP_PASSWORD", "3131")
    if password == pwd:
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
""").send()

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
    print("鲲鹏志 v4.0 · chainlit run app.py")

"""
鲲鹏志 · 内容驱动辩论系统 v3.0
====================================
4v4 林肯-道格拉斯式辩论
- Graph RAG 从书库提取相关段落
- 双教练 pre-strategy / pre-flight check
- 每轮必须回应前一人
- 霞鹜文楷字体
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(message)s",
)
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
R2_PUBLIC_BASE = os.getenv(
    "R2_PUBLIC_BASE",
    "https://pub-777cf729d9534822b99f4ab446ac6059.r2.dev",
)

TYPE_SPEED_MS = int(os.getenv("TYPE_SPEED_MS", "50"))
SIGIL_SPEED_MS = 80   # 签诗慢推 ms/字


# ─── 内容检索 ────────────────────────────────────

from core.retriever import load_topic_content, BookRetriever


# ─── R2 存储 ─────────────────────────────────────

class R2Store:
    @staticmethod
    async def upload(key: str, data: bytes) -> bool:
        if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
            return False
        import httpx
        url = (
            f"https://api.cloudflare.com/client/v4/accounts"
            f"/{CLOUDFLARE_ACCOUNT_ID}/r2/buckets/{R2_BUCKET}/objects/{key}"
        )
        async with httpx.AsyncClient() as c:
            r = await c.put(
                url,
                headers={"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"},
                content=data,
                timeout=30,
            )
            return r.status_code == 200 and r.json().get("success", False)

    @staticmethod
    def public_url(key: str) -> str:
        return f"{R2_PUBLIC_BASE}/{key}"


# ─── TTS ──────────────────────────────────────────

class TTSEngine:
    VOICES = {
        "zh-CN-YunxiNeural": "云希（男声）",
        "zh-CN-YunyangNeural": "云扬（男声）",
        "zh-CN-XiaoxiaoNeural": "晓晓（女声）",
        "zh-CN-XiaoyiNeural": "晓伊（女声）",
    }

    def __init__(self, voice: str = TTS_VOICE):
        self.voice = voice

    async def generate(self, text: str, tag: str, idx: int) -> Optional[str]:
        if not text or len(text.strip()) < 5:
            return None
        try:
            import edge_tts
            key = f"tts/debate_{idx:03d}_{uuid.uuid4().hex[:8]}.mp3"
            tmp = f"/tmp/{uuid.uuid4().hex}.mp3"
            await edge_tts.Communicate(text[:2000], self.voice).save(tmp)
            if not os.path.exists(tmp):
                return None
            with open(tmp, "rb") as f:
                data = f.read()
            ok = await R2Store.upload(key, data)
            os.remove(tmp)
            if ok:
                log.info(f"🔊 TTS: {tag}")
                return R2Store.public_url(key)
        except Exception as e:
            log.error(f"TTS fail {tag}: {e}")
        return None


# ─── 辩题库 ──────────────────────────────────────

TOPICS = {
    "1": {
        "title": "白貂皮大衣：全球贸易网络的铁证 vs 过度诠释",
        "pro": "白貂皮大衣是嚈哒帝国与东北亚保持联系的铁证",
        "con": "白貂皮大衣是转手贸易的结果，族群记忆是过度诠释",
        "abstract": "北魏正光元年（520年），一件白貂皮大衣从波斯经嚈哒帝国辗转至北魏宫廷。",
    },
    "2": {
        "title": "木兰的哥哥：历史真相 vs 叙事虚构",
        "pro": "木兰无长兄的真正含义是长兄参加了大同流亡军团西征",
        "con": "木兰无长兄是文学修辞，强行关联嚈哒帝国是过度解读",
        "abstract": "《木兰辞》中'阿爷无大儿，木兰无长兄'——是文学加工还是史实线索？",
    },
    "3": {
        "title": "产权分割理论：安史之乱的经济学本质",
        "pro": "安史之乱=大股东收购母公司，产权理论是利器",
        "con": "用企业并购解释安史之乱是削足适履",
        "abstract": "公元755年安禄山起兵范阳。节度使制度制造了代理人困境。",
    },
}

# 八仙签诗
SPEAKER_SIGILS = {
    "正方一辩": "☰ 吕洞宾·纯阳剑 · 道心点破鹊桥边",
    "反方一辩": "☷ 何仙姑·碧水莲 · 一缕香风归去瑶华",
    "正方二辩": "☶ 张果老·渔鼓 · 古今多少事盲眼看虚无",
    "反方二辩": "☱ 韩湘子·紫金箫 · 一曲横吹截断江河水",
    "正方三辩": "☲ 汉钟离·芭蕉扇 · 任他樱桃红透老了仙翁",
    "反方三辩": "☵ 蓝采和·花竹板 · 贫贱与公侯南柯一梦",
    "正方四辩": "☳ 曹国舅·云阳笏 · 洗净满身浮毒白云归",
    "反方四辩": "☴ 铁拐李·太极葫 · 待到悬壶济世散作山前雾",
}

DEBATE_ROLES = [
    ("正方一辩", "开篇立论"),
    ("反方一辩", "开篇立论"),
    ("正方二辩", "驳论"),
    ("反方二辩", "驳论"),
    ("正方三辩", "自由辩论"),
    ("反方三辩", "自由辩论"),
    ("正方四辩", "总结陈词"),
    ("反方四辩", "总结陈词"),
]


# ─── 教练系统 ────────────────────────────────────

class DebateCoach:
    """双教练：阅读原文 → 输出 pre-strategy"""

    @staticmethod
    async def generate_pre_strategy(
        topic_id: str,
        book_content: str,
        side: str,  # "pro" or "con"
    ) -> str:
        """
        教练阅读原文 + 彩虹屁/批判，输出赛前策略
        """
        t = TOPICS.get(topic_id, TOPICS["1"])
        stance_label = "正方（支持：" + t["pro"] + "）" if side == "pro" else "反方（反对：" + t["con"] + "）"

        prompt = f"""
你是一名资深辩论教练。你的队伍即将参加一场 4v4 辩论赛。

## 辩题
{t['title']}

## 你的阵营
{stance_label}

## 原文参考（从《鲲鹏志》书库中提取的相关章节）
{book_content[:6000]}

## 任务
请输出一份 pre-strategy / pre-flight check，包含：

1. **核心论据** — 原文中哪些段落/证据可以支撑你的立场？每一条论据都要标注原文出处。
2. **对方可能的攻击点** — 对方可能会引用哪些段落攻击你？如何防守？
3. **关键金句** — 从原文中提炼 2-3 句可以引用的原句，注明出处。
4. **战术布置** — 四个辩手各自应该侧重什么？一辩立论应引用什么？二辩驳论应针对什么？三辩自由辩论应抓住什么？四辩总结应升华什么？

要求：每条论据都要有**原文引用**，不能凭空捏造。
"""
        import openai
        client = openai.AsyncOpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        resp = await client.chat.completions.create(
            model=DEBATE_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content


# ─── 单轮辩论 ────────────────────────────────────

async def debate_round(
    topic_id: str,
    role: str,            # "正方一辩" / "反方二辩" ...
    stage: str,           # "开篇立论" / "驳论" ...
    book_content: str,    # 原文参考
    pro_strategy: str,    # 正方教练策略
    con_strategy: str,    # 反方教练策略
    history: str,         # 之前所有轮次的完整记录
) -> str:
    """生成一轮辩论发言，必须回应前一个人"""
    t = TOPICS.get(topic_id, TOPICS["1"])
    side = "正方" if "正方" in role else "反方"
    stance = t["pro"] if "正方" in role else t["con"]
    opponent = "正方" if "反方" in role else "反方"
    coach_strat = pro_strategy if "正方" in role else con_strategy

    has_history = bool(history.strip())
    last_speaker_instruction = ""
    if has_history:
        last_speaker_instruction = f"""
## 上一位发言者
{history.strip()[-2000:]}

⚠️ **你必须针对上一位发言者的论点做出直接回应。**
先指出对方论点的问题，再展开你的论述。不能自说自话。
"""

    prompt = f"""
你是一名 4v4 林肯-道格拉斯辩论赛的辩手。

## 你是谁
- **角色**: {role}（{stage}）
- **阵营**: {side}
- **立场**: {stance}
- **对面**: {opponent}

## 原文参考（鲲鹏志书库）
{book_content[:4000]}

## 你的教练策略
{coach_strat[:2000]}

{last_speaker_instruction}

## 格式要求
- 以「{role}」开头
- 必须直接回应上一位发言者的核心论点（如果是开场则直接立论）
- 引用原文证据时注明出处（如"据《牧人记》第07章记载…"）
- 风格犀利、有火药味
- 控制在 400 字以内

现在请发言：
"""
    import openai
    client = openai.AsyncOpenAI(
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    stream = await client.chat.completions.create(
        model=DEBATE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    return stream


# ─── 梗概生成 ────────────────────────────────────

async def generate_synopsis(book_content: str, topic_title: str) -> str:
    """快速生成原文梗概，先过一遍文章再辩论"""
    prompt = f"""请快速阅读以下文章节选，输出一份 300 字以内的梗概。

## 文章（节选）
{book_content[:5000]}

## 要求
- 核心论点是什么？
- 作者用了哪些关键证据？
- 和辩题「{topic_title}」的关系是什么？

用平实的语言写，让没读过原文的人也能跟上。
"""
    import openai
    client = openai.AsyncOpenAI(
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    resp = await client.chat.completions.create(
        model=DEBATE_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


# ─── 主席 / 议事长（Robert\'s Rules）─────────────

class Chair:
    """
    议事长（Orchestrator）：罗伯特议事规则中心节点
    - 每轮发言后，议事长收麦、归纳、再传麦
    """

    @staticmethod
    async def summarize(
        topic_id: str,
        last_role: str,
        last_text: str,
        prev_role: str,
        prev_text: str,
    ) -> str:
        """议事长归纳上一轮交锋"""
        t = TOPICS.get(topic_id, TOPICS["1"])
        prompt = f"""你是辩论赛议事长（Orchestrator），采用罗伯特议事规则。

## 辩题
{t['title']}

## 上一轮发言
【{prev_role}】{prev_text[:800]}

## 本轮发言
【{last_role}】{last_text[:800]}

## 任务
用 100 字以内归纳：
1. 本轮发言的核心论点是什么？
2. 和上一轮的分歧点在哪里？
3. 用一句总结性的话过渡给下一位发言者。

不要评价谁对谁错，只需陈述交锋焦点。
"""
        import openai
        client = openai.AsyncOpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        resp = await client.chat.completions.create(
            model=DEBATE_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content


# ─── 主席 Chainlit 流式 ──────────────────────────

async def run_debate_stream(msg: cl.Message, topic_id: str) -> list:
    """
    完整辩论流程（罗伯特议事规则）：
    1. 加载原文内容
    2. 双教练输出 pre-strategy
    3. 8 轮逐轮辩论（每轮回应前一人，议事长+主席双控场）
    """
    t = TOPICS.get(topic_id, TOPICS["1"])
    book_content = load_topic_content(topic_id, t["title"])

    # ── 加载中提示 ──
    for ch in f"📖 **正在阅读原文...**\n\n":
        await msg.stream_token(ch)
        await asyncio.sleep(12 / 1000)

    # ── 梗概先过一遍 ──
    synopsis = await generate_synopsis(book_content, t["title"])
    for s_ch in f"📖 **原文梗概**:\n{synopsis}\n\n":
        await msg.stream_token(s_ch)
        await asyncio.sleep(8 / 1000)
    await asyncio.sleep(0.5)

    # ── 双教练并行 ──
    log.info("🏋️ 教练分析中...")
    pro_strat, con_strat = await asyncio.gather(
        DebateCoach.generate_pre_strategy(topic_id, book_content, "pro"),
        DebateCoach.generate_pre_strategy(topic_id, book_content, "con"),
    )
    log.info(f"✅ 教练策略完成: pro={len(pro_strat)}c con={len(con_strat)}c")

    # ── 辩论开始（议事长先发言） ──
    await msg.stream_token(f"🏛️ **议事长**: 本场辩论采用罗伯特议事规则。"
                           f"每轮发言后麦克风交还议事长，由议事长归纳后再传麦。\n\n")
    await asyncio.sleep(0.3)
    await msg.stream_token(f"🎙️ **辩论开始！**\n\n")
    await asyncio.sleep(0.5)

    history = ""
    last_role = ""
    last_text = ""
    prev_role = ""
    prev_text = ""
    round_idx = 0
    tts_tasks = []

    for role, stage in DEBATE_ROLES:
        round_idx += 1

        # ── 议事长归纳上一轮 ──
        if prev_role and prev_text and last_role and last_text:
            summary = await Chair.summarize(
                topic_id, last_role, last_text, prev_role, prev_text,
            )
            mc_line = f"\n\n🏛️ **议事长归纳**: {summary}\n"
            for mch in mc_line:
                await msg.stream_token(mch)
                await asyncio.sleep(6 / 1000)
            await asyncio.sleep(0.4)

        # 上轮发言变成 prev，准备接收新的 last
        if last_role:
            prev_role, prev_text = last_role, last_text

        # ── 主席传麦 ──
        side_color = "🔴" if "正方" in role else "🔵"
        mc_line = f"\n\n🎙️ **主席**: {side_color} 下面请 {role} 发言（{stage}）\n"
        for mch in mc_line:
            await msg.stream_token(mch)
            await asyncio.sleep(4 / 1000)

        # 八仙签诗
        sigil = SPEAKER_SIGILS.get(role, "")
        if sigil:
            for sch in sigil:
                await msg.stream_token(sch)
                await asyncio.sleep(SIGIL_SPEED_MS / 1000)
            await msg.stream_token("\n\n")
            await asyncio.sleep(0.2)

        # 生成该轮
        stream = await debate_round(
            topic_id, role, stage, book_content,
            pro_strat, con_strat, history,
        )

        # 流式输出 + 收集
        round_text = ""
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if not delta or not delta.content:
                continue
            round_text += delta.content
            for ch in delta.content:
                await msg.stream_token(ch)
                await asyncio.sleep(TYPE_SPEED_MS / 1000)

        # 更新历史
        history += f"\n\n【{role}】{round_text.strip()}"

        # 记录本轮为 last
        last_role, last_text = role, round_text.strip()

        # 停顿 + 后台 TTS
        if round_text.strip():
            await asyncio.sleep(0.4)
            if TTS_ENABLED:
                t = asyncio.ensure_future(
                    TTSEngine().generate(
                        re.sub(r"^【[^】]+】\s*", "", round_text).strip(),
                        role, round_idx,
                    )
                )
                tts_tasks.append(t)

    # ─ 议事长最终归纳 ─
    if last_role and last_text:
        final_summary = await Chair.summarize(
            topic_id, last_role, last_text, prev_role, prev_text,
        )
        await msg.stream_token(f"\n\n🏛️ **议事长总结**: {final_summary}")

    # ─ 结束 ─
    await msg.stream_token("\n\n---\n✅ **辩论结束**")
    await msg.send()

    # ─ TTS ─
    if tts_tasks:
        log.info(f"⏳ 等待 {len(tts_tasks)} 段 TTS...")
        results = await asyncio.gather(*tts_tasks)
        urls = [r for r in results if r]
        if urls:
            for start in range(0, len(urls), 3):
                batch = urls[start : start + 3]
                items = "\n\n".join(
                    f"[{start+i+1}] <audio controls src='{url}' "
                    f"style='width:70%;vertical-align:middle'></audio>"
                    for i, url in enumerate(batch)
                )
                await cl.Message(content=f"## 🎧 语音回放\n\n{items}").send()
        else:
            await cl.Message(content="ℹ️ 语音生成跳过").send()

    return urls if tts_tasks else []


# ─── Chainlit ─────────────────────────────────────

@cl.password_auth_callback
def auth_callback(username: str, password: str):
    pwd = os.getenv("APP_PASSWORD", "3131")
    if password == pwd:
        return cl.User(identifier=username)
    return None


@cl.on_chat_start
async def start():
    await cl.Message(
        content="""🦅 **鲲鹏志 · 内容驱动辩论会**

## 📋 辩题库
1️⃣ 白貂皮大衣：全球贸易铁证 vs 过度诠释
2️⃣ 木兰的哥哥：历史真相 vs 叙事虚构
3️⃣ 产权分割理论：安史之乱的经济学本质

每轮辩论前，AI 教练会先阅读原文 → 制定策略。
八位辩手逐轮对阵，必须回应前一人。

输入数字选择辩题！
"""
    ).send()


@cl.on_message
async def main(message: cl.Message):
    topic_id = message.content.strip()
    topic = TOPICS.get(topic_id)
    if not topic:
        await cl.Message(content="请选择 1、2 或 3").send()
        return

    title = topic["title"]
    msg = cl.Message(content=f"🎯 **辩题**: {title}\n\n")

    # Abstract 垫子
    if topic["abstract"]:
        for ch in f"📖 **背景**: {topic['abstract']}\n\n":
            await msg.stream_token(ch)
            await asyncio.sleep(8 / 1000)

    if TTS_ENABLED:
        for ch in "🔊 **语音模式已开启**\n\n":
            await msg.stream_token(ch)
            await asyncio.sleep(10 / 1000)

    log.info(f"🎯 辩题: {title}")
    await run_debate_stream(msg, topic_id)
    log.info(f"✅ 完成: {title}")


if __name__ == "__main__":
    print("鲲鹏志 v3.0 · chainlit run app.py")

"""
鲲鹏志 · AI 辩论系统 v2.3
====================================
4v4 大专辩论会 + 讲茶大堂 + R2 TTS 语音

主席控场 · 实时流式 · 回合停顿 · Abstract 垫子
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

# 打字速度  ms/字
TYPE_SPEED_MS = int(os.getenv("TYPE_SPEED_MS", "50"))


# ─── R2 ──────────────────────────────────────────

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
            if r.status_code == 200 and r.json().get("success"):
                return True
            log.error(f"R2 upload fail: {r.status_code}")
            return False

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
                url = R2Store.public_url(key)
                log.info(f"🔊 TTS: {tag}")
                return url
        except Exception as e:
            log.error(f"TTS fail {tag}: {e}")
        return None


# ─── 辩题库 ──────────────────────────────────────

TOPICS = {
    "1": {
        "title": "白貂皮大衣：全球贸易网络的铁证 vs 过度诠释",
        "abstract": (
            "北魏正光元年（520年），一件白貂皮大衣从波斯经嚈哒帝国"
            "辗转至北魏宫廷。这件奢侈品穿越了 4 个文明板块、"
            "2000 多公里商贸路线。它究竟见证了怎样的文明交往？"
        ),
    },
    "2": {
        "title": "木兰的哥哥：历史真相 vs 叙事虚构",
        "abstract": (
            "《木兰辞》中'阿爷无大儿，木兰无长兄'——是南朝文人为押韵"
            "做的文学加工，还是暗藏着兄长西征大同流亡军团的史实线索？"
        ),
    },
    "3": {
        "title": "产权分割理论：安史之乱的经济学本质",
        "abstract": (
            "公元 755 年安禄山起兵范阳。从产权经济学看，节度使制度"
            "制造的代理人困境，让这场叛乱本质成了'企业控制权争夺战'。"
        ),
    },
}

ROUND_LABELS = [
    "正方一辩 · 开篇立论",
    "反方一辩 · 开篇立论",
    "正方二辩 · 驳论",
    "反方二辩 · 驳论",
    "正方三辩 · 自由辩论",
    "反方三辩 · 自由辩论",
    "正方四辩 · 总结陈词",
    "反方四辩 · 总结陈词",
]


# ─── 辩论引擎 ────────────────────────────────────

def build_prompt(topic_id: str) -> str:
    t = TOPICS.get(topic_id, TOPICS["1"])
    rounds_list = "\n".join(f"【{l}】" for l in ROUND_LABELS)
    return f"""
你是一个 4v4 大专辩论会现场。请模拟完整辩论赛。

## 辩题
{t['title']}

## 格式
必须在每段发言前标注【角色】，严格按顺序：

{rounds_list}

## 规则
- 有火药味、有金句、有急智
- 后发言者必须针对前面发言回应
- 自由辩论至少 3 回合攻防
- 不许问要不要继续，直接把全场打完

现在请开始：
"""


def strip_speaker_prefix(text: str) -> str:
    """去掉开头的【角色】标记"""
    return re.sub(r"^【[^】]+】\s*", "", text).strip()


# ─── 主席 Chainlit 流式 ──────────────────────────

async def run_debate_stream(msg: cl.Message, topic_id: str) -> list:
    """
    实时流式辩论：
    - 从 API token 流中实时打出文字
    - 逐字符 state machine 识别【回合】切换
    - 切换时插入停顿 + 主席宣布
    - 后台异步生成 TTS 并上传 R2
    - 返回所有语音 URL
    """
    import openai
    client = openai.AsyncOpenAI(
        base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:4000/v1"),
        api_key=os.getenv("OPENAI_API_KEY", "sk-47318"),
    )

    prompt = build_prompt(topic_id)
    stream = await client.chat.completions.create(
        model=DEBATE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )

    # ─ 状态 ─
    round_text = ""          # 当前回合文本累积（用于 TTS）
    current_tag = ""         # 当前回合标签
    partial_tag = ""         # 检测中的【标签】
    in_tag = False           # 是否在【内部
    round_idx = 0
    tts_tasks: list = []

    # 主席开场
    for ch in "🎙️ **辩论开始！**\n\n":
        await msg.stream_token(ch)
        await asyncio.sleep(8 / 1000)
    await asyncio.sleep(0.5)

    async for chunk in stream:
        delta = chunk.choices[0].delta if chunk.choices else None
        if not delta or not delta.content:
            continue

        token = delta.content

        for ch in token:
            # ── state machine 检测回合切换 ──
            if ch == "【":
                # 遇到新【→ flush 上一回合
                if round_text.strip() and current_tag and TTS_ENABLED:
                    t = asyncio.ensure_future(
                        TTSEngine().generate(
                            strip_speaker_prefix(round_text),
                            current_tag,
                            round_idx,
                        )
                    )
                    tts_tasks.append(t)
                    round_idx += 1

                # 切换停顿
                if current_tag:
                    # 判断是否换方
                    is_new_side = (
                        "正方" in current_tag and "反方" in partial_tag.lower()
                    ) or (
                        "反方" in current_tag and "正方" in partial_tag.lower()
                    )
                    await asyncio.sleep(0.8 if is_new_side else 0.5)

                in_tag = True
                partial_tag = "【"
                continue

            if ch == "】" and in_tag:
                in_tag = False
                partial_tag += "】"
                current_tag = partial_tag[1:-1].strip()  # 去掉【】
                partial_tag = ""
                round_text = ""

                # 主席宣布
                annc = f"\n\n🎙️ **主席**: 有请 {current_tag}——\n\n"
                for ach in annc:
                    await msg.stream_token(ach)
                    await asyncio.sleep(6 / 1000)
                await asyncio.sleep(0.3)
                continue

            if in_tag:
                partial_tag += ch
                continue

            # ── 正常打字输出 ──
            await msg.stream_token(ch)
            await asyncio.sleep(TYPE_SPEED_MS / 1000)

            # 累积到当前回合
            if current_tag:
                round_text += ch

    # ─ 最后一回合 flush ─
    if round_text.strip() and current_tag and TTS_ENABLED:
        t = asyncio.ensure_future(
            TTSEngine().generate(
                strip_speaker_prefix(round_text),
                current_tag,
                round_idx,
            )
        )
        tts_tasks.append(t)

    # ─ 等 TTS ─
    if tts_tasks:
        log.info(f"⏳ 等待 {len(tts_tasks)} 段 TTS...")
        results = await asyncio.gather(*tts_tasks)
        urls = [r for r in results if r]
        log.info(f"✅ TTS 完成: {len(urls)} 段")
    else:
        urls = []

    return urls


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
        content="""🦅 **鲲鹏志 · 4v4 辩论会**

## 📋 辩题库
1️⃣ 白貂皮大衣：全球贸易铁证 vs 过度诠释
2️⃣ 木兰的哥哥：历史真相 vs 叙事虚构
3️⃣ 产权分割理论：安史之乱的经济学本质

## 🔤 自定义
直接输入你自己的辩题

## 🔊 语音自动生成
输入数字开始！
"""
    ).send()


@cl.on_message
async def main(message: cl.Message):
    topic_id = message.content.strip()
    topic = TOPICS.get(topic_id)

    if not topic:
        # ─ 自定义辩题 ─
        title = message.content
        msg = cl.Message(content=f"🎯 **辩题**: {title}\n\n")
        if TTS_ENABLED:
            await msg.stream_token("🔊 **语音模式已开启**\n\n")

        import openai
        client = openai.AsyncOpenAI(
            base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:4000/v1"),
            api_key=os.getenv("OPENAI_API_KEY", "sk-47318"),
        )
        stream = await client.chat.completions.create(
            model=DEBATE_MODEL,
            messages=[{"role": "user",
                       "content": f"4v4 辩论会，辩题：{title}，请模拟完整辩论。"}],
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                for ch in delta.content:
                    await msg.stream_token(ch)
                    await asyncio.sleep(TYPE_SPEED_MS / 1000)
        await msg.send()
        return

    # ─ 预设辩题 ─
    title = topic["title"]
    abstract = topic["abstract"]

    msg = cl.Message(content=f"🎯 **辩题**: {title}\n\n")

    # 1. Abstract 垫子（慢速呼吸灯）
    if abstract:
        for ch in f"📖 **背景**: {abstract}\n\n":
            await msg.stream_token(ch)
            await asyncio.sleep(8 / 1000)

    # 2. 语音提示
    if TTS_ENABLED:
        for ch in "🔊 **语音模式已开启**\n\n":
            await msg.stream_token(ch)
            await asyncio.sleep(12 / 1000)

    # 3. 实时辩论
    log.info(f"🎯 辩题: {title}")
    audio_urls = await run_debate_stream(msg, topic_id)

    # 4. 完成
    await msg.stream_token("\n\n---\n✅ **辩论结束**")
    await msg.send()

    # 5. 语音播放
    if audio_urls:
        # 每 3 个一组发送
        for start in range(0, len(audio_urls), 3):
            batch = audio_urls[start : start + 3]
            items = "\n\n".join(
                f"[{start+i+1}] <audio controls src='{url}' "
                f"style='width:70%;vertical-align:middle'></audio>"
                for i, url in enumerate(batch)
            )
            await cl.Message(content=f"## 🎧 语音回放\n\n{items}").send()
    else:
        await cl.Message(content="ℹ️ 未生成语音（TTS 跳过）").send()

    log.info(f"✅ 辩论完成: {title}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--teahouse":
        import openai
        fpath = sys.argv[2]
        if fpath and os.path.exists(fpath):
            with open(fpath) as f:
                debate_text = f.read()
            client = openai.AsyncOpenAI(
                base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:4000/v1"),
                api_key=os.getenv("OPENAI_API_KEY", "sk-47318"),
            )
            prompt = f"茶馆评论：\n{debate_text[:4000]}"
            resp = asyncio.run(client.chat.completions.create(
                model=DEBATE_MODEL,
                messages=[{"role": "user", "content": prompt}],
            ))
            print(resp.choices[0].message.content)
    else:
        print("鲲鹏志 v2.3 · chainlit run app.py")

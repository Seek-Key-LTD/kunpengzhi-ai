"""
鲲鹏志 · AI 辩论系统 v2.0
================================
4v4 大专辩论会 + 讲茶大堂 + 微软 TTS 语音

源于 Flow（4v4 辩论），高于 Flow（讲茶大堂 + 语音）
"""

import chainlit as cl
import os
import asyncio
import json
from typing import Optional
from dotenv import load_dotenv
import edge_tts

load_dotenv()

# ─── 配置 ─────────────────────────────────────────
DEBATE_MODEL = os.getenv("DEBATE_MODEL", "gemini-2.5-flash")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TTS_VOICE = os.getenv("TTS_VOICE", "zh-CN-YunxiNeural")  # 微软 TTS 中文男声
TTS_ENABLED = os.getenv("TTS_ENABLED", "true").lower() == "true"

# ─── 微软 TTS ─────────────────────────────────────

class TTSEngine:
    """微软 Edge TTS 引擎（免费，无需 API Key）"""

    VOICES = {
        "zh-CN-YunxiNeural": "云希（男声，活力）",
        "zh-CN-YunyangNeural": "云扬（男声，新闻）",
        "zh-CN-XiaoxiaoNeural": "晓晓（女声，温柔）",
        "zh-CN-XiaoyiNeural": "晓伊（女声，自然）",
        "zh-CN-YunjianNeural": "云剑（男声，成熟）",
        "zh-CN-YunxiaNeural": "云夏（男声，年轻）",
    }

    def __init__(self, voice: str = TTS_VOICE):
        self.voice = voice

    async def speak(self, text: str, filename: str = "tts_output.mp3") -> str:
        """生成 TTS 音频文件"""
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(filename)
        return filename


# ─── 辩论引擎 ─────────────────────────────────────

class DebateEngine:
    """4v4 辩论引擎"""

    TOPICS = {
        "1": {
            "title": "白貂皮大衣：全球贸易网络的铁证 vs 过度诠释",
            "pro": "白貂皮大衣是嚈哒帝国与东北亚保持联系的铁证，证明大同流亡军团理论",
            "con": "白貂皮大衣是转手贸易的结果，用来论证族群记忆是过度诠释",
        },
        "2": {
            "title": "木兰的哥哥：历史真相 vs 叙事虚构",
            "pro": "木兰无长兄的真正含义是长兄参加了大同流亡军团西征",
            "con": "木兰无长兄是文学修辞，强行关联嚈哒帝国是过度解读",
        },
        "3": {
            "title": "产权分割理论：安史之乱的经济学本质",
            "pro": "安史之乱=大股东收购母公司，产权理论是理解政治史的利器",
            "con": "用企业并购解释安史之乱是削足适履，忽略历史复杂性",
        },
    }

    @staticmethod
    def build_prompt(topic_id: str) -> str:
        """构建辩论 prompt"""
        topic = DebateEngine.TOPICS.get(topic_id, DebateEngine.TOPICS["1"])

        return f"""
你是一个 4v4 大专辩论会的现场。请模拟完整的辩论赛。

## 辩题
{topic['title']}

## 正方立场
{topic['pro']}

## 反方立场
{topic['con']}

## 角色与格式

【正方一辩】开篇立论（咄咄逼人、充满激情）
【反方一辩】开篇立论（冷静拆解、犀利毒舌）
【正方二辩】驳论（接招拆招）
【反方二辩】驳论（针锋相对）
【正方三辩】自由辩论（攻防至少3回合）
【反方三辩】自由辩论（攻防至少3回合）
【正方四辩】总结陈词（升华主题）
【反方四辩】总结陈词（致命一击）

## 规则
- 每个角色发言前标注角色名，用【】括起来
- 风格要像真正的大专辩论会，有火药味
- 正方可以引用白貂皮、词源学等证据
- 反方要质疑论据可靠性、指出逻辑漏洞
- 不许问要不要继续
"""


# ─── Chainlit 界面 ─────────────────────────────────

@cl.password_auth_callback
def auth_callback(username: str, password: str):
    """密码认证"""
    pwd = os.getenv("APP_PASSWORD", "3131")
    if password == pwd:
        return cl.User(identifier=username)
    return None


@cl.on_chat_start
async def start():
    """初始化"""
    await cl.Message(
        content="""🦅 **鲲鹏志 · 4v4 辩论会 + 讲茶大堂**

## 辩题库
1. 白貂皮大衣：全球贸易铁证 vs 过度诠释
2. 木兰的哥哥：历史真相 vs 叙事虚构  
3. 产权分割理论：安史之乱的经济学本质

## 自定义辩题
也可以输入你自己的辩题。

## 语音
每轮辩论会自动语音朗读 🔊
输入数字选择辩题，或直接输入你的辩题！
"""
    ).send()


@cl.on_message
async def main(message: cl.Message):
    """处理辩论请求"""
    topic_id = message.content.strip()
    topic = DebateEngine.TOPICS.get(topic_id)

    # 如果是自定义辩题
    if not topic:
        title = message.content
        prompt = f"""
你是一个 4v4 大专辩论会的现场。辩题是：{title}

请模拟完整的辩论赛，包括：
【正方一辩】开篇立论
【反方一辩】开篇立论
【正方二辩】驳论
【反方二辩】驳论
【正方三辩】自由辩论（攻防至少3回合）
【反方三辩】自由辩论（攻防至少3回合）
【正方四辩】总结陈词
【反方四辩】总结陈词

正方持支持立场，反方持反对立场。
风格要犀利，有火药味。
"""
    else:
        title = topic["title"]
        prompt = DebateEngine.build_prompt(topic_id)

    msg = cl.Message(content=f"🎯 **辩题**: {title}\n\n🎤 辩论即将开始...\n")

    if TTS_ENABLED:
        msg.content += "\n🔊 **语音模式已开启**\n"

    await msg.send()

    # 用 pi 运行辩论
    proc = await asyncio.create_subprocess_exec(
        "pi",
        "--model", f"google-vertex/{DEBATE_MODEL}",
        "--no-session", "-p", prompt,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    # 逐行读取输出
    current_speaker = ""
    speech_buffer = ""
    round_num = 0

    # TTS 引擎
    tts = TTSEngine()
    tts_tasks = []

    async def read_stream():
        nonlocal current_speaker, speech_buffer, round_num

        while True:
            line = await proc.stdout.readline()
            if not line:
                break

            text = line.decode("utf-8", errors="replace").strip()
            if not text:
                continue

            # 检测发言人切换
            if text.startswith("【"):
                # 先发送上一位发言人的内容
                if speech_buffer and current_speaker:
                    # 动画效果：逐字显示
                    display = f"\n\n**{current_speaker}**:\n{speech_buffer}"
                    await msg.stream_token(display)

                    # TTS：异步生成语音
                    if TTS_ENABLED and len(speech_buffer) > 10:
                        audio_file = f"/tmp/debate_{round_num}.mp3"
                        tts_tasks.append(
                            asyncio.create_task(
                                tts.speak(speech_buffer, audio_file)
                            )
                        )

                # 切换发言人
                current_speaker = text
                speech_buffer = ""
                round_num += 1

                # 显示发言人切换
                await msg.stream_token(f"\n\n--- *{current_speaker}* ---\n")

            else:
                speech_buffer += text + "\n"

        # 最后一位发言人
        if speech_buffer and current_speaker:
            display = f"\n\n**{current_speaker}**:\n{speech_buffer}"
            await msg.stream_token(display)

    await read_stream()
    await proc.wait()

    # 等待所有 TTS 任务完成
    if TTS_ENABLED and tts_tasks:
        await msg.stream_token("\n\n🔊 **语音生成中...**\n")
        await asyncio.gather(*tts_tasks, return_exceptions=True)
        await msg.stream_token("✅ **语音已就绪**\n")

    await msg.stream_token("\n\n---\n✅ **辩论结束** | 使用 `/audio` 查看语音文件")


# ─── 讲茶大堂入口（独立 CLI） ──────────────────

async def run_teahouse(debate_text: str):
    """
    讲茶大堂：对辩论进行场外评论
    可通过 CLI 独立调用：python app.py --teahouse <debate_file>
    """
    prompt = f"""
你是一个茶馆里的各路食客，正在观看刚才结束的一场辩论赛。

## 辩论实录（节选）
{debate_text[:4000]}

请模拟以下角色发表评论：

【茶博士】德高望重的老茶客，一针见血："正方最大的问题是……反方虽然犀利但忽略了……"
【店小二】消息灵通的跑堂："哎哟，我刚听说啊，那件白貂皮其实是……"
【神秘客】戴斗笠的独行客："你们都忽略了更关键的问题……"
【账房先生】拨算盘珠子："我算了一笔账，正方核心论据成功率……按赔率……"

每人至少一段，风格鲜活，像真的茶馆。
"""

    proc = await asyncio.create_subprocess_exec(
        "pi",
        "--model", f"google-vertex/{DEBATE_MODEL}",
        "--no-session", "-p", prompt,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    return stdout.decode("utf-8", errors="replace")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--teahouse":
        debate_file = sys.argv[2] if len(sys.argv) > 2 else None
        if debate_file and os.path.exists(debate_file):
            with open(debate_file) as f:
                debate_text = f.read()
            result = asyncio.run(run_teahouse(debate_text))
            print(result)
        else:
            print("Usage: python app.py --teahouse <debate_file.md>")
    else:
        print("鲲鹏志 · AI 辩论系统 v2.0")
        print("运行方式: chainlit run app.py")
        print("独立模式: python app.py --teahouse <debate_file.md>")

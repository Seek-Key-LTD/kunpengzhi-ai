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

# ─── 内存日志缓存（监控与诊断） ──────────────────────
class LogBufferHandler(logging.Handler):
    def __init__(self, capacity=200):
        super().__init__()
        self.capacity = capacity
        self.buffer = []

    def emit(self, record):
        try:
            msg = self.format(record)
            self.buffer.append(msg)
            if len(self.buffer) > self.capacity:
                self.buffer.pop(0)
        except Exception:
            self.handleError(record)

log_buffer_handler = LogBufferHandler()
log_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log_buffer_handler.setFormatter(log_formatter)
log.addHandler(log_buffer_handler)
logging.getLogger().addHandler(log_buffer_handler)


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

# 全局八卦看板状态
DEBATE_STATE = {
    "topic_title": "等待选择辩题开始辩论...",
    "current_round": 0,
    "active_role": "",
    "book_content": "",
    "past_debates": "",
    "rounds": {
        role: {
            "status": "pending",
            "speech": "",
            "whisper": ""
        } for role, _ in DEBATE_ROLES
    }
}


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
        try:
            resp = await client.chat.completions.create(model=DEBATE_MODEL,
                messages=[{"role": "user", "content": prompt}], timeout=60.0)
            return resp.choices[0].message.content
        except Exception as e:
            log.error(f"generate_pre_strategy failed: {e}")
            raise e

    @staticmethod
    async def generate_whisper(
        topic_id: str,
        role: str,
        book_content: str,
        coach_strategy: str,
        history: str,
    ) -> str:
        """
        教练针对当前局势，给当前辩手（学生）发送实时耳语指导（teacher model 实时交互）
        """
        t = TOPICS.get(topic_id, TOPICS["1"])
        prompt = f"""
你是一名资深辩论教练（Teacher Model）。你正在实时指导你的辩手：【{role}】。
当前辩题：{t['title']}
当前大局策略：
{coach_strategy[:1000]}

当前辩论历史：
{history[-1500:] if history else "辩论刚刚开始，准备第一轮发言。"}

任务：
请给【{role}】发一条简短、犀利的耳语指导（80字以内），告诉他/她本轮应该抓住对方什么漏洞、引用原文什么证据，或者采取什么战术。
注意：直接输出耳语内容，语气要像教练在台下悄悄给队员叮嘱，不要任何多余的格式或客套话。
耳语："""
        import openai
        client = openai.AsyncOpenAI(base_url=os.getenv("OPENAI_BASE_URL"), api_key=os.getenv("OPENAI_API_KEY"))
        try:
            resp = await client.chat.completions.create(
                model=DEBATE_MODEL,
                messages=[{"role": "user", "content": prompt}],
                timeout=12,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            log.warning(f"Whisper generation fail: {e}")
            return "教练正在观察局势，准备下一轮指导。"


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
        model=DEBATE_MODEL, messages=[{"role": "user", "content": prompt}], stream=True, timeout=30.0)


# ─── 议事长 ──────────────────────────────────────

class Chair:
    @staticmethod
    async def summarize(topic_id: str, last_role: str, last_text: str,
                        prev_role: str, prev_text: str) -> str:
        t = TOPICS.get(topic_id, TOPICS["1"])
        prompt = f"辩论归纳：\n辩题：{t['title']}\n上轮：{prev_role}说{prev_text[:500]}\n本轮：{last_role}说{last_text[:500]}\n\n用80字归纳交锋焦点。"
        import openai
        client = openai.AsyncOpenAI(base_url=os.getenv("OPENAI_BASE_URL"), api_key=os.getenv("OPENAI_API_KEY"))
        try:
            resp = await client.chat.completions.create(model=DEBATE_MODEL,
                messages=[{"role": "user", "content": prompt}], timeout=15.0)
            return resp.choices[0].message.content.strip()
        except Exception as e:
            log.warning(f"Chair summary fail: {e}")
            return f"双方针对辩题展开激烈交锋，【{last_role}】直接反驳了【{prev_role}】的立场。"


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

class RoundState:
    def __init__(self, role: str, stage: str):
        self.role = role
        self.stage = stage
        self.whisper_future = asyncio.Future()
        self.speech_future = asyncio.Future()
        self.chair_summary_future = asyncio.Future()

async def debate_generation_pipeline(rounds, topic_id, book_content, pro_strat, con_strat, past_debates, tts_tasks, tmp_paths):
    history = ""
    last_role, last_text = "", ""
    prev_role, prev_text = "", ""
    
    for idx, r in enumerate(rounds):
        # 1. 后台并发启动教练耳语生成
        async def run_whisper(r_state, hist):
            try:
                res = await DebateCoach.generate_whisper(
                    topic_id, r_state.role, book_content,
                    pro_strat if "正方" in r_state.role else con_strat,
                    hist
                )
                r_state.whisper_future.set_result(res)
            except Exception as e:
                log.error(f"Error generating whisper in pipeline: {e}")
                r_state.whisper_future.set_result("教练正在观察局势，准备下一轮指导。")
        asyncio.create_task(run_whisper(r, history))
        
        # 2. 后台并发启动议事长总结生成（非首轮）
        if idx > 0:
            async def run_chair(r_state, l_role, l_text, p_role, p_text):
                try:
                    res = await Chair.summarize(topic_id, l_role, l_text, p_role, p_text)
                    r_state.chair_summary_future.set_result(res)
                except Exception as e:
                    log.error(f"Error generating chair summary in pipeline: {e}")
                    r_state.chair_summary_future.set_result("双方交锋激烈，各抒己见。")
            asyncio.create_task(run_chair(r, last_role, last_text, prev_role, prev_text))
        else:
            r.chair_summary_future.set_result("")
            
        # 3. 后台生成当前辩手发言（这是最长路径/关键路径！）
        try:
            stream = await debate_round(topic_id, r.role, r.stage, book_content, pro_strat, con_strat, history)
            speech_text = ""
            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    speech_text += delta.content
            r.speech_future.set_result(speech_text)
        except Exception as e:
            log.error(f"Error generating speech in pipeline: {e}")
            r.speech_future.set_result(f"【{r.role}】因网络原因暂时无法发言。")
            speech_text = ""
            
        # 4. 一旦当前发言生成完毕，立刻在后台并发启动语音 TTS 生成与上传，无需等待前台打字机结束！
        if speech_text.strip():
            if TTS_ENABLED:
                t = asyncio.ensure_future(
                    TTSEngine().generate(
                        re.sub(r"^【[^】]+】\s*", "", speech_text).strip(),
                        r.role, idx + 1, tmp_paths
                    )
                )
                tts_tasks.append(t)
                
        # 5. 更新上下文历史
        if last_role:
            prev_role, prev_text = last_role, last_text
        last_role, last_text = r.role, speech_text
        history += f"\n\n【r.role】{speech_text.strip()}"
        
    # 生成最终总结
    final_summary_future = asyncio.Future()
    async def run_final_chair(l_role, l_text, p_role, p_text):
        try:
            res = await Chair.summarize(topic_id, l_role, l_text, p_role, p_text)
            final_summary_future.set_result(res)
        except Exception as e:
            final_summary_future.set_result("辩论精彩落幕。")
    asyncio.create_task(run_final_chair(last_role, last_text, prev_role, prev_text))
    return final_summary_future, history

def parse_markdown(text: str) -> str:
    if not text:
        return ""
    # 1. Bold: **text** -> <strong>text</strong>
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    # 2. Italic: *text* -> <em>text</em>
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    # 3. Inline code: `code` -> <code>code</code>
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
    
    # 4. Headers
    text = re.sub(r'^### (.*?)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.*?)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    
    # 5. Paragraphs and Lists
    paragraphs = text.strip().split('\n\n')
    parsed_paragraphs = []
    for para in paragraphs:
        lines = para.split('\n')
        list_items = []
        is_list = True
        for line in lines:
            line_str = line.strip()
            if line_str.startswith('- ') or line_str.startswith('* '):
                list_items.append(f"<li>{line_str[2:]}</li>")
            elif line_str.startswith('1. ') or line_str.startswith('2. ') or line_str.startswith('3. ') or line_str.startswith('4. '):
                idx = line_str.find(' ')
                list_items.append(f"<li>{line_str[idx+1:]}</li>")
            else:
                is_list = False
                break
        
        if is_list and list_items:
            if lines[0].strip().startswith(('- ', '* ')):
                parsed_paragraphs.append(f"<ul>{''.join(list_items)}</ul>")
            else:
                parsed_paragraphs.append(f"<ol>{''.join(list_items)}</ol>")
        else:
            para_html = para.replace('\n', '<br/>')
            parsed_paragraphs.append(f"<p>{para_html}</p>")
            
    return "".join(parsed_paragraphs)

def make_debate_html(
    role: str,
    stage: str,
    moderator_intro: str,
    poem: str,
    speech_text: str,
    pro_whisper: Optional[str],
    con_whisper: Optional[str],
    is_pro: bool,
) -> str:
    side_class = "pro-side" if is_pro else "con-side"
    left_active_class = "active" if is_pro else ""
    right_active_class = "active" if not is_pro else ""

    if is_pro:
        if pro_whisper:
            left_whisper_html = f"<div>{parse_markdown(pro_whisper)}</div>"
        else:
            left_whisper_html = '<div class="whisper-placeholder">教练正在拟定耳语战术...</div>'
    else:
        left_whisper_html = '<div class="whisper-placeholder">教练正在观察局势...</div>'

    if not is_pro:
        if con_whisper:
            right_whisper_html = f"<div>{parse_markdown(con_whisper)}</div>"
        else:
            right_whisper_html = '<div class="whisper-placeholder">教练正在拟定耳语战术...</div>'
    else:
        right_whisper_html = '<div class="whisper-placeholder">教练正在观察局势...</div>'

    speech_html = ""
    if moderator_intro:
        speech_html += f'<div class="moderator-intro" style="margin-bottom: 12px; font-weight: 500; opacity: 0.85;">{moderator_intro}</div>'
    if poem:
        poem_formatted = poem.replace("\n", "<br/>")
        speech_html += f'<div class="speaker-poem" style="margin-bottom: 16px; font-style: italic; color: #7f8c8d; line-height: 1.6;">{poem_formatted}</div>'
    if speech_text:
        speech_formatted = parse_markdown(speech_text)
        speech_html += f'<div class="speaker-speech" style="line-height: 1.7; font-size: 1.05em;">{speech_formatted}</div>'

    html = f"""
<div class="debate-row">
  <div class="whisper-bar left-bar {left_active_class}">
    <div class="whisper-title">🔴 正方教练耳语</div>
    {left_whisper_html}
  </div>

  <div class="speech-content {side_class}">
    <div style="font-weight: bold; font-size: 1.1em; margin-bottom: 10px; border-bottom: 1px solid var(--row-border); padding-bottom: 6px;">
      {role} ({stage})
    </div>
    {speech_html}
  </div>

  <div class="whisper-bar right-bar {right_active_class}">
    <div class="whisper-title">🔵 反方教练耳语</div>
    {right_whisper_html}
  </div>
</div>
"""
    return html

async def type_text_in_html_from_string(
    role: str,
    stage: str,
    full_intro: str,
    full_poem: str,
    speech_future: asyncio.Future,
    whisper_future: asyncio.Future,
    is_pro: bool,
    round_msg: cl.Message,
) -> str:
    global DEBATE_STATE
    DEBATE_STATE["active_role"] = role
    DEBATE_STATE["rounds"][role]["status"] = "active"
    DEBATE_STATE["rounds"][role]["speech"] = ""
    DEBATE_STATE["rounds"][role]["whisper"] = ""

    intro_curr = ""
    poem_curr = ""
    speech_curr = ""
    
    def get_whisper_val():
        if whisper_future.done():
            try:
                val = whisper_future.result()
                DEBATE_STATE["rounds"][role]["whisper"] = val
                return val
            except Exception:
                return "教练正在观察局势，准备下一轮指导。"
        return None

    # 1. 打印主持传麦
    if full_intro:
        chunk_size = 2
        for i in range(0, len(full_intro), chunk_size):
            intro_curr += full_intro[i:i+chunk_size]
            w_val = get_whisper_val()
            pro_w = w_val if is_pro else None
            con_w = w_val if not is_pro else None
            
            round_msg.content = make_debate_html(
                role=role, stage=stage,
                moderator_intro=intro_curr, poem=poem_curr, speech_text=speech_curr,
                pro_whisper=pro_w, con_whisper=con_w, is_pro=is_pro
            )
            DEBATE_STATE["rounds"][role]["speech"] = speech_curr
            await round_msg.update()
            await asyncio.sleep((5 / 1000) * chunk_size)
            
    # 2. 打印定场诗
    if full_poem:
        for ch in full_poem:
            poem_curr += ch
            w_val = get_whisper_val()
            pro_w = w_val if is_pro else None
            con_w = w_val if not is_pro else None
            
            round_msg.content = make_debate_html(
                role=role, stage=stage,
                moderator_intro=intro_curr, poem=poem_curr, speech_text=speech_curr,
                pro_whisper=pro_w, con_whisper=con_w, is_pro=is_pro
            )
            DEBATE_STATE["rounds"][role]["speech"] = speech_curr
            await round_msg.update()
            await asyncio.sleep(POEM_SPEED_MS / 1000)
            
    # 3. 等待大语言模型生成完毕（若早已生成好则秒解），然后以打字机流式渲染
    speech_text = await speech_future
    
    chunk_size = 3
    for i in range(0, len(speech_text), chunk_size):
        speech_curr += speech_text[i:i+chunk_size]
        w_val = get_whisper_val()
        pro_w = w_val if is_pro else None
        con_w = w_val if not is_pro else None
        
        round_msg.content = make_debate_html(
            role=role, stage=stage,
            moderator_intro=intro_curr, poem=poem_curr, speech_text=speech_curr,
            pro_whisper=pro_w, con_whisper=con_w, is_pro=is_pro
        )
        DEBATE_STATE["rounds"][role]["speech"] = speech_curr
        await round_msg.update()
        await asyncio.sleep(TYPE_SPEED_MS / 1000 * chunk_size)
        
    # 最终确保教练耳语已加载
    w_val = await whisper_future
    pro_w = w_val if is_pro else None
    con_w = w_val if not is_pro else None
    
    DEBATE_STATE["rounds"][role]["whisper"] = w_val
    DEBATE_STATE["rounds"][role]["speech"] = speech_text
    DEBATE_STATE["rounds"][role]["status"] = "completed"
    
    round_msg.content = make_debate_html(
        role=role, stage=stage,
        moderator_intro=intro_curr, poem=poem_curr, speech_text=speech_curr,
        pro_whisper=pro_w, con_whisper=con_w, is_pro=is_pro
    )
    await round_msg.update()
    
    return speech_text

async def run_debate_stream(msg: cl.Message, topic_id: str) -> list:
    global DEBATE_STATE
    t = TOPICS.get(topic_id, TOPICS["1"])
    
    # 重置全局状态
    DEBATE_STATE["topic_title"] = t["title"]
    DEBATE_STATE["current_round"] = 0
    DEBATE_STATE["active_role"] = ""
    DEBATE_STATE["book_content"] = ""
    DEBATE_STATE["past_debates"] = ""
    DEBATE_STATE["rounds"] = {
        role: {
            "status": "pending",
            "speech": "",
            "whisper": ""
        } for role, _ in DEBATE_ROLES
    }

    # 1. 并行加载原文与检索历史辩论数据（优化网络延迟）
    log.info("🔍 并行加载原文与检索历史辩论...")
    chapters_future = BookRetriever.load_relevant_chapters(topic_id)
    vectorize_future = vectorize_query(t["title"], top_k=5)
    
    chapters_data, debate_matches = await asyncio.gather(chapters_future, vectorize_future, return_exceptions=True)
    
    # 提取原文内容
    book_content = ""
    if not isinstance(chapters_data, Exception) and chapters_data:
        book_content = BookRetriever.extract_relevant(chapters_data)
        
    # 提取历史辩论
    past_debates = ""
    if not isinstance(debate_matches, Exception) and debate_matches:
        past_lines = []
        for m in debate_matches:
            if m.get("source", "").startswith("辩论实录"):
                past_lines.append(f"- **{m['source'].replace('辩论实录/', '').replace('_', ' ')}** (相似度: {m['score']:.3f})\n  {m.get('text', '')[:300]}")
        if past_lines:
            past_debates = "\n".join(past_lines)
            log.info(f"📊 Moneyball: 找到 {len(past_lines)} 条历史辩论")

    # 写入全局状态
    DEBATE_STATE["book_content"] = book_content
    DEBATE_STATE["past_debates"] = past_debates

    # 2. 【关键优化】立即启动后台生成教练策略（LLM 耗时最长，与前台渲染原文进行并发）
    log.info("🏋️ [运筹学并发] 后台启动双教练赛前策略生成任务...")
    coach_task = asyncio.gather(
        DebateCoach.generate_pre_strategy(topic_id, book_content, "pro", past_debates),
        DebateCoach.generate_pre_strategy(topic_id, book_content, "con", past_debates),
    )

    # 3. 前台并发渲染原文检索结果（打字机流式展示，不占用 LLM 等待时间）
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

    await msg.send() # 结束第一个 message

    await cl.Message(content="**[进度: 1/4] 原文检索完成，教练正在研读并制定策略...**\n").send()

    # ── 阶段 2/4: 等待后台教练策略任务结束 ──
    try:
        pro_strat, con_strat = await coach_task
        log.info(f"✅ 策略完成: pro={len(pro_strat)}c con={len(con_strat)}c")
    except Exception as e:
        error_msg = f"❌ **大模型调用失败 (双教练策略生成错误)**: {str(e)}\n\n" \
                    f"**当前 API 配置**:\n" \
                    f"- `DEBATE_MODEL`: `{DEBATE_MODEL}`\n" \
                    f"- `OPENAI_BASE_URL`: `{os.getenv('OPENAI_BASE_URL', 'http://localhost:4000/v1')}`\n" \
                    f"- `OPENAI_API_KEY`: `{'已设置' if os.getenv('OPENAI_API_KEY') else '未设置'}`\n\n" \
                    f"请检查 Heroku Config Vars 中的环境变量是否配置正确，或服务是否正常！"
        await cl.Message(content=error_msg).send()
        log.error(f"Coach strategy generation failed: {e}", exc_info=True)
        return []

    # 存储完整策略到 user_session
    cl.user_session.set("pro_strat", pro_strat)
    cl.user_session.set("con_strat", con_strat)
    cl.user_session.set("topic_title", t["title"])

    # 显示教练策略摘要 + 查看按钮
    actions = [
        cl.Action(name="show_coach_briefing", value="show_briefing", label="📊 查看教练策略", payload={"value": "show_briefing"})
    ]
    await cl.Message(content="**[进度: 2/4] 教练策略已部署，辩论即将开始...**", actions=actions).send()

    # ── 阶段 3/4: 辩论进行中 ──
    # 初始化后台流水线状态
    rounds_state = [RoundState(role, stage) for role, stage in DEBATE_ROLES]
    
    tts_tasks = []
    tmp_paths = []

    # 启动后台大模型并发生成流水线 (WBS/运筹学关键路径并行)
    pipeline_task = asyncio.create_task(
        debate_generation_pipeline(
            rounds_state, topic_id, book_content, pro_strat, con_strat, past_debates, tts_tasks, tmp_paths
        )
    )

    welcome_msg = cl.Message(content="🏛️ **议事长**: 欢迎来到鲲鹏志辩论现场！本场辩论采用罗伯特议事规则。\n"
                                     "每轮发言后麦克风交还议事长，由议事长归纳交锋，确保辩论焦点清晰。\n"
                                     "双方辩手将围绕辩题展开激烈交锋，并引用《鲲鹏志》书库原文。\n\n")
    await welcome_msg.send()
    await asyncio.sleep(INTRO_SPEED_MS / 1000 * 30) # 模拟更慢的开场白

    for idx, r in enumerate(rounds_state):
        round_idx = idx + 1
        total_stages = len(DEBATE_ROLES) + 1

        # 更新全局状态中的当前轮次，并标记之前的辩手为 completed
        DEBATE_STATE["current_round"] = round_idx
        for prev_idx in range(idx):
            prev_role = DEBATE_ROLES[prev_idx][0]
            DEBATE_STATE["rounds"][prev_role]["status"] = "completed"

        # 1. 议事长归纳（非首轮，等待后台生成完毕并显示）
        if round_idx > 1:
            summary = await r.chair_summary_future
            summary_msg = cl.Message(content="")
            await summary_msg.send()
            summary_content = ""
            for ch in f"🏛️ **议事长**: {summary}":
                summary_content += ch
                summary_msg.content = summary_content
                await summary_msg.update()
                await asyncio.sleep(6 / 1000)
            await asyncio.sleep(0.5)

        # 2. 创建本轮 HTML 消息并发送
        round_msg = cl.Message(content="")
        await round_msg.send()

        # 3. 主席传麦文案
        side_color = "🔴" if "正方" in r.role else "🔵"
        moderator_intro = f"🎙️ **主席**: **[进度: {round_idx}/{total_stages}]** {side_color} 有请 {r.role}（{r.stage}）——"
        poem = SPEAKER_POEMS.get(r.role, "")

        # 4. 打印主席、定场诗，并流式播放已预取生成的发言
        await type_text_in_html_from_string(
            role=r.role,
            stage=r.stage,
            full_intro=moderator_intro,
            full_poem=poem,
            speech_future=r.speech_future,
            whisper_future=r.whisper_future,
            is_pro="正方" in r.role,
            round_msg=round_msg,
        )

    # 等待后台流水线任务结束，并拿到最终的总结与 history
    final_summary_future, history = await pipeline_task

    # 议事长最终总结
    final_summary = await final_summary_future
    DEBATE_STATE["current_round"] = 9
    for role, _ in DEBATE_ROLES:
        DEBATE_STATE["rounds"][role]["status"] = "completed"

    final_msg = cl.Message(content="")
    await final_msg.send()
    final_content = ""
    for ch in f"🏛️ **议事长总结**: {final_summary}":
        final_content += ch
        final_msg.content = final_content
        await final_msg.update()
        await asyncio.sleep(6 / 1000)

    end_msg = cl.Message(content="✅ **辩论结束**")
    await end_msg.send()

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

[自动运行模式]: 系统已默认选择 1️⃣ 白貂皮大衣 并自动启动辩论赛，请在两侧终端/看板凝望数据。
"""
    ).send()
    
    # 模拟用户输入 "1" 开始辩论
    msg = cl.Message(content="1")
    asyncio.create_task(main(msg))

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

from chainlit.server import app

@app.get("/status")
async def get_system_status():
    llm_error = None
    llm_ok = False
    try:
        import openai
        client = openai.AsyncOpenAI(
            base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:4000/v1"),
            api_key=os.getenv("OPENAI_API_KEY", "sk-47318")
        )
        resp = await client.chat.completions.create(
            model=DEBATE_MODEL,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5,
            timeout=5.0
        )
        if resp.choices:
            llm_ok = True
    except Exception as e:
        llm_error = str(e)

    raw_key = os.getenv("OPENAI_API_KEY", "")
    masked_key = "Not Set"
    if raw_key:
        masked_key = raw_key[:4] + "..." + raw_key[-4:] if len(raw_key) > 8 else "***"

    return {
        "status": "healthy" if llm_ok else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "config": {
            "DEBATE_MODEL": DEBATE_MODEL,
            "OPENAI_BASE_URL": os.getenv("OPENAI_BASE_URL", "http://localhost:4000/v1"),
            "OPENAI_API_KEY": masked_key,
            "TTS_ENABLED": TTS_ENABLED,
            "TTS_VOICE": TTS_VOICE,
        },
        "llm_check": {
            "success": llm_ok,
            "error": llm_error
        },
        "logs": log_buffer_handler.buffer
    }

# 将 /status, /bagua, /bagua/api 路由移动到 FastAPI 路由表的最前列，绕过 Chainlit 自带的单页应用 (SPA) 兜底通配符
from fastapi.responses import HTMLResponse

HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>鲲鹏志 · 八卦乾坤辩论看板</title>
    <meta name="description" content="鲲鹏志内容驱动辩论系统的实时八卦流可视化看板。">
    <link href="https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&family=Outfit:wght@300;400;600;700&family=Noto+Sans+SC:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0b0f19;
            --card-bg: rgba(17, 24, 39, 0.7);
            --border-color: rgba(255, 255, 255, 0.08);
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --color-pro: #ef4444;
            --color-con: #3b82f6;
            --color-pro-glow: rgba(239, 68, 68, 0.5);
            --color-con-glow: rgba(59, 130, 246, 0.5);
            --color-active: #fbbf24;
            --color-active-glow: rgba(251, 191, 36, 0.6);
            --color-completed: #10b981;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Noto Sans SC', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
            background-image: 
                radial-gradient(at 0% 0%, rgba(31, 41, 55, 0.3) 0, transparent 50%),
                radial-gradient(at 50% 0%, rgba(17, 24, 39, 0.5) 0, transparent 50%),
                radial-gradient(at 100% 0%, rgba(31, 41, 55, 0.3) 0, transparent 50%);
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1.5rem 2rem;
            border-bottom: 1px solid var(--border-color);
            background: rgba(11, 15, 25, 0.8);
            backdrop-filter: blur(8px);
            z-index: 10;
        }

        .logo-section h1 {
            font-family: 'Ma Shan Zheng', cursive;
            font-size: 2.2rem;
            background: linear-gradient(135deg, #fbbf24, #ef4444);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: 2px;
        }

        .logo-section p {
            font-family: 'Outfit', sans-serif;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 4px;
            color: var(--text-secondary);
            margin-top: 0.2rem;
        }

        .status-badge {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.85rem;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: var(--text-secondary);
        }

        .status-dot.active {
            background-color: var(--color-active);
            box-shadow: 0 0 10px var(--color-active);
            animation: pulse 1.5s infinite;
        }

        .status-dot.completed {
            background-color: var(--color-completed);
            box-shadow: 0 0 8px var(--color-completed);
        }

        @keyframes pulse {
            0% { transform: scale(0.9); opacity: 0.6; }
            50% { transform: scale(1.2); opacity: 1; }
            100% { transform: scale(0.9); opacity: 0.6; }
        }

        .main-container {
            display: flex;
            flex: 1;
            width: 100%;
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
            gap: 2rem;
        }

        @media (max-width: 1100px) {
            .main-container {
                flex-direction: column;
                align-items: center;
            }
        }

        .canvas-card {
            flex: 1.2;
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
            padding: 2rem;
            min-height: 600px;
            backdrop-filter: blur(12px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        }

        .svg-container {
            width: 100%;
            max-width: 580px;
            height: auto;
            aspect-ratio: 1 / 1;
        }

        .info-sidebar {
            flex: 0.8;
            width: 100%;
            max-width: 460px;
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }

        .glass-panel {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 1.5rem;
            backdrop-filter: blur(12px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
            display: flex;
            flex-direction: column;
        }

        .topic-panel h2 {
            font-size: 1.2rem;
            color: #fbbf24;
            margin-bottom: 0.5rem;
            border-left: 4px solid #fbbf24;
            padding-left: 0.6rem;
            line-height: 1.2;
        }

        .topic-panel p {
            font-size: 0.9rem;
            color: var(--text-secondary);
        }

        .debater-card {
            flex: 1;
        }

        .trigram-avatar {
            width: 60px;
            height: 60px;
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-color);
            display: flex;
            justify-content: center;
            align-items: center;
            font-family: 'Ma Shan Zheng', cursive;
            font-size: 2.2rem;
            color: var(--text-primary);
            transition: all 0.3s;
        }

        .debater-title h3 {
            font-size: 1.15rem;
            font-weight: 600;
        }

        .debater-title p {
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-top: 0.15rem;
        }

        .poem-box {
            font-family: 'Noto Sans SC', sans-serif;
            font-style: italic;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 8px;
            padding: 0.8rem 1rem;
            margin-bottom: 1rem;
            font-size: 0.9rem;
            line-height: 1.6;
            color: #fbbf24;
            border-left: 2px solid rgba(251, 191, 36, 0.4);
            white-space: pre-line;
        }

        .speech-box {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
            padding: 1rem;
            font-size: 0.95rem;
            line-height: 1.6;
            min-height: 120px;
            max-height: 250px;
            overflow-y: auto;
            border: 1px solid rgba(255, 255, 255, 0.03);
            margin-bottom: 1rem;
        }

        .speech-box::-webkit-scrollbar {
            width: 6px;
        }
        .speech-box::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 3px;
        }

        .whisper-box {
            border: 1px dashed var(--color-active);
            background: rgba(251, 191, 36, 0.04);
            color: #fbbf24;
            border-radius: 8px;
            padding: 1.2rem 1rem 1rem 1rem;
            font-size: 0.88rem;
            line-height: 1.5;
            position: relative;
        }

        .whisper-box::before {
            content: "👂 教练耳语指导";
            position: absolute;
            top: -10px;
            left: 12px;
            background: #0f172a;
            padding: 0 6px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .grid-circle {
            fill: none;
            stroke: rgba(255, 255, 255, 0.03);
            stroke-width: 1;
        }

        .grid-line {
            fill: none;
            stroke: rgba(255, 255, 255, 0.015);
            stroke-width: 1;
        }

        .taiji-group {
            cursor: pointer;
            filter: drop-shadow(0 0 15px rgba(255, 255, 255, 0.15));
        }

        .taiji-rotate {
            animation: taiji-spin 30s linear infinite;
            transform-origin: 300px 300px;
        }

        @keyframes taiji-spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        .debate-path {
            fill: none;
            stroke: rgba(255, 255, 255, 0.04);
            stroke-width: 2;
            stroke-dasharray: 4 4;
            transition: all 0.5s ease;
        }

        .debate-path.completed {
            stroke-dasharray: none;
            stroke-width: 2.5;
            filter: drop-shadow(0 0 3px rgba(255, 255, 255, 0.2));
        }

        .debate-path.active {
            stroke-width: 3.5;
            stroke-dasharray: 8 4;
            animation: dash 1s linear infinite;
        }

        .debate-path.pro-path {
            stroke: rgba(239, 68, 68, 0.2);
        }
        .debate-path.pro-path.completed {
            stroke: var(--color-pro);
            filter: drop-shadow(0 0 4px rgba(239, 68, 68, 0.4));
        }
        .debate-path.pro-path.active {
            stroke: var(--color-pro);
            filter: drop-shadow(0 0 6px rgba(239, 68, 68, 0.6));
        }

        .debate-path.con-path {
            stroke: rgba(59, 130, 246, 0.2);
        }
        .debate-path.con-path.completed {
            stroke: var(--color-con);
            filter: drop-shadow(0 0 4px rgba(59, 130, 246, 0.4));
        }
        .debate-path.con-path.active {
            stroke: var(--color-con);
            filter: drop-shadow(0 0 6px rgba(59, 130, 246, 0.6));
        }

        @keyframes dash {
            to {
                stroke-dashoffset: -20;
            }
        }

        .node-group {
            cursor: pointer;
            transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }

        .node-group:hover {
            transform: scale(1.08);
        }

        .node-ring {
            transition: all 0.5s ease;
        }

        .node-group.pro .node-ring {
            stroke: rgba(239, 68, 68, 0.3);
            fill: #0c0e15;
        }
        .node-group.pro.completed .node-ring {
            stroke: var(--color-pro);
            fill: rgba(239, 68, 68, 0.08);
            filter: drop-shadow(0 0 6px var(--color-pro-glow));
        }

        .node-group.con .node-ring {
            stroke: rgba(59, 130, 246, 0.3);
            fill: #0c0e15;
        }
        .node-group.con.completed .node-ring {
            stroke: var(--color-con);
            fill: rgba(59, 130, 246, 0.08);
            filter: drop-shadow(0 0 6px var(--color-con-glow));
        }

        .node-group.active {
            transform: scale(1.08);
        }

        .node-group.active .node-ring {
            stroke: var(--color-active) !important;
            stroke-width: 3px;
            fill: rgba(251, 191, 36, 0.12) !important;
            filter: drop-shadow(0 0 10px var(--color-active-glow)) !important;
        }

        .pulsate-circle {
            animation: pulse-ring 2s cubic-bezier(0.215, 0.610, 0.355, 1) infinite;
            transform-origin: center;
        }

        @keyframes pulse-ring {
            0% { transform: scale(0.95); opacity: 0.8; }
            50% { transform: scale(1.15); opacity: 0.3; }
            100% { transform: scale(1.25); opacity: 0; }
        }

        .node-trigram {
            font-family: 'Ma Shan Zheng', cursive;
            fill: var(--text-primary);
            text-anchor: middle;
            dominant-baseline: middle;
            font-size: 26px;
        }

        .node-label {
            font-size: 11px;
            fill: var(--text-secondary);
            text-anchor: middle;
        }

        .node-character {
            font-size: 11px;
            font-weight: 500;
            text-anchor: middle;
        }

        .pro-text {
            fill: #fca5a5;
        }

        .con-text {
            fill: #93c5fd;
        }

        footer {
            text-align: center;
            padding: 1.5rem;
            font-size: 0.8rem;
            color: rgba(255, 255, 255, 0.15);
            border-top: 1px solid var(--border-color);
            margin-top: auto;
        }

        .back-link {
            color: #fbbf24;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            font-weight: 600;
            font-size: 0.9rem;
            transition: all 0.3s;
        }

        .back-link:hover {
            color: #ef4444;
            transform: translateX(-3px);
        }
    </style>
</head>
<body>
    <header>
        <div class="logo-section">
            <h1>八卦乾坤</h1>
            <p>KUNPENGZHI • BAGUA DEBATE MONITOR</p>
        </div>
        <div style="display: flex; align-items: center; gap: 1rem;">
            <a href="/" class="back-link">← 返回主页</a>
            <div class="status-badge" id="monitor-status">
                <span class="status-dot"></span>
                <span id="status-text">实时连接中</span>
            </div>
        </div>
    </header>

    <div class="main-container">
        <div class="canvas-card">
            <svg class="svg-container" viewBox="0 0 600 600" xmlns="http://www.w3.org/2000/svg">
                <circle class="grid-circle" cx="300" cy="300" r="140" />
                <circle class="grid-circle" cx="300" cy="300" r="220" />
                <line class="grid-line" x1="300" y1="50" x2="300" y2="550" />
                <line class="grid-line" x1="50" y1="300" x2="550" y2="300" />
                <line class="grid-line" x1="123" y1="123" x2="477" y2="477" />
                <line class="grid-line" x1="477" y1="123" x2="123" y2="477" />

                <line id="path-1" class="debate-path pro-path" x1="300" y1="80" x2="300" y2="520" />
                <line id="path-2" class="debate-path con-path" x1="300" y1="520" x2="145" y2="145" />
                <line id="path-3" class="debate-path pro-path" x1="145" y1="145" x2="455" y2="455" />
                <line id="path-4" class="debate-path con-path" x1="455" y1="455" x2="80" y2="300" />
                <line id="path-5" class="debate-path pro-path" x1="80" y1="300" x2="520" y2="300" />
                <line id="path-6" class="debate-path con-path" x1="520" y1="300" x2="455" y2="145" />
                <line id="path-7" class="debate-path pro-path" x1="455" y1="145" x2="145" y2="455" />

                <g class="taiji-group" id="taiji">
                    <g class="taiji-rotate">
                        <circle cx="300" cy="300" r="50" fill="#111" stroke="#333" stroke-width="1.5" />
                        <path d="M 300,250 A 25,25 0 0,1 300,300 A 25,25 0 0,0 300,350 A 50,50 0 0,1 300,250 Z" fill="#e2e8f0" />
                        <circle cx="300" cy="275" r="7" fill="#111" />
                        <circle cx="300" cy="325" r="7" fill="#e2e8f0" />
                    </g>
                </g>

                <g class="node-group pro" id="node-pro1" onclick="selectNode('正方一辩')">
                    <circle cx="300" cy="80" r="30" class="node-ring" />
                    <text x="300" y="81" class="node-trigram">☰</text>
                    <text x="300" y="38" class="node-label">正方一辩</text>
                    <text x="300" y="126" class="node-character pro-text">乾 · 吕洞宾</text>
                </g>

                <g class="node-group con" id="node-con1" onclick="selectNode('反方一辩')">
                    <circle cx="300" cy="520" r="30" class="node-ring" />
                    <text x="300" y="521" class="node-trigram">☷</text>
                    <text x="300" y="562" class="node-label">反方一辩</text>
                    <text x="300" y="474" class="node-character con-text">坤 · 何仙姑</text>
                </g>

                <g class="node-group pro" id="node-pro2" onclick="selectNode('正方二辩')">
                    <circle cx="145" cy="145" r="30" class="node-ring" />
                    <text x="145" y="146" class="node-trigram">☶</text>
                    <text x="145" y="102" class="node-label">正方二辩</text>
                    <text x="145" y="191" class="node-character pro-text">艮 · 张果老</text>
                </g>

                <g class="node-group con" id="node-con2" onclick="selectNode('反方二辩')">
                    <circle cx="455" cy="455" r="30" class="node-ring" />
                    <text x="455" y="456" class="node-trigram">☱</text>
                    <text x="455" y="499" class="node-label">反方二辩</text>
                    <text x="455" y="411" class="node-character con-text">兑 · 韩湘子</text>
                </g>

                <g class="node-group pro" id="node-pro3" onclick="selectNode('正方三辩')">
                    <circle cx="80" cy="300" r="30" class="node-ring" />
                    <text x="80" y="301" class="node-trigram">☲</text>
                    <text x="80" y="258" class="node-label">正方三辩</text>
                    <text x="80" y="346" class="node-character pro-text">离 · 汉钟离</text>
                </g>

                <g class="node-group con" id="node-con3" onclick="selectNode('反方三辩')">
                    <circle cx="520" cy="300" r="30" class="node-ring" />
                    <text x="520" y="301" class="node-trigram">☵</text>
                    <text x="520" y="258" class="node-label">反方三辩</text>
                    <text x="520" y="346" class="node-character con-text">坎 · 蓝采和</text>
                </g>

                <g class="node-group pro" id="node-pro4" onclick="selectNode('正方四辩')">
                    <circle cx="455" cy="145" r="30" class="node-ring" />
                    <text x="455" y="146" class="node-trigram">☳</text>
                    <text x="455" y="102" class="node-label">正方四辩</text>
                    <text x="455" y="191" class="node-character pro-text">震 · 曹国舅</text>
                </g>

                <g class="node-group con" id="node-con4" onclick="selectNode('反方四辩')">
                    <circle cx="145" cy="455" r="30" class="node-ring" />
                    <text x="145" y="456" class="node-trigram">☴</text>
                    <text x="145" y="499" class="node-label">反方四辩</text>
                    <text x="145" y="411" class="node-character con-text">巽 · 铁拐李</text>
                </g>
            </svg>
        </div>

        <div class="info-sidebar">
            <div class="glass-panel topic-panel">
                <h2>当前辩题</h2>
                <h3 id="topic-title" style="margin-top: 0.5rem; font-size: 1.05rem; font-weight: 600;">等待辩题加载...</h3>
                <p id="debate-phase" style="margin-top: 0.4rem; color: #fbbf24; font-size: 0.85rem; font-weight: 500;">阶段: 尚未开始</p>
            </div>

            <div class="glass-panel debater-card" id="detail-panel">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 1rem;">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div class="trigram-avatar" id="detail-avatar">☰</div>
                        <div class="debater-title">
                            <h3 id="detail-role">正方一辩</h3>
                            <p id="detail-identity">乾 · 吕洞宾</p>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.4rem; font-size: 0.8rem; color: var(--text-secondary);">
                        <input type="checkbox" id="auto-track-cb" checked onchange="toggleAutoTrack(this)">
                        <label for="auto-track-cb" style="cursor: pointer; user-select: none;">自动追踪</label>
                    </div>
                </div>
                <div class="poem-box" id="detail-poem">点击八卦节点查看诗词与发言</div>
                <div style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.3rem; font-weight: 600;">🎙️ 发言实录</div>
                <div class="speech-box" id="detail-speech">无发言记录</div>
                <div class="whisper-box" id="detail-whisper">无实时指导</div>
            </div>
        </div>
    </div>

    <footer>
        鲲鹏志内容驱动辩论系统 · 智慧可视化看板 v1.0
    </footer>

    <script>
        const SPEAKER_POEMS = {
            "正方一辩": `【乾 ☰ · 吕洞宾 —— 鹊桥仙】
一柄纯阳宝剑，寒芒乍现，辞却九重天阙。人间自古情难尽，斩不绝、红尘恩怨。醉扶吕祖，清吟太白，试问纯阳生灭。道心点破鹊桥边，化作了、清风明月。`,
            "反方一辩": `【坤 ☷ · 何仙姑 —— 卷珠帘】
手执碧水青莲步玉沙。云散处、现仙家。不染红尘半点，珠帘高卷，缥缈看流霞。弱水三千空浪迹。心似月、净无瑕。一缕香风归去，高唐梦醒，独坐守瑶华。`,
            "正方二辩": `【艮 ☶ · 张果老 —— 临江仙】
倒骑毛驴江渚上，朝行碧海苍梧。手扣通玄渔鼓道情孤。古今多少事，盲眼看虚无。莫问老翁年几许，曾陪尧舜双枯。冷眼公卿尽泥涂。乾坤装入壳，一杖任徐驱。`,
            "反方二辩": `【兑 ☱ · 韩湘子 —— 苏幕遮】
紫金箫，清怨起。声振灵樾，音动微茫里。碧海苍梧飞仙履。一曲横吹，截断江河水。少年郎，心不死。踏遍群山，笑看红尘死。万古沧桑皆入耳。渔鼓声沉，唯有仙音在。`,
            "正方三辩": `【离 ☲ · 汉钟离 —— 一剪梅】
手摇芭蕉宝扇夜气清。急鼓初催，乐奏公卿。满堂金翠转头空，大汉将军，解甲归蓬。一展神风雾隐腾。莫问流光，冷眼输赢。任他樱桃红透时，几度春风，老了仙翁。`,
            "反方三辩": `【坎 ☵ · 蓝采和 —— 西江月】
手执叠板花篮，盛来满槛春风。竹板声声戏顽童，醉倒长街乱冢。几点山前疏雨，半宵稻海鸣虫。算来贫贱与公侯，都是南柯一梦。`,
            "正方四辩": `【震 ☳ · 曹国舅 —— 虞美人】
掌中云阳玉笏何时了？权柄如罂粟。满城开遍美人花，谁解红衣妖艳、是鸩家。雕栏玉砌生尸骨，大梦惊吞吐。老夫脱却大朝衣，洗净满身浮毒、白云归。`,
            "反方四辩": `【巽 ☴ · 铁拐李 —— 卜算子】
背负太极葫芦落红尘，拐杖惊风雨。莫笑形骸至贱躯，壶里乾坤寓.酒肉任穿肠，不肯栖寒树。待到悬壶济世时，散作山前雾。`
        };

        const SPEAKER_INFO = {
            "正方一辩": { trigram: "☰", name: "乾 · 吕洞宾", id: "pro1", type: "pro" },
            "反方一辩": { trigram: "☷", name: "坤 · 何仙姑", id: "con1", type: "con" },
            "正方二辩": { trigram: "☶", name: "艮 · 张果老", id: "pro2", type: "pro" },
            "反方二辩": { trigram: "☱", name: "兑 · 韩湘子", id: "con2", type: "con" },
            "正方三辩": { trigram: "☲", name: "离 · 汉钟离", id: "pro3", type: "pro" },
            "反方三辩": { trigram: "☵", name: "坎 · 蓝采和", id: "con3", type: "con" },
            "正方四辩": { trigram: "☳", name: "震 · 曹国舅", id: "pro4", type: "pro" },
            "反方四辩": { trigram: "☴", name: "巽 · 铁拐李", id: "con4", type: "con" }
        };

        let localDebateState = null;
        let selectedRole = "正方一辩";
        let autoTracking = true;

        function selectNode(role) {
            autoTracking = false;
            document.getElementById("auto-track-cb").checked = false;
            selectedRole = role;
            updateDetailPanel();
        }

        function toggleAutoTrack(cb) {
            autoTracking = cb.checked;
            if (autoTracking && localDebateState && localDebateState.active_role) {
                selectedRole = localDebateState.active_role;
                updateDetailPanel();
            }
        }

        function updateDetailPanel() {
            if (!localDebateState) return;

            const role = selectedRole;
            const info = SPEAKER_INFO[role];
            const roundData = localDebateState.rounds[role] || {};

            document.getElementById("detail-role").textContent = role;
            document.getElementById("detail-role").className = info.type + "-text";
            document.getElementById("detail-identity").textContent = info.name;
            document.getElementById("detail-avatar").textContent = info.trigram;
            document.getElementById("detail-poem").textContent = SPEAKER_POEMS[role] || "无";

            const speechEl = document.getElementById("detail-speech");
            const whisperEl = document.getElementById("detail-whisper");

            const incomingSpeech = (roundData.speech || "暂无发言内容").trim();
            const renderedSpeech = speechEl.dataset.fullText || "";
            
            if (incomingSpeech !== "暂无发言内容" && incomingSpeech.startsWith(renderedSpeech) && renderedSpeech.length > 0) {
                const diffText = incomingSpeech.substring(renderedSpeech.length);
                if (diffText.length > 0) {
                    speechEl.innerHTML += diffText.replace(/\n/g, '<br>');
                    speechEl.dataset.fullText = incomingSpeech;
                    speechEl.scrollTop = speechEl.scrollHeight;
                }
            } else {
                speechEl.innerHTML = incomingSpeech.replace(/\n/g, '<br>');
                speechEl.dataset.fullText = incomingSpeech;
            }

            whisperEl.textContent = roundData.whisper || "暂无教练实时耳语指导";
        }

        async function fetchState() {
            try {
                const res = await fetch('/bagua/api');
                if (!res.ok) throw new Error("API response error");
                const state = await res.json();
                
                localDebateState = state;
                document.getElementById("topic-title").textContent = state.topic_title || "等待辩题开始...";
                
                const dot = document.querySelector(".status-dot");
                const text = document.getElementById("status-text");
                
                if (state.current_round === 0) {
                    dot.className = "status-dot";
                    text.textContent = "辩论未开始";
                    document.getElementById("debate-phase").textContent = "阶段: 尚未开始";
                } else if (state.current_round === 9) {
                    dot.className = "status-dot completed";
                    text.textContent = "辩论已结束";
                    document.getElementById("debate-phase").textContent = "阶段: 终局归纳";
                } else {
                    dot.className = "status-dot active";
                    text.textContent = "辩论进行中";
                    document.getElementById("debate-phase").textContent = `阶段: 第 \${state.current_round} / 8 轮 (\${state.active_role} 发言中)`;
                    
                    if (autoTracking && state.active_role && selectedRole !== state.active_role) {
                        selectedRole = state.active_role;
                    }
                }

                updateVisuals(state);
                updateDetailPanel();

            } catch (err) {
                console.error("Polling state error:", err);
                const dot = document.querySelector(".status-dot");
                const text = document.getElementById("status-text");
                dot.className = "status-dot";
                text.textContent = "连接断开，重试中";
            }
        }

        function updateVisuals(state) {
            for (const [role, info] of Object.entries(SPEAKER_INFO)) {
                const nodeEl = document.getElementById(`node-\${info.id}`);
                if (!nodeEl) continue;

                const roundData = state.rounds[role] || {};
                const status = roundData.status || "pending";

                nodeEl.classList.remove("active", "completed", "pending");
                nodeEl.classList.add(status);

                const oldPulse = nodeEl.querySelector(".pulsate-circle");
                if (oldPulse) oldPulse.remove();

                if (status === "active") {
                    const cx = nodeEl.querySelector("circle").getAttribute("cx");
                    const cy = nodeEl.querySelector("circle").getAttribute("cy");
                    const pulseCircle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
                    pulseCircle.setAttribute("cx", cx);
                    pulseCircle.setAttribute("cy", cy);
                    pulseCircle.setAttribute("r", "30");
                    pulseCircle.setAttribute("fill", "none");
                    pulseCircle.setAttribute("stroke", "var(--color-active)");
                    pulseCircle.setAttribute("stroke-width", "1.5");
                    pulseCircle.setAttribute("class", "pulsate-circle");
                    nodeEl.insertBefore(pulseCircle, nodeEl.firstChild);
                }
            }

            const currentRound = state.current_round;

            for (let i = 1; i <= 7; i++) {
                const pathEl = document.getElementById(`path-\${i}`);
                if (!pathEl) continue;

                pathEl.classList.remove("active", "completed");

                if (currentRound === 9) {
                    pathEl.classList.add("completed");
                } else if (i < currentRound) {
                    pathEl.classList.add("completed");
                } else if (i === currentRound) {
                    pathEl.classList.add("active");
                }
            }
        }

        document.getElementById("taiji").addEventListener("click", () => {
            autoTracking = true;
            document.getElementById("auto-track-cb").checked = true;
            if (localDebateState && localDebateState.active_role) {
                selectedRole = localDebateState.active_role;
            } else {
                selectedRole = "正方一辩";
            }
            updateDetailPanel();
        });

        fetchState();
        setInterval(fetchState, 1000);
    </script>
</body>
</html>"""

@app.get("/bagua")
async def get_bagua_page():
    return HTMLResponse(content=HTML_CONTENT)

LEFT_BOARD_CONTENT = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>鲲鹏志 · 系统监控与原文检索</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Noto+Sans+SC:wght@300;400;500;700&family=Share+Tech+Mono&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #030508;
            --card-bg: rgba(7, 10, 17, 0.95);
            --border-color: rgba(59, 130, 246, 0.25);
            --text-primary: #38bdf8; /* Cyan */
            --text-secondary: #0ea5e9;
            --neon-green: #34d399;
            --neon-amber: #fbbf24;
            --neon-cyan: #22d3ee;
            --neon-red: #f87171;
            --terminal-bg: #010204;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-primary);
            font-family: "Share Tech Mono", "Outfit", "Noto Sans SC", sans-serif;
            height: 100vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            padding: 0.6rem;
            position: relative;
        }

        /* CRT Scanline & Screen effect */
        body::after {
            content: " ";
            display: block;
            position: fixed;
            top: 0; left: 0; bottom: 0; right: 0;
            background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.3) 50%);
            z-index: 9999;
            background-size: 100% 3px;
            pointer-events: none;
            opacity: 0.85;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1.5px solid var(--border-color);
            padding-bottom: 0.4rem;
            margin-bottom: 0.5rem;
            flex-shrink: 0;
        }

        h1 {
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--neon-cyan);
            display: flex;
            align-items: center;
            gap: 0.4rem;
            text-shadow: 0 0 8px rgba(34, 211, 238, 0.5);
        }

        .ticker {
            font-size: 0.72rem;
            color: var(--neon-amber);
            display: flex;
            gap: 0.6rem;
            background: rgba(251, 191, 36, 0.05);
            padding: 0.15rem 0.5rem;
            border: 1px dashed rgba(251, 191, 36, 0.2);
            border-radius: 4px;
        }

        .ticker span {
            font-weight: bold;
        }

        .grid-container {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            flex: 1;
            overflow: hidden;
        }

        .panel {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 0.6rem;
            display: flex;
            flex-direction: column;
            box-shadow: 0 0 15px rgba(59, 130, 246, 0.15);
            overflow: hidden;
            position: relative;
        }

        .panel::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, var(--neon-cyan), transparent);
        }

        .panel-header {
            font-size: 0.75rem;
            font-weight: bold;
            color: var(--neon-cyan);
            margin-bottom: 0.4rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(59, 130, 246, 0.2);
            padding-bottom: 0.25rem;
            user-select: none;
        }

        .panel-header .tag {
            background: rgba(34, 211, 238, 0.1);
            padding: 0.05rem 0.3rem;
            border-radius: 3px;
            font-size: 0.65rem;
        }

        .rag-content {
            font-size: 0.72rem;
            line-height: 1.4;
            color: var(--neon-green);
            overflow-y: auto;
            padding-right: 0.3rem;
            white-space: pre-wrap;
            scrollbar-width: thin;
            scrollbar-color: rgba(59, 130, 246, 0.2) transparent;
            flex: 1;
        }

        .rag-content strong {
            color: var(--neon-amber);
            text-shadow: 0 0 4px rgba(251, 191, 36, 0.3);
        }

        /* Oscilloscope & Stats Grid */
        .metrics-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.5rem;
            padding: 0.2rem 0;
        }

        .metric-item {
            display: flex;
            flex-direction: column;
            gap: 0.2rem;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.05);
            padding: 0.3rem 0.5rem;
            border-radius: 4px;
        }

        .m-header {
            display: flex;
            justify-content: space-between;
            font-size: 0.65rem;
            color: var(--text-secondary);
        }

        .m-value {
            font-size: 0.8rem;
            font-weight: bold;
            color: var(--neon-amber);
        }

        .m-bar {
            height: 4px;
            background: rgba(255,255,255,0.08);
            border-radius: 2px;
            overflow: hidden;
        }

        .m-bar-inner {
            height: 100%;
            background: var(--neon-cyan);
            box-shadow: 0 0 5px var(--neon-cyan);
            transition: width 0.3s ease;
        }

        .oscilloscope-panel {
            grid-column: span 2;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.05);
            padding: 0.3rem 0.5rem;
            border-radius: 4px;
        }

        /* TTY Console Shell */
        .terminal-shell {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: var(--terminal-bg);
            border-radius: 4px;
            overflow: hidden;
            border: 1px solid rgba(59, 130, 246, 0.15);
        }

        .terminal-logs {
            flex: 1;
            overflow-y: auto;
            padding: 0.4rem;
            font-size: 0.72rem;
            line-height: 1.3;
            color: #38bdf8;
            scrollbar-width: thin;
            scrollbar-color: rgba(59, 130, 246, 0.2) transparent;
        }

        .log-entry {
            margin-bottom: 0.2rem;
            word-break: break-all;
        }

        .log-entry.info { color: #38bdf8; }
        .log-entry.warn { color: var(--neon-amber); }
        .log-entry.error { color: var(--neon-red); }
        .log-entry.success { color: var(--neon-green); }
        .log-entry.input-command { color: #ffffff; font-weight: bold; }

        .terminal-form {
            display: flex;
            align-items: center;
            border-top: 1px solid rgba(59, 130, 246, 0.2);
            padding: 0.3rem 0.5rem;
            background: #020305;
            flex-shrink: 0;
        }

        .prompt-symbol {
            color: var(--neon-green);
            font-weight: bold;
            margin-right: 0.4rem;
            user-select: none;
            font-size: 0.72rem;
        }

        .terminal-form input {
            flex: 1;
            background: transparent;
            border: none;
            outline: none;
            color: #ffffff;
            font-family: "Share Tech Mono", monospace;
            font-size: 0.72rem;
            caret-color: var(--neon-cyan);
        }

        .placeholder {
            font-style: italic;
            opacity: 0.4;
            text-align: center;
            padding: 1rem 0;
            font-size: 0.7rem;
            color: var(--neon-green);
        }

        /* custom scrollbar */
        ::-webkit-scrollbar {
            width: 4px;
            height: 4px;
        }
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(59, 130, 246, 0.2);
            border-radius: 2px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(59, 130, 246, 0.4);
        }
    </style>
</head>
<body>
    <header>
        <h1><span>📡</span> KUNPENG_TELEMETRY</h1>
        <div class="ticker">
            SYS: <span>ACTIVE</span> | LLM: <span style="color: var(--neon-green)">OK</span> | TTS: <span id="ticker-tts">ON</span>
        </div>
    </header>

    <div class="grid-container">
        <!-- F1: BOOK RAG -->
        <div class="panel" style="height: 145px; flex-shrink: 0;">
            <div class="panel-header">
                <span>[F1: BOOK_RAG_SOURCE]</span>
                <span class="tag">QUERY_OK</span>
            </div>
            <div class="rag-content" id="rag-book-content">
                <div class="placeholder">等待检索关联原文...</div>
            </div>
        </div>

        <!-- F2: VECTOR MATCHES -->
        <div class="panel" style="height: 145px; flex-shrink: 0;">
            <div class="panel-header">
                <span>[F2: VEC_HIST_DB]</span>
                <span class="tag">COS_SIM</span>
            </div>
            <div class="rag-content" id="rag-past-content">
                <div class="placeholder">等待检索历史关联数据...</div>
            </div>
        </div>

        <!-- F3: HARDWARE MONITOR & OSCILLOSCOPE -->
        <div class="panel" style="height: 105px; flex-shrink: 0;">
            <div class="panel-header">
                <span>[F3: SYS_OSCILLOSCOPE]</span>
                <span class="tag">LIVE</span>
            </div>
            <div class="metrics-container">
                <div class="metric-item">
                    <div class="m-header">
                        <span>CPU_LOAD</span>
                        <span id="cpu-num">32%</span>
                    </div>
                    <div class="m-bar">
                        <div class="m-bar-inner" id="cpu-bar" style="width: 32%;"></div>
                    </div>
                </div>
                <div class="metric-item">
                    <div class="m-header">
                        <span>API_LATENCY</span>
                        <span id="lat-num">1.1s</span>
                    </div>
                    <div class="m-bar">
                        <div class="m-bar-inner" id="lat-bar" style="width: 55%; background: var(--neon-amber); box-shadow: 0 0 5px var(--neon-amber);"></div>
                    </div>
                </div>
                <div class="oscilloscope-panel">
                    <span style="font-size: 0.65rem; color: var(--text-secondary); flex-shrink: 0;">OSCILLOSCOPE:</span>
                    <canvas id="wave-canvas" width="230" height="15" style="background: #020203; border: 1px solid rgba(59, 130, 246, 0.15); flex: 1;"></canvas>
                </div>
            </div>
        </div>

        <!-- F4: INTERACTIVE TTY CONSOLE -->
        <div class="panel" style="flex: 1; min-height: 150px;">
            <div class="panel-header">
                <span>[F4: TTY_SHELL_CONSOLE]</span>
                <span class="tag">STDOUT</span>
            </div>
            <div class="terminal-shell">
                <div class="terminal-logs" id="terminal-logs">
                    <div class="log-entry success">[SYSTEM] Bloomberg Terminal v5.0 initialized.</div>
                    <div class="log-entry success">[SYSTEM] Telemetry hook connected to KUNPENGZHI API.</div>
                    <div class="log-entry success">[SYSTEM] Type 'help' to access active command deck.</div>
                </div>
                <form class="terminal-form" id="terminal-form">
                    <span class="prompt-symbol">KUNPENG@ROOT:~#</span>
                    <input type="text" id="terminal-input" autocomplete="off" placeholder="Enter command (e.g. 'help')...">
                </form>
            </div>
        </div>
    </div>

    <script>
        let lastLogs = [];
        let localDebateState = null;

        // Oscilloscope animation
        const canvas = document.getElementById('wave-canvas');
        const ctx = canvas.getContext('2d');
        let points = Array(40).fill(7.5);
        function drawWave() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            points.shift();
            const last = points[points.length - 1] || 7.5;
            const next = Math.max(2, Math.min(13, last + (Math.random() - 0.5) * 4));
            points.push(next);
            
            ctx.strokeStyle = '#22d3ee'; // Neon Cyan
            ctx.lineWidth = 1;
            ctx.beginPath();
            for(let i = 0; i < points.length; i++) {
                const x = (canvas.width / (points.length - 1)) * i;
                const y = points[i];
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            ctx.stroke();
        }
        setInterval(drawWave, 200);

        // Telemetry fluctuation simulator
        function fluctuateMetrics() {
            // CPU
            const cpuVal = Math.floor(25 + Math.random() * 20);
            document.getElementById('cpu-num').textContent = cpuVal + '%';
            document.getElementById('cpu-bar').style.width = cpuVal + '%';
            
            // Latency
            const latVal = (0.8 + Math.random() * 0.6).toFixed(2);
            document.getElementById('lat-num').textContent = latVal + 's';
            // Scale bar up to 2 seconds
            const latPercent = Math.min(100, Math.floor((latVal / 2) * 100));
            document.getElementById('lat-bar').style.width = latPercent + '%';
        }
        setInterval(fluctuateMetrics, 2000);

        // Fetch state and logs from backend
        async function pollStateAndLogs() {
            // 1. Fetch RAG data
            try {
                const res = await fetch('/bagua/api');
                if (res.ok) {
                    const state = await res.json();
                    localDebateState = state;
                    
                    // Update Book RAG
                    const bookEl = document.getElementById('rag-book-content');
                    if (state.book_content && state.book_content.trim() !== "") {
                        bookEl.innerHTML = state.book_content.replace(/\n/g, '<br>');
                    } else {
                        bookEl.innerHTML = '<div class="placeholder">等待检索关联原文...</div>';
                    }

                    // Update Past Debates
                    const pastEl = document.getElementById('rag-past-content');
                    if (state.past_debates && state.past_debates.trim() !== "") {
                        let formatted = state.past_debates
                            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                            .replace(/\n/g, '<br>');
                        pastEl.innerHTML = formatted;
                    } else {
                        pastEl.innerHTML = '<div class="placeholder">等待检索历史关联数据...</div>';
                    }

                    // Ticker updates
                    const tickerTts = document.getElementById('ticker-tts');
                    if (tickerTts) {
                        tickerTts.textContent = state.config && state.config.TTS_ENABLED === false ? 'OFF' : 'ON';
                    }
                }
            } catch (err) {
                console.error("Error polling debate api:", err);
            }

            // 2. Fetch Logs
            try {
                const res = await fetch('/status');
                if (res.ok) {
                    const statusData = await res.json();
                    const logs = statusData.logs || [];
                    
                    if (logs.length > 0 && JSON.stringify(logs) !== JSON.stringify(lastLogs)) {
                        lastLogs = [...logs];
                        const termEl = document.getElementById('terminal-logs');
                        
                        // Keep user-typed commands and outputs while appending new system logs
                        // To avoid complete wipe, we only append new logs
                        logs.forEach(log => {
                            // Simple check to prevent duplicate log displays
                            if (!logIsRendered(log)) {
                                appendLogEntry(log, getLogClass(log));
                            }
                        });
                        
                        termEl.scrollTop = termEl.scrollHeight;
                    }
                }
            } catch (err) {
                console.error("Error polling system status logs:", err);
            }
        }

        function logIsRendered(logText) {
            const termEl = document.getElementById('terminal-logs');
            const entries = termEl.getElementsByClassName('log-entry');
            for (let i = Math.max(0, entries.length - 20); i < entries.length; i++) {
                if (entries[i].textContent === logText) return true;
            }
            return false;
        }

        function getLogClass(log) {
            if (log.includes('ERROR') || log.includes('Exception') || log.includes('fail')) {
                return 'error';
            } else if (log.includes('WARNING') || log.includes('warn')) {
                return 'warn';
            } else if (log.includes('✅') || log.includes('success') || log.includes('完成') || log.includes('完成:')) {
                return 'success';
            }
            return 'info';
        }

        function appendLogEntry(text, className) {
            const termEl = document.getElementById('terminal-logs');
            const entry = document.createElement('div');
            entry.className = `log-entry ${className}`;
            entry.textContent = text;
            termEl.appendChild(entry);
            termEl.scrollTop = termEl.scrollHeight;
        }

        // Terminal command handling
        const termForm = document.getElementById('terminal-form');
        const termInput = document.getElementById('terminal-input');

        termForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const cmd = termInput.value.trim();
            termInput.value = '';
            if (!cmd) return;

            appendLogEntry(`SYS@KUNPENG:~$ ${cmd}`, 'input-command');

            const lowerCmd = cmd.toLowerCase();
            if (lowerCmd === 'help') {
                appendLogEntry("--- AVAILABLE COMMAND DECK ---", 'success');
                appendLogEntry("status   : Show debate server live parameters", 'info');
                appendLogEntry("sysinfo  : Check system telemetries and hardware", 'info');
                appendLogEntry("clear    : Wipe terminal console buffers", 'info');
                appendLogEntry("help     : Print this command registry", 'info');
            } else if (lowerCmd === 'clear') {
                const termEl = document.getElementById('terminal-logs');
                termEl.innerHTML = '';
                appendLogEntry("[SYSTEM] Console buffers cleared.", 'success');
            } else if (lowerCmd === 'status') {
                appendLogEntry("--- LIVE DEBATE PARAMETERS ---", 'success');
                if (localDebateState) {
                    appendLogEntry(`Topic    : ${localDebateState.topic_title || 'Waiting...'}`, 'info');
                    appendLogEntry(`Round    : ${localDebateState.current_round} / 8`, 'info');
                    appendLogEntry(`Speaker  : ${localDebateState.active_role || 'Idle'}`, 'info');
                } else {
                    appendLogEntry("Server   : Standby mode", 'info');
                    appendLogEntry("Topic    : Waiting for client selection", 'info');
                }
            } else if (lowerCmd === 'sysinfo') {
                appendLogEntry("--- DEBATE TELEMETRY CORE ---", 'success');
                appendLogEntry("Server OS: Heroku Linux Sandbox", 'info');
                appendLogEntry("Engine   : FastAPI + Chainlit Engine", 'info');
                appendLogEntry("Database : Vector DB (Cloudflare Vectorize)", 'info');
                appendLogEntry("TTS Bind : Edge-TTS stitcher module", 'info');
            } else {
                appendLogEntry(`bash: ${cmd}: command not found. Type 'help' for support.`, 'error');
            }
        });

        pollStateAndLogs();
        setInterval(pollStateAndLogs, 1500);
    </script>
</body>
</html>
"""

@app.get("/left-board")
async def get_left_board_page():
    return HTMLResponse(content=LEFT_BOARD_CONTENT)

@app.get("/bagua/api")
async def get_bagua_api():
    return DEBATE_STATE

# 将 /status, /bagua, /bagua/api, /left-board 路由移动到 FastAPI 路由表的最前列，绕过 Chainlit 自带 of 单页应用 (SPA) 兜底通配符
try:
    target_paths = ["/status", "/bagua/api", "/bagua", "/left-board"]
    moved_routes = []
    i = 0
    while i < len(app.routes):
        r = app.routes[i]
        if hasattr(r, "path") and r.path in target_paths:
            moved_routes.append(app.routes.pop(i))
        else:
            i += 1
    for idx, r in enumerate(moved_routes):
        app.routes.insert(idx, r)
except Exception as e:
    log.error(f"Failed to prioritize custom routes: {e}")

if __name__ == "__main__":
    print("鲲鹏志 v4.6 · chainlit run app.py")

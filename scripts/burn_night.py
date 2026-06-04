#!/usr/bin/env python3
"""
鲲鹏志 · 夜间薅羊毛管线 v2 🐑💰
===============================
目标：今晚烧掉 $100 GCP 免费额度
策略：30路并发 × 大输入输出 × 多样化产物

产物类型（保证多样性）：
1. 知识图谱三元组（结构化）
2. 章节深度分析（长文）
3. 跨书概念关联报告
4. 四川话播客脚本 🎙️ ← NEW
5. 辩论全文（5种风格）
6. Q&A 语料库
7. 教学讨论指南
8. 叙事重述

最终推送 GitLab CE
"""

import os
import sys
import json
import asyncio
import logging
import time
import re
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(message)s")
log = logging.getLogger("burn")

# ─── 配置 ─────────────────────────────────────────
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:4000/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-47318")
DEBATE_MODEL = os.getenv("DEBATE_MODEL", "gemini-2.5-flash")
# ─── 启动校验 ────────────────────────────────────
_REQUIRED_ENV = ["CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN", "OPENAI_BASE_URL", "OPENAI_API_KEY"]
_MISSING = [v for v in _REQUIRED_ENV if not os.getenv(v)]
if _MISSING:
    log.warning(f"⚠️  缺少环境变量: {_MISSING}")
    log.warning("R2 上传和 LLM 调用可能失败，请检查 .env 文件或环境变量")
else:
    log.info("✅ 环境变量校验通过")

# 确保本地输出目录存在
_LOCAL_OUTPUTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs")
os.makedirs(os.path.join(_LOCAL_OUTPUTS, "kg"), exist_ok=True)
os.makedirs(os.path.join(_LOCAL_OUTPUTS, "analysis"), exist_ok=True)
os.makedirs(os.path.join(_LOCAL_OUTPUTS, "crossref"), exist_ok=True)
os.makedirs(os.path.join(_LOCAL_OUTPUTS, "podcast"), exist_ok=True)
os.makedirs(os.path.join(_LOCAL_OUTPUTS, "debates"), exist_ok=True)
os.makedirs(os.path.join(_LOCAL_OUTPUTS, "qa"), exist_ok=True)
os.makedirs(os.path.join(_LOCAL_OUTPUTS, "batch"), exist_ok=True)
log.info(f"📁 本地输出目录: {_LOCAL_OUTPUTS}")

CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
R2_BUCKET = os.getenv("R2_BUCKET", "kunpengzhi-tts")
BOOKS_DIR = os.getenv("KUNPENGZHI_BOOK_PATH", "/home/ben/kunpengzhi")

# GitLab CE
GITLAB_CE_URL = os.getenv("GITLAB_CE_URL", "https://gitlab.xiujiwei.com")
GITLAB_CE_TOKEN = os.getenv("GITLAB_CE_TOKEN", "")
GITLAB_PROJECT = os.getenv("GITLAB_PROJECT", "kunpengzhi/podcast-content")

# 并发控制
MAX_CONCURRENT = 20  # 50路并发 🔥
RATE_LIMIT_DELAY = 0.2  # 每批后等待（激进）

# 进度文件
PROGRESS_FILE = "/tmp/burn_progress.json"

# ─── LLM Client ──────────────────────────────────
import openai

client = openai.AsyncOpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)

# 信号量控制并发
semaphore = asyncio.Semaphore(MAX_CONCURRENT)

async def llm_burn(prompt: str, system: str = "", max_tokens: int = 8192) -> Tuple[str, int]:
    """调用 LLM 并返回 (文本, 估算总token数) - 带有指数退避重试"""
    async with semaphore:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        input_tokens = len(prompt) + len(system)
        
        max_retries = 8
        backoff_factor = 2.0
        initial_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                resp = await client.chat.completions.create(
                    model=DEBATE_MODEL,
                    messages=messages,
                    max_tokens=max_tokens,
                    timeout=180,
                )
                text = resp.choices[0].message.content
                output_tokens = len(text) if text else 0
                return text or "", input_tokens + output_tokens
            except (openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError) as e:
                if attempt == max_retries - 1:
                    log.error(f"❌ LLM 调用失败（已达到最大重试次数）: {e}")
                    raise
                delay = initial_delay * (backoff_factor ** attempt)
                log.warning(f"⚠️  LLM 调用触发限流或超时 ({e})，正在进行第 {attempt + 1} 次重试，等待 {delay:.1f} 秒...")
                await asyncio.sleep(delay)
            except Exception as e:
                log.error(f"❌ LLM 发生非重试异常: {e}")
                raise


async def llm_stream_burn(prompt: str, system: str = "") -> Tuple[str, int]:
    """流式调用，适合长文本 - 带有指数退避重试"""
    async with semaphore:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        input_tokens = len(prompt) + len(system)
        
        max_retries = 8
        backoff_factor = 2.0
        initial_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                stream = await client.chat.completions.create(
                    model=DEBATE_MODEL,
                    messages=messages,
                    stream=True,
                    timeout=300,
                )
                
                result = ""
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        result += chunk.choices[0].delta.content
                
                return result, input_tokens + len(result)
            except (openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError) as e:
                if attempt == max_retries - 1:
                    log.error(f"❌ LLM 流式调用失败（已达到最大重试次数）: {e}")
                    raise
                delay = initial_delay * (backoff_factor ** attempt)
                log.warning(f"⚠️  LLM 流式调用触发限流或超时 ({e})，正在进行第 {attempt + 1} 次重试，等待 {delay:.1f} 秒...")
                await asyncio.sleep(delay)
            except Exception as e:
                log.error(f"❌ LLM 流式发生非重试异常: {e}")
                raise


# ─── R2 存储 ─────────────────────────────────────
import httpx

async def r2_upload(key: str, data: bytes) -> bool:
    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
        return False
    url = (f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}"
           f"/r2/buckets/{R2_BUCKET}/objects/{key}")
    async with httpx.AsyncClient() as c:
        r = await c.put(url, headers={"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"},
                        content=data, timeout=60)
        return r.status_code == 200 and r.json().get("success", False)


async def r2_upload_text(key: str, text: str) -> bool:
    """上传到 R2，同时写本地文件兜底"""
    # 本地兜底：把 key 中的 / 换成路径
    local_path = os.path.join(_LOCAL_OUTPUTS, key)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    try:
        with open(local_path, 'w', encoding='utf-8') as f:
            f.write(text)
    except Exception as e:
        log.warning(f"本地写入失败 {local_path}: {e}")
    
    # R2 上传
    ok = await r2_upload(key, text.encode("utf-8"))
    if ok:
        log.info(f"  ☁️  R2: {key} ({len(text)} bytes)")
    else:
        log.warning(f"  ⚠️  R2 上传失败，但已保存到本地: {local_path}")
    return ok


# ─── GitLab CE ───────────────────────────────────
async def gitlab_push_file(path: str, content: str, commit_msg: str) -> bool:
    """通过 GitLab API 推送文件到 CE"""
    if not GITLAB_CE_TOKEN:
        log.warning("⚠️  GITLAB_CE_TOKEN 未设置，跳过 GitLab 推送")
        return False
    
    # 先检查文件是否存在，获取 sha
    url = f"{GITLAB_CE_URL}/api/v4/projects/{GITLAB_PROJECT}/repository/files/{path.replace('/', '%2F')}"
    headers = {"PRIVATE-TOKEN": GITLAB_CE_TOKEN}
    
    # 获取当前 sha (如果文件已存在)
    existing_sha = None
    try:
        async with httpx.AsyncClient() as c:
            r = await c.get(url, headers=headers)
            if r.status_code == 200:
                existing_sha = r.json().get("content_sha256", "")
    except:
        pass
    
    # 创建或更新文件
    data = {
        "branch": "main",
        "content": content,
        "commit_message": commit_msg,
        "encoding": "text",
    }
    if existing_sha:
        data["sha"] = existing_sha
    
    try:
        async with httpx.AsyncClient() as c:
            r = await c.post(url + "?branch=main", headers=headers, json=data)
            if r.status_code in (200, 201):
                log.info(f"  ✅ GitLab CE: {path}")
                return True
            # 尝试 PUT (更新)
            r2 = await c.put(url, headers=headers, json=data)
            if r2.status_code in (200, 201):
                log.info(f"  ✅ GitLab CE (update): {path}")
                return True
            log.warning(f"  ❌ GitLab CE push failed: {r.status_code} {r.text[:200]}")
    except Exception as e:
        log.warning(f"  ❌ GitLab CE error: {e}")
    return False


# ─── 书籍扫描 ────────────────────────────────────

def scan_books() -> List[Dict]:
    chapters = []
    book_dirs = ["牧人记", "双约记", "牧兰记", "牧月记"]
    for book in book_dirs:
        book_path = os.path.join(BOOKS_DIR, book)
        if not os.path.isdir(book_path):
            continue
        for fname in sorted(os.listdir(book_path)):
            if fname.endswith(".md") and not fname.startswith("."):
                fpath = os.path.join(book_path, fname)
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                chapters.append({
                    "book": book,
                    "chapter": fname.replace(".md", ""),
                    "content": content,
                    "length": len(content),
                })
    log.info(f"📚 扫描到 {len(chapters)} 个章节")
    return chapters


# ─── 进度管理 ────────────────────────────────────

def load_progress() -> Dict:
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"done": {}}


def mark_done(pipeline: str, key: str):
    p = load_progress()
    if pipeline not in p["done"]:
        p["done"][pipeline] = []
    p["done"][pipeline].append(key)
    with open(PROGRESS_FILE, "w") as f:
        json.dump(p, f, ensure_ascii=False)


def is_done(pipeline: str, key: str) -> bool:
    p = load_progress()
    return key in p["done"].get(pipeline, [])


# ═══════════════════════════════════════════════════
# 管线 1: 知识图谱三元组 (结构化)
# ═══════════════════════════════════════════════════

async def process_kg_chapter(ch: Dict) -> Tuple[List[Dict], int]:
    """提取一个章节的三元组"""
    content = ch['content'][:8000]  # 前8000字
    
    system = "你是一个历史知识图谱构建专家。只输出 JSON Lines，不要其他文字。"
    prompt = f"""从以下文本中提取所有实体-关系-实体三元组。

文本：{ch['book']} - {ch['chapter']}

{content}

格式（每行一个 JSON）：
{{"s": "实体A", "r": "关系类型", "o": "实体B", "c": "原文片段"}}

关系类型：ATTACK|ALLY|SUCCEED|REPLACE|INHERIT|TRADE|MARRY|LEAD|SERVE|OPPOSE|FOUND|DESTROY|MIGRATE|BELIEVE|CREATE|BELONG_TO|LOCATED_IN|PART_OF

提取尽量多的三元组。"""
    
    text, tokens = await llm_burn(prompt, system)
    
    triples = []
    for line in text.strip().split('\n'):
        line = line.strip()
        if line.startswith('{') and line.endswith('}'):
            try:
                t = json.loads(line)
                t['book'] = ch['book']
                t['chapter'] = ch['chapter']
                triples.append(t)
            except:
                pass
    
    return triples, tokens


async def pipeline_1_kg(chapters: List[Dict]):
    """知识图谱 - 30路并发"""
    log.info("=" * 60)
    log.info("🚀 管线 1: 知识图谱 (30路并发)")
    log.info("=" * 60)
    
    all_triples = []
    total_tokens = 0
    
    # 分批并发
    for i in range(0, len(chapters), MAX_CONCURRENT):
        batch = chapters[i:i+MAX_CONCURRENT]
        keys = [f"kg/{c['book']}/{c['chapter']}" for c in batch]
        
        # 跳过已完成的
        todo = [(c, k) for c, k in zip(batch, keys) if not is_done("kg", k)]
        
        if not todo:
            continue
        
        log.info(f"  批量 {i//MAX_CONCURRENT + 1}: {len(todo)} 个章节")
        
        results = await asyncio.gather(*[process_kg_chapter(c) for c, _ in todo])
        
        for (c, k), (triples, tokens) in zip(todo, results):
            all_triples.extend(triples)
            total_tokens += tokens
            mark_done("kg", k)
            # 逐章保存到本地
            try:
                ch_key = f"kg/{c['book']}/{c['chapter']}.json"
                ch_data = json.dumps(triples, ensure_ascii=False, indent=2)
                local_path = os.path.join(_LOCAL_OUTPUTS, ch_key)
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                with open(local_path, 'w', encoding='utf-8') as f:
                    f.write(ch_data)
            except Exception as e:
                log.warning(f"  本地保存失败: {e}")
            log.info(f"    ✅ {c['book']}/{c['chapter']}: {len(triples)} 三元组 (~{tokens} tokens)")
        
        await asyncio.sleep(RATE_LIMIT_DELAY)
    
    # 上传结果
    if all_triples:
        await r2_upload_text("kg/full_triples.json", json.dumps(all_triples, ensure_ascii=False))
        
        # 统计
        entities = set()
        for t in all_triples:
            entities.add(t.get('s', ''))
            entities.add(t.get('o', ''))
        
        report = {
            "triples": len(all_triples),
            "entities": len(entities),
            "tokens_consumed": total_tokens,
        }
        await r2_upload_text("kg/stats.json", json.dumps(report, ensure_ascii=False))
        log.info(f"\n📊 管线1: {len(all_triples)} 三元组, {len(entities)} 实体, ~{total_tokens:,} tokens")
    
    return total_tokens


# ═══════════════════════════════════════════════════
# 管线 2: 章节深度分析 (长文)
# ═══════════════════════════════════════════════════

ANALYSIS_TYPES = [
    ("summary", "写一篇全面的章节摘要（1500字以上），包含核心论点、人物、历史背景"),
    ("arguments", "分析本章的核心论点与反论点（1200字以上），指出矛盾和张力的来源"),
    ("position", "分析本章在全书叙事结构中的位置和功能（1000字以上）"),
    ("characters", "分析本章出现的主要人物及其动机、立场（1000字以上）"),
    ("timeline", "梳理本章涉及的历史事件时间线（800字以上）"),
]


async def process_analysis(ch: Dict, atype: str, instruction: str) -> Tuple[str, int]:
    """生成一种分析"""
    prompt = f"""请为以下章节{instruction}。

章节：{ch['book']} - {ch['chapter']}

原文：
{ch['content'][:6000]}

要求：分析要深入、具体，引用原文。直接输出分析内容。"""
    
    text, tokens = await llm_stream_burn(prompt)
    return text, tokens


async def pipeline_2_analysis(chapters: List[Dict]):
    """章节分析 - 5种分析 × 并发"""
    log.info("=" * 60)
    log.info("🚀 管线 2: 章节深度分析 (5种类型)")
    log.info("=" * 60)
    
    total_tokens = 0
    all_analyses = []
    
    for ch in chapters:
        tasks = []
        for atype, instr in ANALYSIS_TYPES:
            key = f"analysis/{ch['book']}/{ch['chapter']}/{atype}"
            if is_done("analysis", key):
                continue
            tasks.append((atype, key, process_analysis(ch, atype, instr)))
        
        if not tasks:
            continue
        
        log.info(f"  📖 {ch['book']}/{ch['chapter']}: {len(tasks)} 种分析并发")
        
        results = await asyncio.gather(*[t for _, _, t in tasks])
        
        for (atype, key, _), (text, tokens) in zip(tasks, results):
            all_analyses.append({
                "book": ch['book'],
                "chapter": ch['chapter'],
                "type": atype,
                "content": text,
            })
            total_tokens += tokens
            mark_done("analysis", key)
        
        await asyncio.sleep(RATE_LIMIT_DELAY * 0.5)
    
    # 上传
    if all_analyses:
        await r2_upload_text("analysis/full_analyses.json", json.dumps(all_analyses, ensure_ascii=False))
        log.info(f"\n📊 管线2: {len(all_analyses)} 篇分析, ~{total_tokens:,} tokens")
    
    return total_tokens


# ═══════════════════════════════════════════════════
# 管线 3: 跨书概念关联
# ═══════════════════════════════════════════════════

CORE_CONCEPTS = [
    "嚈哒帝国", "白貂皮大衣", "木兰", "大同流亡军团", "安史之乱",
    "节度使制度", "产权分割", "丝绸之路", "北魏", "突厥",
    "波斯", "佛教传播", "草原帝国", "中原王朝", "民族融合",
    "贸易网络", "文明冲突", "历史书写权", "身份认同", "迁徙",
    "长城", "西域", "科举制度", "道教", "儒家",
    "佛教", "游牧文明", "农耕文明", "军事制度", "税收制度",
    "土地制度", "官制演变", "文化融合", "技术传播", "瘟疫",
    "气候变化", "人口迁移", "文字系统", "法律体系", "货币",
    "马政", "驿站系统", "水利工程", "都城规划", "墓葬文化",
    "天文历法", "医学", "兵法", "外交", "和亲",
    "质子", "朝贡", "羁縻", "屯田", "盐铁",
    "府兵制", "均田制", "租庸调", "两税法", "科举",
    "门阀", "士族", "寒门", "宦官", "藩镇",
    "匈奴", "鲜卑", "柔然", "突厥", "回鹘",
    "吐蕃", "南诏", "高句丽", "百济", "新罗",
    "倭国", "大食", "拂林", "天竺", "真腊",
]


async def process_concept(concept: str, chapters: List[Dict]) -> Tuple[Optional[Dict], int]:
    """分析一个概念的跨书关联"""
    # 查找提及
    mentions = []
    for ch in chapters:
        idx = ch['content'].find(concept)
        if idx >= 0:
            start = max(0, idx - 150)
            end = min(len(ch['content']), idx + len(concept) + 250)
            ctx = ch['content'][start:end].replace('\n', ' ')[:400]
            mentions.append({"book": ch['book'], "chapter": ch['chapter'], "context": ctx})
    
    if not mentions:
        return None, 0
    
    # 按书分组
    books_covered = list(set(m['book'] for m in mentions))
    
    mentions_text = "\n\n".join([
        f"[{m['book']}/{m['chapter']}] {m['context']}"
        for m in mentions[:8]
    ])
    
    prompt = f"""概念：【{concept}】
全书提及：{len(mentions)} 处，涉及 {', '.join(books_covered)}

上下文片段：
{mentions_text}

请生成一份跨书关联分析（1200字以上）：
1. 这个概念在四本书中分别如何呈现？
2. 含义在不同书中是否有演变？
3. 连接了哪些不同的叙事线索？
4. 在整个鲲鹏志宇宙中处于什么地位？
5. 如果围绕这个概念做一个播客节目，应该讨论什么？

分析："""
    
    text, tokens = await llm_stream_burn(prompt)
    
    report = {
        "concept": concept,
        "mentions": len(mentions),
        "books": books_covered,
        "analysis": text,
    }
    return report, tokens


async def pipeline_3_crossref(chapters: List[Dict]):
    """跨书概念分析 - 并发"""
    log.info("=" * 60)
    log.info("🚀 管线 3: 跨书概念关联 ({len(CORE_CONCEPTS)} 个概念)")
    log.info("=" * 60)
    
    total_tokens = 0
    reports = []
    
    for i in range(0, len(CORE_CONCEPTS), MAX_CONCURRENT):
        batch = CORE_CONCEPTS[i:i+MAX_CONCURRENT]
        keys = [f"crossref/{c}" for c in batch]
        
        todo = [(c, k) for c, k in zip(batch, keys) if not is_done("crossref", k)]
        if not todo:
            continue
        
        log.info(f"  批量 {i//MAX_CONCURRENT + 1}: {len(todo)} 个概念")
        
        results = await asyncio.gather(*[process_concept(c, chapters) for c, _ in todo])
        
        for (c, k), (report, tokens) in zip(todo, results):
            if report:
                reports.append(report)
                total_tokens += tokens
                mark_done("crossref", k)
                log.info(f"    ✅ {c}: {report['mentions']} 处提及 (~{tokens} tokens)")
        
        await asyncio.sleep(RATE_LIMIT_DELAY)
    
    if reports:
        await r2_upload_text("crossref/concept_reports.json", json.dumps(reports, ensure_ascii=False))
        log.info(f"\n📊 管线3: {len(reports)} 个概念, ~{total_tokens:,} tokens")
    
    return total_tokens


# ═══════════════════════════════════════════════════
# 管线 4: 播客脚本 🎙️ (四川话男 + 普通话女)
# ═══════════════════════════════════════════════════

PODCAST_TOPICS = [
    # (标题, 关联概念, 角度)
    ("白貂皮大衣：一件衣服串起的世界史", ["白貂皮大衣", "嚈哒帝国", "丝绸之路", "贸易网络"],
     "从一件衣服看全球贸易网络的雏形"),
    ("木兰无长兄：一首诗背后的流亡军团", ["木兰", "大同流亡军团", "北魏", "民族融合"],
     "《木兰辞》中的历史密码"),
    ("安史之乱：一次古代企业并购", ["安史之乱", "节度使制度", "产权分割"],
     "用经济学重新理解安史之乱"),
    ("草原帝国为什么总爱南下？", ["草原帝国", "中原王朝", "游牧文明", "农耕文明"],
     "游牧与农耕的千年博弈"),
    ("佛教入华：一场最成功的文化输入", ["佛教传播", "丝绸之路", "文化融合"],
     "宗教如何改变一个文明"),
    ("丝绸之路不只是贸易路", ["丝绸之路", "技术传播", "瘟疫", "人口迁移"],
     "病菌、技术和思想的旅行"),
    ("北魏：一个少数民族的汉化实验", ["北魏", "民族融合", "身份认同", "科举制度"],
     "中国历史上最大规模的文化融合实验"),
    ("突厥与中原：相爱相杀的千年", ["突厥", "和亲", "朝贡", "军事制度"],
     "恩恩怨怨说不清的草原-中原关系"),
    ("长安：一座世界城市的兴衰", ["都城规划", "西域", "贸易网络", "文化融合"],
     "唐朝长安为什么是世界之都"),
    ("历史是谁写的？", ["历史书写权", "身份认同", "文明冲突"],
     "叙事权才是真正的权力"),
    ("嚈哒帝国：被遗忘的草原霸主", ["嚈哒帝国", "突厥", "波斯", "丝绸之路"],
     "比突厥还强大的帝国为什么被历史遗忘"),
    ("瘟疫如何改变了中国历史", ["瘟疫", "气候变化", "人口迁移", "军事制度"],
     "微生物才是历史的真正推手"),
    ("唐朝军事实力为什么那么强？", ["府兵制", "马政", "军事制度", "节度使制度"],
     "从兵制看唐朝的崛起与衰落"),
    ("科举：中国古代的高考", ["科举制度", "门阀", "士族", "寒门"],
     "考试制度如何重塑了中国社会"),
    ("大同流亡军团：一支孤军的西行", ["大同流亡军团", "嚈哒帝国", "北魏"],
     "命运多舛的流亡者如何改变了世界"),
]

PODCAST_INTRO = """🎙️ 【鲲鹏志·边角聊】开场白

男（四川话·青衣）：「各位听众朋友大家好，欢迎收听《鲲鹏志·边角聊》。我是青衣。」
女（普通话·峨眉）：「我是峨眉。」
男（四川话）：「我们两个又来摆龙门阵了。今天要聊的话题有点意思——」
"""


async def generate_podcast_episode(topic: List, chapters: List[Dict]) -> Tuple[Dict, int]:
    """生成一集播客脚本"""
    title, concepts, angle = topic
    
    # 收集相关原文
    context_parts = []
    for ch in chapters:
        for concept in concepts:
            if concept in ch['content']:
                idx = ch['content'].index(concept)
                start = max(0, idx - 300)
                end = min(len(ch['content']), idx + len(concept) + 500)
                ctx = ch['content'][start:end]
                context_parts.append(f"[{ch['book']}/{ch['chapter']}]\n{ctx}")
                break
    
    context = "\n\n".join(context_parts[:5]) if context_parts else "（无直接原文引用）"
    
    prompt = f"""你是一名播客编剧。请为播客节目《鲲鹏志·边角聊》写一集完整的对话脚本。

## 本期主题
{title}

## 核心角度
{angle}

## 参考原文
{context}

## 主持人设定
- **男主播**（青衣）：四川人，说**四川话**。以青衣江为名，性格如江水般豪爽奔放、幽默接地气，喜欢用四川方言表达观点，比如"这个就有点巴适了哦"、"你晓得不？"、"硬是凶得很哦"。偶尔插科打诨，但关键时刻有深度。
- **女主播**（峨眉）：说**普通话**。以峨眉山为名，气质如高山般知性沉稳、逻辑清晰，负责引导话题和深入分析。偶尔接梗，和男主播有默契的互动。

## 格式要求
- 每段标注说话人：【青衣】或【峨眉】
- 四川话部分用拼音或汉字写出来都可以，但必须是四川方言风格
- 总长度：3000-5000字
- 风格：轻松但有深度，像两个好朋友聊天

## 脚本结构
1. **开场**（四川话男开场 + 女接话）
2. **话题引入**（为什么聊这个？）
3. **背景铺垫**（历史故事、事件）
4. **深度讨论**（核心论点、争议点）
5. **精彩碰撞**（男女观点交锋）
6. **收尾升华**（回到现实意义、引发思考）

请直接输出脚本："""
    
    text, tokens = await llm_stream_burn(prompt)
    
    episode = {
        "title": title,
        "concepts": concepts,
        "angle": angle,
        "script": text,
        "timestamp": datetime.now().isoformat(),
    }
    return episode, tokens


async def pipeline_4_podcast(chapters: List[Dict]):
    """播客脚本生成 - 15集"""
    log.info("=" * 60)
    log.info("🚀 管线 4: 播客脚本生成 🎙️ (四川话男+普通话女)")
    log.info("=" * 60)
    
    total_tokens = 0
    episodes = []
    
    for i in range(0, len(PODCAST_TOPICS), 5):  # 每次5集并发
        batch = PODCAST_TOPICS[i:i+5]
        keys = [f"podcast/ep{i+j:02d}" for j in range(len(batch))]
        
        todo = [(t, k) for t, k in zip(batch, keys) if not is_done("podcast", k)]
        if not todo:
            continue
        
        log.info(f"  批量: {len(todo)} 集播客")
        
        results = await asyncio.gather(*[generate_podcast_episode(t, chapters) for t, _ in todo])
        
        for (t, k), (ep, tokens) in zip(todo, results):
            episodes.append(ep)
            total_tokens += tokens
            mark_done("podcast", k)
            
            # 单集上传
            safe_title = re.sub(r'[^a-zA-Z0-9_一-龥]', '', t[0][:20])
            await r2_upload_text(f"podcast/ep{i//5}_{safe_title}.json", json.dumps(ep, ensure_ascii=False))
            log.info(f"    ✅ {t[0][:30]}... (~{tokens} tokens)")
        
        await asyncio.sleep(RATE_LIMIT_DELAY * 2)  # 播客生成更重，多等一会
    
    if episodes:
        # 生成总目录
        toc = f"# 🎙️ 鲲鹏志·边角聊 - 播客目录\n\n共 {len(episodes)} 集\n\n"
        for ep in episodes:
            toc += f"- {ep['title']}\n"
        await r2_upload_text("podcast/TOC.md", toc)
        
        log.info(f"\n📊 管线4: {len(episodes)} 集播客, ~{total_tokens:,} tokens")
    
    return total_tokens


# ═══════════════════════════════════════════════════
# 管线 5: 辩论批量生成 (多样风格)
# ═══════════════════════════════════════════════════

DEBATE_STYLES = [
    "学术严谨型：引用大量历史文献，逻辑严密",
    "激情对抗型：情绪饱满，火力全开",
    "幽默讽刺型：用调侃和反讽推进论点",
    "故事叙述型：用叙事代替说理",
    "数据论证型：用数据和逻辑说话",
    "哲学思辨型：上升到文明和人性层面",
]

TOPICS = {
    "1": {"title": "白貂皮大衣：全球贸易网络的铁证 vs 过度诠释",
          "pro": "白貂皮大衣是嚈哒帝国与东北亚保持联系的铁证",
          "con": "白貂皮大衣是转手贸易的结果，族群记忆是过度诠释"},
    "2": {"title": "木兰的哥哥：历史真相 vs 叙事虚构",
          "pro": "木兰无长兄的真正含义是长兄参加大同流亡军团西征",
          "con": "木兰无长兄是文学修辞，强行关联是过度解读"},
    "3": {"title": "产权分割理论：安史之乱的经济学本质",
          "pro": "安史之乱=大股东收购母公司，产权理论是利器",
          "con": "用企业并购解释安史之乱是削足适履"},
}

DEBATE_ROLES = [
    ("正方一辩", "开篇立论"), ("反方一辩", "开篇立论"),
    ("正方二辩", "驳论"), ("反方二辩", "驳论"),
    ("正方三辩", "自由辩论"), ("反方三辩", "自由辩论"),
    ("正方四辩", "总结陈词"), ("反方四辩", "总结陈词"),
]


async def generate_debate(topic_id: str, style: str, chapters: List[Dict]) -> Tuple[Dict, int]:
    """生成一场完整辩论"""
    t = TOPICS[topic_id]
    total_tokens = 0
    
    # 收集相关原文
    context_parts = []
    for ch in chapters[:15]:
        context_parts.append(f"## {ch['book']}/{ch['chapter']}\n\n{ch['content'][:1500]}")
    book_content = "\n\n".join(context_parts)
    
    # 教练策略
    pro_strat, ps_tokens = await llm_stream_burn(f"""
风格：{style}
辩题：{t['title']}
正方：{t['pro']}

请写出正方教练的赛前策略（2000字以上），包含：
1. 核心论点架构
2. 每个辩手分工
3. 对方可能的攻击点
4. 关键论据引用

原文参考：
{book_content[:4000]}
""")
    total_tokens += ps_tokens
    
    con_strat, cs_tokens = await llm_stream_burn(f"""
风格：{style}
辩题：{t['title']}
反方：{t['con']}

请写出反方教练的赛前策略（2000字以上），包含：
1. 核心论点架构
2. 每个辩手分工
3. 对方可能的攻击点
4. 关键论据引用

原文参考：
{book_content[:4000]}
""")
    total_tokens += cs_tokens
    
    # 辩论全文
    history = ""
    for role, stage in DEBATE_ROLES:
        side = "正方" if "正方" in role else "反方"
        stance = t["pro"] if "正方" in role else t["con"]
        coach = pro_strat if "正方" in role else con_strat
        
        prev = ""
        if history.strip():
            prev = f"\n上一位发言：{history[-1500:]}\n"
        
        speech, sp_tokens = await llm_stream_burn(f"""
风格：{style}
角色：{role}（{stage}）
阵营：{side}
立场：{stance}

教练策略参考：{coach[:1000]}
{prev}

写一段辩论发言（500-800字），以「{role}：」开头。引用历史依据。
""")
        total_tokens += sp_tokens
        history += f"\n\n【{role}】\n{speech}"
    
    return {
        "topic_id": topic_id,
        "topic_title": t['title'],
        "style": style,
        "pro_strategy": pro_strat,
        "con_strategy": con_strat,
        "transcript": history,
    }, total_tokens


async def pipeline_5_debates(chapters: List[Dict]):
    """批量辩论 - 3×6=18场"""
    log.info("=" * 60)
    log.info("🚀 管线 5: 辩论批量生成 (18场)")
    log.info("=" * 60)
    
    total_tokens = 0
    debates = []
    
    for topic_id in ["1", "2", "3"]:
        for style in DEBATE_STYLES:
            key = f"debate/{topic_id}/{style[:4]}"
            if is_done("debate", key):
                continue
            
            log.info(f"  辩题{topic_id} [{style[:15]}...]")
            
            debate, tokens = await generate_debate(topic_id, style, chapters)
            debates.append(debate)
            total_tokens += tokens
            mark_done("debate", key)
            
            # 单场上传
            safe_style = re.sub(r'[^a-zA-Z0-9_]', '', style[:10])
            await r2_upload_text(f"debates/topic{topic_id}_{safe_style}.json",
                                json.dumps(debate, ensure_ascii=False))
            log.info(f"    ✅ (~{tokens} tokens)")
            
            await asyncio.sleep(RATE_LIMIT_DELAY)
    
    if debates:
        log.info(f"\n📊 管线5: {len(debates)} 场辩论, ~{total_tokens:,} tokens")
    
    return total_tokens


# ═══════════════════════════════════════════════════
# 管线 6: Q&A 语料库 + 教学讨论指南
# ═══════════════════════════════════════════════════

async def generate_qa_pairs(ch: Dict) -> Tuple[List[Dict], int]:
    """从一个章节生成 Q&A 对话对"""
    prompt = f"""根据以下章节内容，生成 10 个高质量的 Q&A 对话对。
每个 Q 应该是一个有深度的问题，A 应该是详细的回答（100-200字）。

章节：{ch['book']} - {ch['chapter']}

原文：
{ch['content'][:5000]}

格式（每行一个 JSON）：
{{"q": "问题", "a": "回答"}}

问题要有讨论价值，不要问事实性问题。"""
    
    text, tokens = await llm_burn(prompt)
    
    qa_pairs = []
    for line in text.strip().split('\n'):
        line = line.strip()
        if line.startswith('{') and line.endswith('}'):
            try:
                qa = json.loads(line)
                qa['book'] = ch['book']
                qa['chapter'] = ch['chapter']
                qa_pairs.append(qa)
            except:
                pass
    
    return qa_pairs, tokens


async def generate_discussion_guide(ch: Dict) -> Tuple[Dict, int]:
    """生成教学讨论指南"""
    prompt = f"""根据以下章节内容，生成一份讨论指南（1500字以上）。

章节：{ch['book']} - {ch['chapter']}

原文：
{ch['content'][:5000]}

包含：
1. 本章的核心问题（3-5个）
2. 关键概念解释
3. 可供辩论的论点
4. 跨书关联指引
5. 延伸阅读建议

直接输出："""
    
    text, tokens = await llm_stream_burn(prompt)
    return {
        "book": ch['book'],
        "chapter": ch['chapter'],
        "guide": text,
    }, tokens


async def pipeline_6_qa(chapters: List[Dict]):
    """Q&A + 讨论指南"""
    log.info("=" * 60)
    log.info("🚀 管线 6: Q&A 语料库 + 教学指南")
    log.info("=" * 60)
    
    total_tokens = 0
    all_qa = []
    all_guides = []
    
    for i in range(0, len(chapters), 10):  # 每次10章并发
        batch = chapters[i:i+10]
        
        # Q&A
        qa_keys = [f"qa/{c['book']}/{c['chapter']}" for c in batch]
        qa_todo = [(c, k) for c, k in zip(batch, qa_keys) if not is_done("qa", k)]
        
        if qa_todo:
            log.info(f"  Q&A: {len(qa_todo)} 章")
            qa_results = await asyncio.gather(*[generate_qa_pairs(c) for c, _ in qa_todo])
            for (c, k), (pairs, tokens) in zip(qa_todo, qa_results):
                for p in pairs:
                    p['book'] = c['book']
                    p['chapter'] = c['chapter']
                all_qa.extend(pairs)
                total_tokens += tokens
                mark_done("qa", k)
        
        # 讨论指南
        guide_keys = [f"guide/{c['book']}/{c['chapter']}" for c in batch]
        guide_todo = [(c, k) for c, k in zip(batch, guide_keys) if not is_done("guide", k)]
        
        if guide_todo:
            log.info(f"  讨论指南: {len(guide_todo)} 章")
            guide_results = await asyncio.gather(*[generate_discussion_guide(c) for c, _ in guide_todo])
            for (c, k), (guide, tokens) in zip(guide_todo, guide_results):
                all_guides.append(guide)
                total_tokens += tokens
                mark_done("guide", k)
        
        await asyncio.sleep(RATE_LIMIT_DELAY * 0.5)
    
    if all_qa:
        await r2_upload_text("qa/full_qa_pairs.json", json.dumps(all_qa, ensure_ascii=False))
    if all_guides:
        await r2_upload_text("qa/discussion_guides.json", json.dumps(all_guides, ensure_ascii=False))
    
    log.info(f"\n📊 管线6: {len(all_qa)} Q&A, {len(all_guides)} 指南, ~{total_tokens:,} tokens")
    return total_tokens


async def r2_get(key: str) -> Optional[str]:
    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
        return None
    url = (f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}"
           f"/r2/buckets/{R2_BUCKET}/objects/{key}")
    async with httpx.AsyncClient() as c:
        r = await c.get(url, headers={"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"})
        if r.status_code == 200:
            return r.text
    return None


# ═══════════════════════════════════════════════════
# GitLab CE 推送
# ═══════════════════════════════════════════════════

async def push_to_gitlab():
    """将所有生成内容推送到 GitLab CE"""
    log.info("=" * 60)
    log.info("🚀 推送 GitLab CE")
    log.info("=" * 60)
    
    # 从 R2 下载并推送
    # 播客脚本推送到 podcast/ 目录
    # 辩论推送到 debates/ 目录
    # 分析推送到 analysis/ 目录
    
    # 构建一个 README
    readme = f"""# 🦅 鲲鹏志 · AI 生成内容库

> 生成时间：{datetime.now().isoformat()}
> 模型：{DEBATE_MODEL}
> 通过 liteLLM → Vertex AI

## 内容目录

### 🎙️ 播客脚本（四川话男 + 普通话女）
`podcast/` 目录下

### 🏛️ 辩论实录（18场，6种风格）
`debates/` 目录下

### 📚 章节分析（5种维度）
`analysis/` 目录下

### 🔗 跨书概念关联（{len(CORE_CONCEPTS)} 个概念）
`crossref/` 目录下

### 🧠 知识图谱
`kg/` 目录下

### 💬 Q&A 语料库
`qa/` 目录下

## 生成管线
- Pipeline 1: 知识图谱三元组
- Pipeline 2: 章节深度分析
- Pipeline 3: 跨书概念关联
- Pipeline 4: 播客脚本 🎙️
- Pipeline 5: 辩论批量生成
- Pipeline 6: Q&A + 讨论指南

---
*自动生成，未经人工审核*
"""
    
    await gitlab_push_file("README.md", readme, "chore: auto-generate content library")
    
    # 播客目录
    podcast_toc = """# 🎙️ 鲲鹏志·边角聊

> 男主播（青衣）：四川话
> 女主播（峨眉）：普通话

## 剧集列表
"""
    for i, t in enumerate(PODCAST_TOPICS):
        podcast_toc += f"\n### EP{i+1:02d}: {t[0]}\n- 概念：{'、'.join(t[1])}\n- 角度：{t[2]}\n"
        # 尝试从 R2 获取脚本内容并推送
        safe_title = re.sub(r'[^a-zA-Z0-9_一-龥]', '', t[0][:20])
        key = f"podcast/ep{i//5}_{safe_title}.json"
        content = await r2_get(key)
        if content:
            try:
                data = json.loads(content)
                script_path = f"podcast/EP{i+1:02d}_{safe_title}.md"
                await gitlab_push_file(script_path, data.get("script", ""), f"add podcast EP{i+1:02d}: {t[0]}")
            except:
                pass
    
    await gitlab_push_file("podcast/README.md", podcast_toc, "chore: update podcast TOC")
    log.info("✅ GitLab CE 推送完成")


# ═══════════════════════════════════════════════════
# 主控
# ═══════════════════════════════════════════════════

async def main():
    start_time = time.time()
    log.info("🦅 鲲鹏志 · 夜间薅羊毛管线启动 🐑💰")
    log.info(f"  模型: {DEBATE_MODEL}")
    log.info(f"  Base URL: {OPENAI_BASE_URL}")
    log.info(f"  并发: {MAX_CONCURRENT} 路")
    log.info(f"  目标: 今晚烧掉 $100+")
    log.info("")
    
    chapters = scan_books()
    log.info(f"📚 共 {len(chapters)} 个章节\n")
    
    total_tokens = 0
    
    # 按顺序运行所有管线
    pipelines = [
        ("管线1: 知识图谱", pipeline_1_kg),
        ("管线2: 章节分析", pipeline_2_analysis),
        ("管线3: 跨书概念", pipeline_3_crossref),
        ("管线4: 播客脚本 🎙️", pipeline_4_podcast),
        ("管线5: 辩论批量", pipeline_5_debates),
        ("管线6: Q&A + 指南", pipeline_6_qa),
    ]
    
    for name, func in pipelines:
        log.info(f"\n{'='*60}")
        log.info(f"🏁 启动 {name}")
        log.info(f"{'='*60}")
        try:
            tokens = await func(chapters)
            total_tokens += tokens
            log.info(f"✅ {name} 完成, 累计 {total_tokens:,} tokens")
        except Exception as e:
            log.error(f"❌ {name} 失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 每完成一个管线，保存中间状态
        elapsed = time.time() - start_time
        status = {
            "elapsed_hours": round(elapsed / 3600, 2),
            "total_tokens": total_tokens,
            "estimated_cost": total_tokens / 1_000_000 * 0.26,  # 混合价格
            "pipelines_completed": [n for n, _ in pipelines[:pipelines.index((name, func))+1]],
        }
        await r2_upload_text("batch/status.json", json.dumps(status, ensure_ascii=False))
    
    # 最终报告
    elapsed = time.time() - start_time
    estimated_cost = total_tokens / 1_000_000 * 0.26
    
    log.info("\n" + "=" * 60)
    log.info("🏆 所有管线执行完毕")
    log.info("=" * 60)
    log.info(f"\n⏱️  耗时: {elapsed/3600:.1f} 小时")
    log.info(f"💰 总 Token: {total_tokens:,}")
    log.info(f"💰 估算成本: ${estimated_cost:.2f}")
    
    # 生成最终报告
    report = f"""# 🦅 鲲鹏志 · 夜间批处理报告

## 执行信息
- 时间：{datetime.now().isoformat()}
- 模型：{DEBATE_MODEL}
- 耗时：{elapsed/3600:.1f} 小时
- 并发：{MAX_CONCURRENT} 路

## 生成内容
- 📊 知识图谱三元组（Pipeline 1）
- 📚 章节深度分析（Pipeline 2）
- 🔗 跨书概念关联（Pipeline 3）
- 🎙️ 播客脚本 {len(PODCAST_TOPICS)} 集（Pipeline 4）
- 🏛️ 辩论全文 18 场（Pipeline 5）
- 💬 Q&A 语料库 + 教学指南（Pipeline 6）

## 费用
- 总 Token 消耗：{total_tokens:,}
- 估算成本：${estimated_cost:.2f}
- 模型单价：Input $0.15/1M, Output $0.60/1M

## 产物位置
- R2: rag/ 目录下各子目录
- GitLab CE: podcast/ 目录
"""
    await r2_upload_text("batch/final_report.md", report)
    
    # 尝试推送到 GitLab CE
    try:
        await push_to_gitlab()
    except Exception as e:
        log.warning(f"GitLab CE 推送失败: {e}")
    
    log.info(f"\n📝 最终报告已保存到 R2: batch/final_report.md")
    log.info(f"💵 预计烧掉: ${estimated_cost:.2f}")


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
鲲鹏志 · 大规模批处理管线 💰
==============================
在 3 天内烧光 200+ 美金 GCP 免费额度。
对全部四本书做 4 条并行管线处理：
  ① 知识图谱三元组提取（71 章）
  ② 章节深度分析（71 章 × 3 种分析）
  ③ 跨书核心概念关联分析（100+ 概念）
  ④ 辩论批量生成（3 辩题 × 5 风格 = 15 场）

用法:
  python scripts/batch_processor.py [--pipeline 1|2|3|4|all] [--resume]

环境变量:
  OPENAI_BASE_URL, OPENAI_API_KEY, DEBATE_MODEL
  CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN (for R2 storage)
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
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(message)s")
log = logging.getLogger("batch")

# ─── 配置 ─────────────────────────────────────────
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:4000/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-47318")
DEBATE_MODEL = os.getenv("DEBATE_MODEL", "gemini-2.5-flash")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
R2_BUCKET = os.getenv("R2_BUCKET", "kunpengzhi-tts")
R2_PUBLIC_BASE = os.getenv("R2_PUBLIC_BASE", "https://kunpengzhi-debate.seekkey.eu.org")

BOOKS_DIR = os.getenv("KUNPENGZHI_BOOK_PATH", "/home/ben/kunpengzhi")
ON_HEROKU = os.getenv("DYNO") is not None

# Token 价格估算 (gemini-2.5-flash via Vertex AI)
# 实际价格 ~$0.15/1M input, $0.60/1M output
# 我们保守估算用满额度
COST_PER_1M_INPUT = 0.15
COST_PER_1M_OUTPUT = 0.60

# 进度跟踪文件
PROGRESS_FILE = "/tmp/batch_progress.json"

# ─── LLM Client ──────────────────────────────────
import openai

client = openai.AsyncOpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)


async def llm_call(prompt: str, system: str = "", max_tokens: int = 2048, timeout: int = 120) -> str:
    """调用 LLM 并返回文本"""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    resp = await client.chat.completions.create(
        model=DEBATE_MODEL,
        messages=messages,
        max_tokens=max_tokens,
        timeout=timeout,
    )
    return resp.choices[0].message.content


async def llm_call_stream(prompt: str, system: str = "") -> str:
    """流式调用的非流式版本，用于长文本生成"""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    stream = await client.chat.completions.create(
        model=DEBATE_MODEL,
        messages=messages,
        stream=True,
        timeout=180,
    )
    
    result = ""
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
            result += chunk.choices[0].delta.content
    return result


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
    return await r2_upload(key, text.encode("utf-8"))


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


# ─── 书籍扫描 ────────────────────────────────────

def scan_books() -> List[Dict]:
    """扫描四本书的所有章节"""
    chapters = []
    book_dirs = ["牧人记", "双约记", "牧兰记", "牧月记"]
    
    for book in book_dirs:
        book_path = os.path.join(BOOKS_DIR, book)
        if not os.path.isdir(book_path):
            log.warning(f"书籍目录不存在: {book_path}")
            continue
        
        for fname in sorted(os.listdir(book_path)):
            if fname.endswith(".md") and not fname.startswith("."):
                fpath = os.path.join(book_path, fname)
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                chapters.append({
                    "book": book,
                    "chapter": fname,
                    "path": fpath,
                    "content": content,
                    "length": len(content),
                })
                log.info(f"  📖 {book}/{fname} ({len(content)} chars)")
    
    log.info(f"\n总计扫描 {len(chapters)} 个章节")
    return chapters


# ─── 进度管理 ────────────────────────────────────

def load_progress() -> Dict:
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"pipeline_1": [], "pipeline_2": [], "pipeline_3": [], "pipeline_4": []}


def save_progress(progress: Dict):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════
# 管线 1: 知识图谱三元组提取
# ═══════════════════════════════════════════════════

async def pipeline_1_kg(chapters: List[Dict], resume: bool = False) -> Dict:
    """
    对每个章节提取知识图谱三元组。
    每章调用 LLM 提取: 实体、关系、上下文引用。
    """
    log.info("=" * 60)
    log.info("🚀 管线 1: 知识图谱三元组提取")
    log.info("=" * 60)
    
    progress = load_progress()
    done_chapters = set(progress.get("pipeline_1", []))
    
    all_triples = []
    stats = {"chapters_processed": 0, "total_triples": 0, "total_tokens": 0}
    
    for ch in chapters:
        ch_id = f"{ch['book']}/{ch['chapter']}"
        if resume and ch_id in done_chapters:
            log.info(f"  ⏭️ 跳过已完成: {ch_id}")
            continue
        
        log.info(f"  🔄 处理: {ch_id} ({ch['length']} chars)")
        
        # 如果章节太长，分段处理
        content = ch['content']
        if len(content) > 8000:
            # 分段落处理
            paragraphs = [p for p in content.split('\n\n') if len(p.strip()) > 50]
            segments = []
            current = []
            current_len = 0
            for p in paragraphs:
                if current_len + len(p) > 6000:
                    segments.append('\n\n'.join(current))
                    current = [p]
                    current_len = len(p)
                else:
                    current.append(p)
                    current_len += len(p)
            if current:
                segments.append('\n\n'.join(current))
        else:
            segments = [content]
        
        chapter_triples = []
        for seg_idx, seg in enumerate(segments):
            prompt = f"""从以下文本中提取所有实体-关系-实体三元组。

文本内容（{ch['book']} - {ch['chapter']}，第 {seg_idx+1}/{len(segments)} 段）：

{seg[:6000]}

请提取所有重要的实体关系，格式如下（每行一个 JSON）：
{{"subject": "实体A", "relation": "关系类型", "object": "实体B", "context": "原文片段"}}

关系类型使用以下分类之一：
- ATTACK / ALLY / SUCCEED / REPLACE / INHERIT / TRADE / MARRY / 
  LEAD / SERVE / OPPOSE / FOUND / DESTROY / MIGRATE / BELIEVE / CREATE / 
  BELONG_TO / LOCATED_IN / PART_OF / REFER_TO / SYMBOLIZE

要求：
1. 只提取文本中明确提到的关系
2. subject 和 object 必须是文本中的具体实体名称（人物名、地名、事件名、概念名）
3. context 用原文中的原句（最多 100 字）
4. 输出纯 JSON Lines，不要其他文字

提取的三元组："""
            
            try:
                result = await llm_call(prompt, max_tokens=4096, timeout=180)
                # 解析结果
                for line in result.strip().split('\n'):
                    line = line.strip()
                    if line.startswith('{') and line.endswith('}'):
                        try:
                            triple = json.loads(line)
                            triple['book'] = ch['book']
                            triple['chapter'] = ch['chapter']
                            chapter_triples.append(triple)
                        except json.JSONDecodeError:
                            pass
                
                # Token 估算
                stats['total_tokens'] += len(seg) + len(result)
                
            except Exception as e:
                log.error(f"    ❌ 提取失败: {e}")
                await asyncio.sleep(5)
        
        all_triples.extend(chapter_triples)
        stats['chapters_processed'] += 1
        stats['total_triples'] += len(chapter_triples)
        
        log.info(f"    ✅ 提取 {len(chapter_triples)} 个三元组（累计 {stats['total_triples']}）")
        
        # 每 5 章上传一次中间结果
        if stats['chapters_processed'] % 5 == 0:
            await r2_upload_text(
                f"kg/triples_intermediate_{stats['chapters_processed']}.json",
                json.dumps(all_triples, ensure_ascii=False, indent=2)
            )
        
        # 记录进度
        done_chapters.add(ch_id)
        progress["pipeline_1"] = list(done_chapters)
        save_progress(progress)
        
        # 延迟避免限流
        await asyncio.sleep(1)
    
    # 最终上传
    if all_triples:
        await r2_upload_text(
            "kg/triples_full.json",
            json.dumps(all_triples, ensure_ascii=False, indent=2)
        )
        
        # 构建实体索引
        entities = set()
        for t in all_triples:
            entities.add(t['subject'])
            entities.add(t['object'])
        
        entity_index = {
            "total_entities": len(entities),
            "total_triples": len(all_triples),
            "entities": sorted(list(entities)),
            "relation_types": list(set(t['relation'] for t in all_triples)),
        }
        await r2_upload_text("kg/entity_index.json", json.dumps(entity_index, ensure_ascii=False, indent=2))
        
        log.info(f"\n📊 管线 1 完成:")
        log.info(f"   实体数: {len(entities)}")
        log.info(f"   三元组: {len(all_triples)}")
        log.info(f"   估算 Token: {stats['total_tokens']}")
        log.info(f"   估算成本: ${stats['total_tokens'] / 1_000_000 * (COST_PER_1M_INPUT + COST_PER_1M_OUTPUT) / 2:.2f}")
    
    return stats


# ═══════════════════════════════════════════════════
# 管线 2: 章节深度分析
# ═══════════════════════════════════════════════════

ANALYSIS_PROMPTS = {
    "summary": """请为以下章节生成一份全面的中文摘要（1000-1500字）：
- 本章核心事件/论点
- 主要人物及其作用
- 历史背景和上下文
- 在整本书中的位置和意义

章节：{book} - {chapter}

内容：
{content[:5000]}""",

    "arguments": """请分析以下章节中出现的核心论点/争论点（800-1000字）：
- 本章提出了哪些核心观点或历史论断？
- 支持这些观点的证据是什么？
- 可能存在哪些反驳角度？
- 这些论点在整个鲲鹏志体系中与哪些其他章节形成呼应或矛盾？

章节：{book} - {chapter}

内容：
{content[:5000]}""",

    "position": """请分析以下章节在《鲲鹏志》整个宏大叙事中的结构位置（800-1000字）：
- 本章在四本书（牧人记、双约记、牧兰记、牧月记）的总体叙事中处于什么位置？
- 它连接了哪些前后章节或事件？
- 它对理解鲲鹏志的核心主题（文明冲突、历史重构、身份认同等）有何贡献？
- 如果有一张"鲲鹏志叙事地图"，这个章节应该放在哪里？

章节：{book} - {chapter}

内容：
{content[:5000]}""",
}


async def pipeline_2_analysis(chapters: List[Dict], resume: bool = False) -> Dict:
    """
    对每个章节生成 3 种深度分析。
    """
    log.info("=" * 60)
    log.info("🚀 管线 2: 章节深度分析")
    log.info("=" * 60)
    
    progress = load_progress()
    done_keys = set(progress.get("pipeline_2", []))
    
    stats = {"chapters_processed": 0, "total_analyses": 0, "total_tokens": 0}
    all_analyses = []
    
    for ch in chapters:
        for analysis_type in ["summary", "arguments", "position"]:
            key = f"{ch['book']}/{ch['chapter']}/{analysis_type}"
            if resume and key in done_keys:
                log.info(f"  ⏭️ 跳过已完成: {key}")
                continue
            
            log.info(f"  🔄 分析: {ch['book']}/{ch['chapter']} [{analysis_type}]")
            
            prompt = ANALYSIS_PROMPTS[analysis_type].format(
                book=ch['book'], chapter=ch['chapter'], content=ch['content']
            )
            
            try:
                result = await llm_call_stream(prompt)
                
                analysis = {
                    "book": ch['book'],
                    "chapter": ch['chapter'],
                    "type": analysis_type,
                    "content": result,
                    "timestamp": datetime.now().isoformat(),
                }
                all_analyses.append(analysis)
                stats['total_analyses'] += 1
                stats['total_tokens'] += len(ch['content']) + len(result)
                
                log.info(f"    ✅ 完成 ({len(result)} chars)")
                
            except Exception as e:
                log.error(f"    ❌ 失败: {e}")
                await asyncio.sleep(5)
                continue
            
            # 每 10 个分析保存一次
            if stats['total_analyses'] % 10 == 0:
                await r2_upload_text(
                    f"analysis/analyses_intermediate_{stats['total_analyses']}.json",
                    json.dumps(all_analyses, ensure_ascii=False, indent=2)
                )
            
            # 记录进度
            done_keys.add(key)
            progress["pipeline_2"] = list(done_keys)
            save_progress(progress)
            
            await asyncio.sleep(1.5)  # 限流
        
        stats['chapters_processed'] += 1
    
    # 最终上传
    if all_analyses:
        await r2_upload_text(
            "analysis/full_analyses.json",
            json.dumps(all_analyses, ensure_ascii=False, indent=2)
        )
        
        log.info(f"\n📊 管线 2 完成:")
        log.info(f"   分析数: {len(all_analyses)}")
        log.info(f"   估算 Token: {stats['total_tokens']}")
    
    return stats


# ═══════════════════════════════════════════════════
# 管线 3: 跨书核心概念关联分析
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
    "天文历法", "医学", "兵法", "外交使节", "和亲政策",
    "质子制度", "朝贡体系", "羁縻政策", "屯田", "盐铁专卖",
]


async def pipeline_3_crossref(chapters: List[Dict], resume: bool = False) -> Dict:
    """
    对 50+ 个核心概念进行跨书关联分析。
    """
    log.info("=" * 60)
    log.info("🚀 管线 3: 跨书核心概念关联分析")
    log.info("=" * 60)
    
    progress = load_progress()
    done_concepts = set(progress.get("pipeline_3", []))
    
    stats = {"concepts_processed": 0, "total_tokens": 0}
    all_reports = []
    
    for concept in CORE_CONCEPTS:
        if resume and concept in done_concepts:
            log.info(f"  ⏭️ 跳过已完成: {concept}")
            continue
        
        log.info(f"  🔄 分析概念: {concept}")
        
        # 收集所有章节中包含该概念的片段
        mentions = []
        for ch in chapters:
            idx = ch['content'].find(concept)
            if idx >= 0:
                start = max(0, idx - 200)
                end = min(len(ch['content']), idx + len(concept) + 300)
                context = ch['content'][start:end]
                mentions.append({
                    "book": ch['book'],
                    "chapter": ch['chapter'],
                    "context": context.replace('\n', ' ')[:500],
                })
        
        if not mentions:
            log.info(f"    ⚠️ 未找到提及，跳过")
            done_concepts.add(concept)
            progress["pipeline_3"] = list(done_concepts)
            save_progress(progress)
            continue
        
        # 生成跨书关联报告
        mentions_text = "\n\n".join([
            f"[{m['book']}/{m['chapter']}] {m['context']}"
            for m in mentions[:10]  # 最多 10 个上下文
        ])
        
        prompt = f"""概念：{concept}

该概念在《鲲鹏志》四本书中的出现情况如下（共 {len(mentions)} 处提及，展示前 10 处）：

{mentions_text}

请生成一份跨书关联分析报告（800-1200字）：
1. **分布概览**：这个概念在哪些书的哪些章节出现？密度如何？
2. **含义演变**：在不同的书中，这个概念的含义有无变化或深化？
3. **跨书关联**：这个概念连接了哪些不同书中的叙事线？
4. **叙事地位**：这个概念在整个鲲鹏志宇宙中扮演什么角色？
5. **辩论价值**：这个概念适合作为什么辩题的切入点？为什么？"""

        try:
            result = await llm_call_stream(prompt)
            
            report = {
                "concept": concept,
                "mention_count": len(mentions),
                "books_covered": list(set(m['book'] for m in mentions)),
                "chapters_covered": list(set(m['chapter'] for m in mentions)),
                "analysis": result,
                "timestamp": datetime.now().isoformat(),
            }
            all_reports.append(report)
            stats['concepts_processed'] += 1
            stats['total_tokens'] += len(prompt) + len(result)
            
            log.info(f"    ✅ 完成 ({len(result)} chars, {len(mentions)} 处提及)")
            
        except Exception as e:
            log.error(f"    ❌ 失败: {e}")
            await asyncio.sleep(5)
            continue
        
        # 每 10 个概念保存一次
        if stats['concepts_processed'] % 10 == 0:
            await r2_upload_text(
                f"crossref/concepts_intermediate_{stats['concepts_processed']}.json",
                json.dumps(all_reports, ensure_ascii=False, indent=2)
            )
        
        # 记录进度
        done_concepts.add(concept)
        progress["pipeline_3"] = list(done_concepts)
        save_progress(progress)
        
        await asyncio.sleep(1)
    
    # 最终上传
    if all_reports:
        await r2_upload_text(
            "crossref/full_concept_reports.json",
            json.dumps(all_reports, ensure_ascii=False, indent=2)
        )
        
        log.info(f"\n📊 管线 3 完成:")
        log.info(f"   概念数: {len(all_reports)}")
        log.info(f"   估算 Token: {stats['total_tokens']}")
    
    return stats


# ═══════════════════════════════════════════════════
# 管线 4: 辩论批量生成
# ═══════════════════════════════════════════════════

DEBATE_STYLES = [
    "学术严谨型",
    "激情对抗型",
    "幽默讽刺型", 
    "故事叙述型",
    "数据论证型",
]

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
    "正方一辩": "【乾 ☰ · 吕洞宾 —— 鹊桥仙】一柄纯阳宝剑，寒芒乍现，辞却九重天阙。人间自古情难尽，斩不绝、红尘恩怨。醉扶吕祖，清吟太白，试问纯阳生灭。道心点破鹊桥边，化作了、清风明月。",
    "反方一辩": "【坤 ☷ · 何仙姑 —— 卷珠帘】手执碧水青莲步玉沙。云散处、现仙家。不染红尘半点，珠帘高卷，缥缈看流霞。弱水三千空浪迹。心似月、净无瑕。一缕香风归去，高唐梦醒，独坐守瑶华。",
    "正方二辩": "【艮 ☶ · 张果老 —— 临江仙】倒骑毛驴江渚上，朝行碧海苍梧。手扣通玄渔鼓道情孤。古今多少事，盲眼看虚无。莫问老翁年几许，曾陪尧舜双枯。冷眼公卿尽泥涂。乾坤装入壳，一杖任徐驱。",
    "反方二辩": "【兑 ☱ · 韩湘子 —— 苏幕遮】紫金箫，清怨起。声振灵樾，音动微茫里。碧海苍梧飞仙履。一曲横吹，截断江河水。少年郎，心不死。踏遍群山，笑看红尘死。万古沧桑皆入耳。渔鼓声沉，唯有仙音在。",
    "正方三辩": "【离 ☲ · 汉钟离 —— 一剪梅】手摇芭蕉宝扇夜气清。急鼓初催，乐奏公卿。满堂金翠转头空，大汉将军，解甲归蓬。一展神风雾隐腾。莫问流光，冷眼输赢。任他樱桃红透时，几度春风，老了仙翁。",
    "反方三辩": "【坎 ☵ · 蓝采和 —— 西江月】手执叠板花篮，盛来满槛春风。竹板声声戏顽童，醉倒长街乱冢。几点山前疏雨，半宵稻海鸣虫。算来贫贱与公侯，都是南柯一梦。",
    "正方四辩": "【震 ☳ · 曹国舅 —— 虞美人】掌中云阳玉笏何时了？权柄如罂粟。满城开遍美人花，谁解红衣妖艳、是鸩家。雕栏玉砌生尸骨，大梦惊吞吐。老夫脱却大朝衣，洗净满身浮毒、白云归。",
    "反方四辩": "【巽 ☴ · 铁拐李 —— 卜算子】背负太极葫芦落红尘，拐杖惊风雨。莫笑形骸至贱躯，壶里乾坤寓。酒肉任穿肠，不肯栖寒树。待到悬壶济世时，散作山前雾。",
}

DEBATE_ROLES = [
    ("正方一辩", "开篇立论"), ("反方一辩", "开篇立论"),
    ("正方二辩", "驳论"), ("反方二辩", "驳论"),
    ("正方三辩", "自由辩论"), ("反方三辩", "自由辩论"),
    ("正方四辩", "总结陈词"), ("反方四辩", "总结陈词"),
]


async def generate_single_debate(topic_id: str, style: str, book_content: str) -> Dict:
    """生成一场完整辩论"""
    t = TOPICS[topic_id]
    
    # Step 1: 生成教练策略
    pro_strat = await llm_call_stream(f"""
你是一名资深辩论教练，风格是{style}。
辩题：{t['title']}
你的阵营：正方（{t['pro']}）
原文参考：{book_content[:4000]}

请输出一份详细的赛前策略（1500字以上）：
1. 核心论点线
2. 每个辩手的任务分配
3. 对方可能的攻击路线
4. 历史论据引用
""")
    
    con_strat = await llm_call_stream(f"""
你是一名资深辩论教练，风格是{style}。
辩题：{t['title']}
你的阵营：反方（{t['con']}）
原文参考：{book_content[:4000]}

请输出一份详细的赛前策略（1500字以上）：
1. 核心论点线
2. 每个辩手的任务分配
3. 对方可能的攻击路线
4. 历史论据引用
""")
    
    # Step 2: 生成辩论全文
    history = ""
    for role, stage in DEBATE_ROLES:
        side = "正方" if "正方" in role else "反方"
        stance = t["pro"] if "正方" in role else t["con"]
        coach = pro_strat if "正方" in role else con_strat
        poem = SPEAKER_POEMS.get(role, "")
        
        last_section = ""
        if history.strip():
            last_section = f"\n上一位发言：{history.strip()[-1500:]}\n必须直接回应。"
        
        speech = await llm_call_stream(f"""
风格：{style}
角色：{role}（{stage}）
阵营：{side} 立场：{stance}
定场诗：{poem}

原文参考：{book_content[:3000]}
教练策略：{coach[:1500]}
{last_section}

请以第一人称写一段辩论发言（400-600字），以「{role}：」开头。
""")
        
        history += f"\n\n【{role}】（{stage}）\n{speech}"
    
    # Step 3: 议事长总结
    final = await llm_call(f"""
请为这场{style}的辩论写一份议事长总结（300字），概括主要交锋点。
辩题：{t['title']}
辩论全文：{history[:4000]}
""")
    
    return {
        "topic_id": topic_id,
        "topic_title": t['title'],
        "style": style,
        "pro_strategy": pro_strat,
        "con_strategy": con_strat,
        "transcript": history,
        "chair_summary": final,
        "timestamp": datetime.now().isoformat(),
    }


async def pipeline_4_debates(chapters: List[Dict], resume: bool = False) -> Dict:
    """
    批量生成 15 场辩论（3 辩题 × 5 风格）。
    """
    log.info("=" * 60)
    log.info("🚀 管线 4: 辩论批量生成")
    log.info("=" * 60)
    
    # 收集原文上下文（用于辩论引用）
    all_content = "\n\n".join([
        f"## {ch['book']}/{ch['chapter']}\n\n{ch['content'][:2000]}"
        for ch in chapters[:20]  # 取前 20 章作为参考
    ])
    
    progress = load_progress()
    done_keys = set(progress.get("pipeline_4", []))
    
    stats = {"debates_generated": 0, "total_tokens": 0}
    all_debates = []
    
    for topic_id in ["1", "2", "3"]:
        for style in DEBATE_STYLES:
            key = f"{topic_id}/{style}"
            if resume and key in done_keys:
                log.info(f"  ⏭️ 跳过已完成: 辩题{topic_id}-{style}")
                continue
            
            log.info(f"  🔄 生成: 辩题{topic_id} [{style}]")
            
            try:
                debate = await generate_single_debate(topic_id, style, all_content)
                all_debates.append(debate)
                stats['debates_generated'] += 1
                
                # Token 粗略估算
                total_len = (len(debate.get('pro_strategy', '')) + 
                            len(debate.get('con_strategy', '')) +
                            len(debate.get('transcript', '')) +
                            len(debate.get('chair_summary', '')))
                stats['total_tokens'] += total_len
                
                log.info(f"    ✅ 完成 (~{total_len} tokens)")
                
            except Exception as e:
                log.error(f"    ❌ 失败: {e}")
                await asyncio.sleep(10)
                continue
            
            # 每场都保存中间结果
            await r2_upload_text(
                f"debates/batch_{topic_id}_{style.replace(' ', '_')}.json",
                json.dumps(debate, ensure_ascii=False, indent=2)
            )
            
            # 记录进度
            done_keys.add(key)
            progress["pipeline_4"] = list(done_keys)
            save_progress(progress)
            
            await asyncio.sleep(2)
    
    # 最终上传
    if all_debates:
        await r2_upload_text(
            "debates/batch_all_debates.json",
            json.dumps(all_debates, ensure_ascii=False, indent=2)
        )
        
        log.info(f"\n📊 管线 4 完成:")
        log.info(f"   辩论场数: {len(all_debates)}")
        log.info(f"   估算 Token: {stats['total_tokens']}")
    
    return stats


# ═══════════════════════════════════════════════════
# 主调度器
# ═══════════════════════════════════════════════════

async def run_all(chapters: List[Dict], resume: bool = False):
    """串行运行所有管线（避免 API 限流）"""
    start_time = time.time()
    total_stats = {}
    
    # 管线 1：知识图谱
    log.info("\n" + "=" * 60)
    log.info("🏁 开始管线 1：知识图谱")
    log.info("=" * 60)
    stats1 = await pipeline_1_kg(chapters, resume)
    total_stats['kg'] = stats1
    
    # 管线 2：章节分析
    log.info("\n" + "=" * 60)
    log.info("🏁 开始管线 2：章节深度分析")
    log.info("=" * 60)
    stats2 = await pipeline_2_analysis(chapters, resume)
    total_stats['analysis'] = stats2
    
    # 管线 3：跨书概念分析
    log.info("\n" + "=" * 60)
    log.info("🏁 开始管线 3：跨书核心概念关联")
    log.info("=" * 60)
    stats3 = await pipeline_3_crossref(chapters, resume)
    total_stats['crossref'] = stats3
    
    # 管线 4：辩论批量生成
    log.info("\n" + "=" * 60)
    log.info("🏁 开始管线 4：辩论批量生成")
    log.info("=" * 60)
    stats4 = await pipeline_4_debates(chapters, resume)
    total_stats['debates'] = stats4
    
    elapsed = time.time() - start_time
    
    # 最终报告
    log.info("\n" + "=" * 60)
    log.info("🏆 所有管线执行完毕")
    log.info("=" * 60)
    log.info(f"\n⏱️  总耗时: {elapsed/3600:.1f} 小时")
    log.info(f"\n📊 汇总:")
    log.info(f"  管线 1 (知识图谱): {stats1.get('total_triples', 0)} 个三元组")
    log.info(f"  管线 2 (章节分析): {stats2.get('total_analyses', 0)} 篇分析")
    log.info(f"  管线 3 (概念关联): {stats3.get('concepts_processed', 0)} 个概念")
    log.info(f"  管线 4 (辩论批量): {stats4.get('debates_generated', 0)} 场辩论")
    
    total_tokens = sum(
        s.get('total_tokens', 0) for s in total_stats.values()
    )
    estimated_cost = total_tokens / 1_000_000 * (COST_PER_1M_INPUT + COST_PER_1M_OUTPUT) / 2
    log.info(f"\n💰 总估算 Token: {total_tokens:,}")
    log.info(f"💰 总估算成本: ${estimated_cost:.2f}")
    
    # 生成最终报告并上传
    report = f"""# 🦅 鲲鹏志 · 批处理执行报告

## 执行时间
{datetime.now().isoformat()}

## 耗时
{elapsed/3600:.1f} 小时

## 管线结果
### 1️⃣ 知识图谱
- 三元组: {stats1.get('total_triples', 0)}
- 估算 Token: {stats1.get('total_tokens', 0):,}

### 2️⃣ 章节深度分析
- 分析篇数: {stats2.get('total_analyses', 0)}
- 章节数: {stats2.get('chapters_processed', 0)}
- 估算 Token: {stats2.get('total_tokens', 0):,}

### 3️⃣ 跨书概念关联
- 概念数: {stats3.get('concepts_processed', 0)}
- 估算 Token: {stats3.get('total_tokens', 0):,}

### 4️⃣ 辩论批量生成
- 辩论场数: {stats4.get('debates_generated', 0)}
- 估算 Token: {stats4.get('total_tokens', 0):,}

## 费用
- 总估算 Token: {total_tokens:,}
- 总估算成本: ${estimated_cost:.2f}
"""
    await r2_upload_text("batch/report_final.md", report)
    log.info(f"\n📝 最终报告已上传到 R2: batch/report_final.md")


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="鲲鹏志批量处理管线")
    parser.add_argument("--pipeline", choices=["1", "2", "3", "4", "all"], default="all",
                       help="选择要运行的管线")
    parser.add_argument("--resume", action="store_true",
                       help="从上次中断处继续")
    args = parser.parse_args()
    
    log.info("🦅 鲲鹏志 · 大规模批处理管线启动")
    log.info(f"  模型: {DEBATE_MODEL}")
    log.info(f"  Base URL: {OPENAI_BASE_URL}")
    log.info(f"  书籍目录: {BOOKS_DIR}")
    log.info(f"  Resume: {args.resume}")
    log.info("")
    
    chapters = scan_books()
    if not chapters:
        log.error("未找到任何章节！")
        sys.exit(1)
    
    if args.pipeline == "all":
        await run_all(chapters, resume=args.resume)
    else:
        pipelines = {
            "1": ("知识图谱", pipeline_1_kg),
            "2": ("章节分析", pipeline_2_analysis),
            "3": ("概念关联", pipeline_3_crossref),
            "4": ("辩论生成", pipeline_4_debates),
        }
        name, func = pipelines[args.pipeline]
        log.info(f"\n🏁 运行管线 {args.pipeline}: {name}")
        stats = await func(chapters, resume=args.resume)
        log.info(f"\n✅ 管线 {args.pipeline} 完成: {stats}")


if __name__ == "__main__":
    asyncio.run(main())

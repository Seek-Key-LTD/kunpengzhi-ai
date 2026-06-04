#!/usr/bin/env python3
"""
鲲鹏志 · Checkpoint Runner
==========================
与 GitLab Runner 配合，每次调用只处理一个批次（5章），
用 progress.json 做存档点，断点续传。

用法:
  python3 scripts/checkpoint_runner.py --mode kg --batch-size 5
  python3 scripts/checkpoint_runner.py --mode analysis --batch-size 5
  python3 scripts/checkpoint_runner.py --mode all  # 自动走完所有管线
  python3 scripts/checkpoint_runner.py --status    # 只看进度
"""

import os, sys, json, asyncio, logging, time, re
from datetime import datetime
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s - checkpoint - %(message)s")
log = logging.getLogger("checkpoint")

# ─── 路径 ─────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
PROGRESS_FILE = OUTPUTS_DIR / "batch" / "progress.json"

# 4 本书的扫描逻辑
BOOK_DIRS = [
    PROJECT_ROOT.parent / "kunpengzhi" / "牧人记",
    PROJECT_ROOT.parent / "kunpengzhi" / "牧兰记",
    PROJECT_ROOT.parent / "kunpengzhi" / "双约记",
    PROJECT_ROOT.parent / "kunpengzhi" / "牧月记",
]

# ─── 进度管理 ─────────────────────────────────────

def load_progress() -> dict:
    """加载进度文件，不存在则初始化"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    # 初始化为空进度
    chapters = _scan_chapters()
    return {
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "kg_remaining": chapters[:],   # 待处理章节
        "analysis_remaining": chapters[:],
        "crossref_done": [],
        "podcast_done": [],
        "debate_done": [],
        "qa_done": [],
    }


def save_progress(progress: dict):
    """保存进度"""
    progress["updated_at"] = datetime.now().isoformat()
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)
    log.info(f"💾 存档点已保存 ({len(progress.get('kg_remaining',[]))} 章待处理)")


def _scan_chapters() -> list:
    """扫描所有章节，返回 (书名/章名) 列表"""
    chapters = []
    for book_dir in BOOK_DIRS:
        if book_dir.exists():
            book_name = book_dir.name
            for f in sorted(book_dir.glob("第*章*.md")):
                chapter_name = f.stem
                chapters.append(f"{book_name}/{chapter_name}")
    log.info(f"📚 扫描到 {len(chapters)} 个章节")
    return chapters


def read_chapter_content(chapter_path: str) -> Optional[str]:
    """读取章节内容"""
    book, chapter = chapter_path.split("/", 1)
    for book_dir in BOOK_DIRS:
        if book_dir.name == book:
            for f in book_dir.glob(f"{chapter}.md"):
                return f.read_text(encoding="utf-8")
    return None


# ─── API 调用 ──────────────────────────────────────

async def call_llm(system: str, prompt: str, model: str = None) -> str:
    """调用 litellm proxy"""
    import httpx
    
    base_url = os.getenv("OPENAI_BASE_URL", "http://localhost:4000/v1")
    api_key = os.getenv("OPENAI_API_KEY", "sk-47318")
    model = model or os.getenv("DEBATE_MODEL", "gemini-2.5-flash")
    
    async with httpx.AsyncClient(timeout=300) as client:
        resp = await client.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 8192,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


# ─── 各种管线处理 ──────────────────────────────────

async def process_kg(chapter: str, progress: dict) -> bool:
    """处理一章的知识图谱"""
    content = read_chapter_content(chapter)
    if not content:
        log.warning(f"⚠️  找不到章节: {chapter}")
        return False
    
    try:
        text = await call_llm(
            "你是鲲鹏志的知识图谱构建专家。从章节中提取实体-关系-实体三元组。",
            f"""请从以下章节中提取 5-20 个知识图谱三元组。
格式: JSON 数组，每个元素 {{"s": 主体, "r": 关系, "o": 客体, "c": 上下文片段}}

章节: {chapter}
内容:
{content[:8000]}"""
        )
        
        # 解析 JSON
        triples = json.loads(re.sub(r"^```json\s*|```\s*$", "", text.strip()))
        
        # 保存到文件
        out_dir = OUTPUTS_DIR / "kg" / chapter.split("/")[0]
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{chapter.split('/')[1]}.json"
        with open(out_file, "w") as f:
            json.dump(triples, f, ensure_ascii=False, indent=2)
        
        log.info(f"  ✅ {chapter}: {len(triples)} 个三元组")
        
        # 更新进度
        progress["kg_remaining"].remove(chapter)
        save_progress(progress)
        return True
        
    except Exception as e:
        log.error(f"  ❌ {chapter}: {e}")
        return False


async def process_analysis(chapter: str, progress: dict) -> bool:
    """处理一章的分析"""
    content = read_chapter_content(chapter)
    if not content:
        return False
    
    analysis_types = ["摘要", "核心论点", "历史定位", "人物谱", "时间线"]
    
    try:
        for atype in analysis_types:
            text = await call_llm(
                f"你是鲲鹏志的{atype}分析师。",
                f"""请对以下章节进行「{atype}」分析，300-500字。

章节: {chapter}
内容:
{content[:6000]}"""
            )
            
            # 保存
            out_dir = OUTPUTS_DIR / "analysis" / chapter.split("/")[0] / chapter.split("/")[1]
            out_dir.mkdir(parents=True, exist_ok=True)
            with open(out_dir / f"{atype}.md", "w") as f:
                f.write(f"# {chapter} - {atype}\n\n{text}\n")
            
            log.info(f"  ✅ {chapter}/{atype}")
        
        # 更新进度
        progress["analysis_remaining"].remove(chapter)
        save_progress(progress)
        return True
        
    except Exception as e:
        log.error(f"  ❌ {chapter}: {e}")
        return False


# ─── 主调度 ────────────────────────────────────────

async def run_mode(mode: str, batch_size: int = 5):
    """运行指定模式"""
    progress = load_progress()
    
    if mode == "kg":
        batch = progress["kg_remaining"][:batch_size]
        log.info(f"📊 KG 批次: {len(batch)} 章 (剩余 {len(progress['kg_remaining'])} 章)")
        for chapter in batch:
            await process_kg(chapter, progress)
    
    elif mode == "analysis":
        batch = progress["analysis_remaining"][:batch_size]
        log.info(f"📊 分析批次: {len(batch)} 章 (剩余 {len(progress['analysis_remaining'])} 章)")
        for chapter in batch:
            await process_analysis(chapter, progress)
    
    elif mode == "status":
        print(f"📊 进度状态:")
        print(f"  KG 待处理: {len(progress['kg_remaining'])} 章")
        print(f"  分析待处理: {len(progress['analysis_remaining'])} 章")
        print(f"  已处理 KG: {len(_scan_chapters()) - len(progress['kg_remaining'])} 章")
        processed = _scan_chapters()
        done = len(processed) - len(progress["analysis_remaining"])
        print(f"  已处理分析: {done} 章")
        return
    
    print(f"📊 当前进度: KG={len(_scan_chapters())-len(progress['kg_remaining'])}/{len(_scan_chapters())}, 分析={len(_scan_chapters())-len(progress['analysis_remaining'])}/{len(_scan_chapters())}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="鲲鹏志 Checkpoint Runner")
    parser.add_argument("--mode", choices=["kg", "analysis", "all", "status"], default="status")
    parser.add_argument("--batch-size", type=int, default=5)
    args = parser.parse_args()
    
    if args.mode == "all":
        async def run_all():
            p = load_progress()
            while p["kg_remaining"] or p["analysis_remaining"]:
                if p["kg_remaining"]:
                    await run_mode("kg", args.batch_size)
                if p["analysis_remaining"]:
                    await run_mode("analysis", args.batch_size)
                p = load_progress()
            log.info("🎉 全部完成!")
        asyncio.run(run_all())
    elif args.mode == "status":
        asyncio.run(run_mode("status"))
    else:
        asyncio.run(run_mode(args.mode, args.batch_size))

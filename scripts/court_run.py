#!/usr/bin/env python3
"""
🦅 鲲鹏志 · 《极昼》案 模拟法庭 headless CLI（Event 2）
====================================================
与网页 streamlit_app.py 同源（debate/court_engine.py）：
独立起诉书 → 13 步令牌环庭审 → 统一落盘存档（本地 + MinIO + runs.jsonl）

事件链：
    庭前会议 (pretrial_run.py) → 庭审 (本脚本，--pretrial 注入庭前笔录锚)

用法:
    uv run python scripts/court_run.py
    uv run python scripts/court_run.py --pretrial 擂台存档/擂台-庭前会议-*.md
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from debate.court_engine import SEATS_DICT, RobertTokenRingEngine, ROBERTS_STEPS

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTICLE_PATH = REPO_ROOT / "research" / "极昼.md"


async def main():
    parser = argparse.ArgumentParser(description="《极昼》案模拟法庭 headless（Event 2 庭审）")
    parser.add_argument("--pretrial", default=None, help="庭前会议笔录 md 路径（注入证据固定锚）")
    args = parser.parse_args()

    article_text = ARTICLE_PATH.read_text(encoding="utf-8")
    base_url = os.getenv("OPENAI_BASE_URL", "https://litellm.capitaltrain.cn/v1")
    api_key = os.getenv("OPENAI_API_KEY", "sk-47318")

    from core.archive import open_stream, append_stream, close_stream
    path, filename, ts = open_stream("法庭", "极昼-阜阳中院")

    engine = RobertTokenRingEngine(base_url, api_key, article_text)
    records = []
    models = set()

    if args.pretrial:
        pretrial_md = Path(args.pretrial).read_text(encoding="utf-8")
        print(f"📋 注入庭前会议笔录锚: {Path(args.pretrial).name}")
        append_stream(path, "📋 庭前会议笔录（Event 1 · 固定证据）", pretrial_md)
        engine.add_to_shared_context("judge_chief", pretrial_md, team="pretrial")

    print("⚖️ 步骤 0/12 · 阜阳市检察院独立撰写起诉书...")
    indictment = engine.draft_official_indictment()
    models.add(SEATS_DICT["prosecutor_chief"]["model"])
    print(f"   ✅ 起诉书 {len(indictment)} 字符")
    append_stream(path, "📜 公诉机关独立撰写之起诉书（阜检刑诉〔2026〕88号）", indictment)
    engine.add_to_shared_context("prosecutor_chief", f"【起诉书全景】:\n{indictment}", team="indictment")

    intel_path = REPO_ROOT / "research" / "反方弹药-恶意揣测.md"
    if intel_path.exists():
        intel_text = intel_path.read_text(encoding="utf-8")
        engine.add_to_shared_context(
            "prosecutor_chief", f"【反方内部研判·恶意揣测全景】:\n{intel_text}",
            team="prosecution_intel",
        )
        print("🔍 已注入《反方弹药·恶意揣测》情报（仅公诉席可见）")

    total = len(ROBERTS_STEPS)
    for idx, (seat_key, instruction) in enumerate(ROBERTS_STEPS, 1):
        seat = SEATS_DICT[seat_key]
        models.add(seat["model"])
        print(f"⚖️ 步骤 {idx}/{total + 1} · {seat['role']} ({seat['agent']} @ {seat['node']})...")
        header, content = engine.execute_token_speech(seat_key, instruction)
        records.append((header, content))
        append_stream(path, header, content)
        print(f"   ✅ {len(content)} 字符")

    filename = close_stream(
        path, filename, ts, "法庭", "极昼-阜阳中院",
        {"models": ",".join(sorted(models)), "steps": total + 1, "_steps": engine.steps},
    )

    print(f"\n{'=' * 60}")
    print(f"🎬 模拟法庭落幕 · 共 {len(records)} 席发言 / {sum(len(c) for _, c in records)} 字符")
    print(f"💾 已流式落盘: {filename}")


if __name__ == "__main__":
    asyncio.run(main())

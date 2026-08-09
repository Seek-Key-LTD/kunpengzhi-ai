#!/usr/bin/env python3
"""
🦅 鲲鹏志 · 《极昼》案 庭前会议 headless CLI（Event 1）
======================================================
与庭审 (court_run.py) 构成事件链：
  庭前会议（固定证据/争议焦点/程序决定）→ 庭审（注入庭前笔录锚，仅用固定证据）

用法:
    uv run python scripts/pretrial_run.py
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from debate.court_engine import SEATS_DICT, RobertTokenRingEngine, PRETRIAL_STEPS

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTICLE_PATH = REPO_ROOT / "research" / "极昼.md"


def build_pretrial_md(records: list) -> str:
    lines = [
        "# 🦅 鲲鹏志 · 《极昼》案 庭前会议笔录",
        "**法院**：安徽省阜阳市中级人民法院刑事审判第一庭",
        "**程序**：庭前会议（刑诉法第187条）· 圆桌协商 · 固定证据 / 争议焦点 / 程序决定",
        "**效力**：庭审阶段双方仅能使用本次会议固定之证据",
        "",
        "## 📋 庭前会议记录（Event 1）",
        "",
    ]
    for header, content in records:
        lines += [f"### {header}", "", content, ""]
    return "\n".join(lines)


async def main():
    article_text = ARTICLE_PATH.read_text(encoding="utf-8")
    base_url = os.getenv("OPENAI_BASE_URL", "https://litellm.capitaltrain.cn/v1")
    api_key = os.getenv("OPENAI_API_KEY", "sk-47318")

    engine = RobertTokenRingEngine(base_url, api_key, article_text)
    records = []
    models = set()

    total = len(PRETRIAL_STEPS)
    for idx, (seat_key, instruction) in enumerate(PRETRIAL_STEPS, 1):
        seat = SEATS_DICT[seat_key]
        models.add(seat["model"])
        print(f"📋 庭前会议 {idx}/{total} · {seat['role']}...")
        header, content = engine.execute_plain_speech(seat_key, instruction)
        records.append((header, content))
        print(f"   ✅ {len(content)} 字符")

    transcript = build_pretrial_md(records)

    from core.archive import save_run
    filename = save_run(
        "庭前会议",
        "极昼-阜阳中院",
        transcript,
        {"models": ",".join(sorted(models)), "steps": total, "_steps": engine.steps},
    )

    print(f"\n{'=' * 60}")
    print(f"📋 庭前会议落幕 · 共 {len(records)} 席发言 / {sum(len(c) for _, c in records)} 字符")
    print(f"💾 已落盘: {filename}")
    print(f"🎬 下一步: uv run python scripts/court_run.py --pretrial 擂台存档/{filename}")


if __name__ == "__main__":
    asyncio.run(main())

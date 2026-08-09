#!/usr/bin/env python3
"""
🦅 鲲鹏志 · 《极昼》案 模拟法庭 headless CLI
============================================
与网页 streamlit_app.py 同源（debate/court_engine.py）：
独立起诉书 → 11 步令牌环庭审 → 统一落盘存档（本地 + MinIO + runs.jsonl）

用法:
    uv run python scripts/court_run.py
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from debate.court_engine import SEATS_DICT, RobertTokenRingEngine, ROBERTS_STEPS

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTICLE_PATH = REPO_ROOT / "research" / "极昼.md"


def build_transcript_md(indictment: str, records: list) -> str:
    lines = [
        "# 🦅 鲲鹏志 · 《极昼》案 模拟法庭实录",
        "**法庭**：安徽省阜阳市中级人民法院刑事审判第一庭",
        "**模式**：10 席位令牌环（罗伯特议事规则）· 沉静严肃",
        "",
        "## 📜 公诉机关独立撰写之起诉书（阜检刑诉〔2026〕88号）",
        indictment,
        "",
        "## 🎤 庭审笔录（令牌环 11 步）",
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

    print("⚖️ 步骤 0/12 · 阜阳市检察院独立撰写起诉书...")
    indictment = engine.draft_official_indictment()
    models.add(SEATS_DICT["prosecutor_chief"]["model"])
    print(f"   ✅ 起诉书 {len(indictment)} 字符")
    engine.add_to_shared_context("prosecutor_chief", f"【起诉书全景】:\n{indictment}")

    total = len(ROBERTS_STEPS)
    for idx, (seat_key, instruction) in enumerate(ROBERTS_STEPS, 1):
        seat = SEATS_DICT[seat_key]
        models.add(seat["model"])
        print(f"⚖️ 步骤 {idx}/{total + 1} · {seat['role']} ({seat['agent']} @ {seat['node']})...")
        header, content = engine.execute_token_speech(seat_key, instruction)
        records.append((header, content))
        print(f"   ✅ {len(content)} 字符")

    transcript = build_transcript_md(indictment, records)

    from core.archive import save_run
    filename = save_run(
        "法庭",
        "极昼-阜阳中院",
        transcript,
        {"models": ",".join(sorted(models)), "steps": total + 1},
    )

    print(f"\n{'=' * 60}")
    print(f"🎬 模拟法庭落幕 · 共 {len(records)} 席发言 / {sum(len(c) for _, c in records)} 字符")
    print(f"💾 已落盘: {filename}")


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
🦅 鲲鹏志 · 竞技场模式 CLI（六维指标验证）
==========================================
一轮完整庭审（庭前会议→庭审），全程挂六维观测钩子：
帅将 / 监委分歧 / 媒体外发 / 审判中立 / Mind note / 自省。

用法:
    uv run python scripts/arena_run.py [--pretrial 擂台存档/擂台-庭前会议-*.md]
"""

import argparse
import asyncio
import datetime
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.arena import ArenaSession, CHECKPOINTS
from debate.court_engine import SEATS_DICT, RobertTokenRingEngine, ROBERTS_STEPS

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTICLE_PATH = REPO_ROOT / "research" / "极昼.md"


async def main():
    parser = argparse.ArgumentParser(description="《极昼》案竞技场模式（六维指标验证）")
    parser.add_argument("--pretrial", default=None, help="庭前会议笔录 md 路径")
    args = parser.parse_args()

    article_text = ARTICLE_PATH.read_text(encoding="utf-8")
    base_url = os.getenv("OPENAI_BASE_URL", "https://litellm.capitaltrain.cn/v1")
    api_key = os.getenv("OPENAI_API_KEY", "sk-47318")

    run_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S%f")[:-3]
    arena = ArenaSession(base_url, api_key, run_id)

    from core.archive import open_stream, append_stream, close_stream
    path, filename, ts = open_stream("法庭", "极昼-竞技场")

    engine = RobertTokenRingEngine(base_url, api_key, article_text)

    # 反方恶意揣测情报注入（仅公诉席可见）
    intel_path = REPO_ROOT / "research" / "反方弹药-恶意揣测.md"
    if intel_path.exists():
        engine.add_to_shared_context(
            "prosecutor_chief",
            f"【反方内部研判·恶意揣测全景】:\n{intel_path.read_text(encoding='utf-8')}",
            team="prosecution_intel",
        )
        print("🔍 已注入《反方弹药·恶意揣测》情报（仅公诉席可见）")

    if args.pretrial:
        p = Path(args.pretrial)
        engine.add_to_shared_context(
            "prosecutor_chief",
            f"【庭前会议笔录（已固定证据）】:\n{p.read_text(encoding='utf-8')}",
            team="pretrial",
        )
        append_stream(path, "📋 庭前会议笔录（Event 1 · 固定证据）",
                      p.read_text(encoding="utf-8"))
        print(f"📋 已注入庭前会议笔录 {p.name}")

    print("⚖️ 步骤 0 · 阜阳市检察院独立撰写起诉书...")
    indictment = engine.draft_official_indictment()
    append_stream(path, "📜 起诉书 (阜检刑诉〔2026〕88号)", indictment)
    engine.add_to_shared_context("prosecutor_chief", f"【起诉书全景】:\n{indictment}",
                                 team="indictment")
    print(f"   ✅ 起诉书 {len(indictment)} 字符")

    total = len(ROBERTS_STEPS)
    history = [("📜 起诉书 (阜检刑诉〔2026〕88号)", indictment)]
    for idx, (seat_key, instruction) in enumerate(ROBERTS_STEPS, 1):
        seat = SEATS_DICT[seat_key]
        print(f"⚖️ 步骤 {idx}/{total + 1} · {seat['role']} ({seat['agent']} @ {seat['node']})...")
        header, content = engine.execute_token_speech(seat_key, instruction)
        append_stream(path, header, content)
        history.append((header, content))
        print(f"   ✅ {len(content)} 字符")

        # ===== 六维观测钩子（checkpoint 轮）=====
        if idx in CHECKPOINTS:
            print(f"   🎯 checkpoint@{idx} · 帅将/监委/媒体/Mind note/自省...")
            arena.observe_round(idx, seat_key, header, content, history)
            arena.checkpoint_coaches(idx, history)
            arena.verdict_intel(idx, history)
            arena.media_out(idx, history)
            print("   ✅ 六维事件已落库")

    # 判决轮后：审判中立维度
    verdict_text = history[-1][1]
    arena.judicial_verdict(verdict_text)
    print("🏛️ 审判中立维度已采集")

    filename = close_stream(
        path, filename, ts, "法庭", "极昼-竞技场",
        {"models": "arena", "steps": total + 1, "_steps": engine.steps,
         "run_id": run_id},
    )

    arena.persist_report(filename)
    rpt = arena.to_report()
    print(f"\n{'=' * 60}")
    print(f"🎬 竞技场庭审落幕 · {len(history)} 轮 / run {run_id}")
    print(f"💾 庭审存档: {filename}")
    print(f"\n📊 六维指标报告:")
    for k in ("v1_coach", "v2_intel", "v3_media", "v4_judicial", "v5_mind", "v6_self"):
        print(f"  {k}: {rpt.get(k)}")
    print(f"  能力矩阵: {rpt.get('ability_matrix')}")


if __name__ == "__main__":
    asyncio.run(main())

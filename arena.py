#!/usr/bin/env python3
"""
🦅 鲲鹏志 · 擂台 — 完整脚本
===============================
4v4 辩论赛 + 讲茶大堂评论 + TTS 语音 + HTML 报告

用法:
    python arena.py                    # 选择辩题
    python arena.py 1                  # 直接跑辩题 1
    python arena.py 1 --no-tts         # 跑辩题 1，无语音
    python arena.py --all              # 跑全部 3 个辩题
"""

import asyncio
import os
import sys
from debate.engine import DebateOrchestrator

SAVE_DIR = os.path.join(os.path.dirname(__file__), "擂台存档")


async def run_one(topic_id: str, enable_tts: bool = True):
    """运行一场完整擂台"""
    result = await DebateOrchestrator.run(topic_id, save_dir=SAVE_DIR)

    print(f"\n{'='*60}")
    print(f"🦅 鲲鹏志 · 擂台")
    print(f"辩题: {result['title']}")
    print(f"{'='*60}")
    print(f"\n🎤 辩论 ({len(result['debate'])} 字符)")
    # 打印前10行
    for line in result['debate'].split('\n')[:10]:
        if line.strip():
            print(f"  {line[:80]}")
    print(f"  ...")
    print(f"\n🍵 讲茶大堂 ({len(result['teahouse'])} 字符)")
    for line in result['teahouse'].split('\n')[:5]:
        if line.strip():
            print(f"  {line[:80]}")
    print(f"  ...")
    print(f"\n💾 已保存: {result.get('file', 'N/A')}")
    print()

    return result


async def main():
    # 解析参数
    args = sys.argv[1:]
    no_tts = "--no-tts" in args
    run_all = "--all" in args

    if run_all:
        print("🦅 鲲鹏志 · 全部辩题擂台赛\n")
        for tid in ["1", "2", "3"]:
            await run_one(tid, not no_tts)
        print("🎉 全部完成！")
    else:
        topic_id = args[0] if args and args[0] not in ("--no-tts",) else ""
        if not topic_id:
            print("🦅 鲲鹏志 · 擂台\n")
            for k, v in DebateOrchestrator.run.__wrapped__.__globals__[
                "DebateMatch"
            ].TOPICS.items():
                print(f"  {k}. {v['emoji']} {v['title']}")
            topic_id = input("\n选择辩题 (1/2/3): ").strip() or "1"

        await run_one(topic_id, not no_tts)


if __name__ == "__main__":
    asyncio.run(main())

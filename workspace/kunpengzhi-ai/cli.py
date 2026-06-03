#!/usr/bin/env python3
"""
辩论命令行工具 — Phase1 MVP
用法:
    python cli.py                    # 交互式
    python cli.py 1 --seats 4        # 跑辩题1，4席（2正2反）
    python cli.py 2 --seats 8        # 跑辩题2，8席（4正4反）
    python cli.py 1 --seats 4 --report   # 带评审报告
"""

import asyncio
import argparse
import json
import os
import sys
from pathlib import Path

# 路径配置
REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT))

from core.seats import SEATS, get_pro_seats, get_con_seats
from debate.engine import DebateOrchestrator


TOPICS = {
    "1": {
        "title": "白貂皮大衣=族群记忆的铁证还是过度诠释？",
        "description": "以《牧人记》第8章为依据，评判白貂皮在历史叙事中的证据效力。",
    },
    "2": {
        "title": "木兰无长兄=大同军团西征痕迹还是文学修辞？",
        "description": "以《牧人记》第7章为依据，考证木兰叙事的真实历史背景。",
    },
    "3": {
        "title": "安史之乱=大股东收购母公司还是削足适履？",
        "description": "以《牧人记》第1章为依据，分析安史之乱的经济学解读。",
    },
}


async def run_debate(topic_id: str, num_seats: int = 4, save_report: bool = False):
    topic = TOPICS.get(topic_id)
    if not topic:
        print(f"❌ 未知辩题: {topic_id}")
        print(f"   可用: {list(TOPICS.keys())}")
        return

    pro_seats = get_pro_seats()[:num_seats // 2]
    con_seats = get_con_seats()[:num_seats // 2]
    active_seats = {**dict.fromkeys([s["id"] for s in pro_seats]),
                    **dict.fromkeys([s["id"] for s in con_seats])}

    print(f"\n{'='*60}")
    print(f"🦅 鲲鹏志辩论 · {topic['title']}")
    print(f"{'='*60}")
    print(f"正方 ({len(pro_seats)}席): {', '.join(s['name']+s['gua'] for s in pro_seats)}")
    print(f"反方 ({len(con_seats)}席): {', '.join(s['name']+s['gua'] for s in con_seats)}")
    print(f"描述: {topic['description']}")
    print(f"{'='*60}\n")

    result = await DebateOrchestrator.run(topic_id, save_dir=REPO_ROOT / "debates")
    debate_file = result.get("file")
    print(f"\n✅ 辩论完成，保存在: {debate_file}")

    if save_report:
        report = build_report(topic_id, result)
        report_file = REPO_ROOT / "reports" / f"debate_{topic_id}.html"
        report_file.parent.mkdir(exist_ok=True)
        report_file.write_text(report, encoding="utf-8")
        print(f"📊 评审报告: {report_file}")


def build_report(topic_id: str, debate_result: dict) -> str:
    topic = TOPICS.get(topic_id, {})
    scores = debate_result.get("scores", {})
    debate_text = debate_result.get("debate", "")[:2000]
    teahouse = debate_result.get("teahouse", "")[:1000]

    scores_html = ""
    if scores:
        for seat_id, sc in scores.items():
            total = sc.get("total", 0)
            scores_html += f"""
        <div class="score-card">
            <div class="seat-name">{seat_id}</div>
            <div class="score-bar" style="--pct:{total/150*100:.0f}%"></div>
            <div class="score-detail">
                礼 {sc.get('li',0):.1f} × 乐 {sc.get('yue',0):.1f} × 螺旋 {sc.get('spiral',0):.1f}
                = <strong>{total:.1f}</strong>/150
            </div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>鲲鹏志辩论评审报告 · {topic_id}</title>
<style>
    body{{font-family:'PingFang SC',sans-serif;background:#0a0a0f;color:#e0d9c8;max-width:900px;margin:0 auto;padding:40px 20px}}
    h1{{color:#e0d9c8;border-bottom:1px solid rgba(255,255,255,0.1);padding-bottom:16px}}
    .meta{{color:#888;font-size:0.85rem;margin-bottom:24px}}
    .section{{margin:32px 0}}
    .section h2{{color:#c8b88a;font-size:1rem;letter-spacing:0.1em;margin-bottom:12px}}
    .debate-text{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);
                  border-radius:8px;padding:20px;font-size:0.9rem;line-height:1.8;white-space:pre-wrap}}
    .scores-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px}}
    .score-card{{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);
                  border-radius:6px;padding:16px}}
    .seat-name{{font-size:0.9rem;color:#c8bfa8;margin-bottom:8px}}
    .score-bar{{height:4px;background:rgba(255,255,255,0.1);border-radius:2px;position:relative}}
    .score-bar::after{{content:'';position:absolute;left:0;top:0;height:100%;
                       width:var(--pct);background:linear-gradient(90deg,#ff6b35,#ffd700);
                       border-radius:2px}}
    .score-detail{{margin-top:8px;font-size:0.75rem;color:#777}}
</style>
</head>
<body>
<h1>{topic.get('title', f'辩题 {topic_id}')}</h1>
<div class="meta">鲲鹏志 · 全模态图灵测试² · Phase1</div>

<div class="section">
    <h2>辩论摘要</h2>
    <div class="debate-text">{debate_text}...</div>
</div>

<div class="section">
    <h2>评分结果</h2>
    <div class="scores-grid">{scores_html or '<p style="color:#555">暂无评分数据</p>'}</div>
</div>

<div class="section">
    <h2>讲茶大堂</h2>
    <div class="debate-text">{teahouse}...</div>
</div>
</body>
</html>"""


def interactive():
    print("\n🦅 鲲鹏志辩论系统 · Phase1")
    print(f"可用辩题: {list(TOPICS.keys())}")
    print("示例: python cli.py 1 --seats 4\n")

    while True:
        try:
            choice = input("选择辩题 (1/2/3) 或 q 退出: ").strip()
            if choice.lower() == "q":
                break
            if choice in TOPICS:
                asyncio.run(run_debate(choice, num_seats=4, save_report=True))
            else:
                print(f"无效选择: {choice}")
        except (EOFError, KeyboardInterrupt):
            print("\n退出")
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="鲲鹏志辩论系统")
    parser.add_argument("topic", nargs="?", help="辩题编号 (1/2/3)")
    parser.add_argument("--seats", type=int, default=4, help="席位数量 (默认4)")
    parser.add_argument("--report", action="store_true", help="生成评审报告HTML")
    args = parser.parse_args()

    if args.topic:
        asyncio.run(run_debate(args.topic, num_seats=args.seats, save_report=args.report))
    else:
        interactive()
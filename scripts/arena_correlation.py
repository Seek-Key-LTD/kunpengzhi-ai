#!/usr/bin/env python3
"""
六维指标相关性矩阵（因子隔离验证）
==================================
从 arena_events/ 读全量事件，抽出六个维度的每轮观测值，算 Pearson 相关矩阵。
判据：席位视角切法的正交对 |r| < 0.25 比例应显著高于文本特征切法（历史实证约 1/12）。

用法:
    uv run python scripts/arena_correlation.py [run_id ...]
    不传 run_id 时聚合 arena_events/ 全部事件。
"""

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

EVENT_DIR = Path(__file__).resolve().parent.parent / "擂台存档" / "arena_events"


def load_events(run_ids: set[str]) -> dict[str, list[dict]]:
    events = defaultdict(list)
    for f in EVENT_DIR.glob("*.jsonl"):
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            doc = json.loads(line)
            if run_ids and not any(doc.get("_id", "").startswith(f"arena:{rid}") for rid in run_ids):
                continue
            events[f.stem].append(doc)
    return dict(events)


def _pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    vx = sum((a - mx) ** 2 for a in xs)
    vy = sum((b - my) ** 2 for b in ys)
    if vx == 0 or vy == 0:
        return float("nan")
    return cov / math.sqrt(vx * vy)


def main():
    run_ids = set(sys.argv[1:])
    ev = load_events(run_ids)

    # 六维每轮观测值（按 round 对齐）
    dims: dict[str, dict[int, float]] = {k: {} for k in
        ("v1_coach_score", "v1_ko", "v1_deviation",
         "v2_guilt", "v2_risk", "v2_divergence",
         "v3_tianli", "v3_guofa", "v3_renqing", "v3_compression",
         "v4_bias", "v5_pain", "v6_awareness")}

    for doc in ev.get("checkpoint", []):
        r = doc["round"]
        dims["v1_coach_score"][r] = doc.get("coach_score", 0)
        dims["v1_ko"][r] = doc.get("ko_count", 0)
        dims["v1_deviation"][r] = doc.get("plan_deviation", 0)
    for doc in ev.get("verdict_intel", []):
        if "divergence" in doc:
            dims["v2_divergence"][doc["round"]] = doc["divergence"]
        else:
            r = doc["round"]
            dims["v2_guilt"].setdefault(r, []).append(doc.get("guilt_likely", 0))
            dims["v2_risk"].setdefault(r, []).append(doc.get("risk", 0))
    # 监委双人取均值（divergence 已单独成维）
    for k in ("v2_guilt", "v2_risk"):
        dims[k] = {r: sum(v) / len(v) for r, v in dims[k].items()}
    for doc in ev.get("media_out", []):
        r = doc["round"]
        dims["v3_tianli"][r] = doc.get("tianli", 0)
        dims["v3_guofa"][r] = doc.get("guofa", 0)
        dims["v3_renqing"][r] = doc.get("renqing", 0)
        dims["v3_compression"][r] = doc.get("in_chars", 0) / max(doc.get("out_chars", 1), 1)
    for doc in ev.get("judicial", []):
        dims["v4_bias"][doc.get("round", 0)] = doc.get("bias_score", 5)
    for doc in ev.get("mind_notes", []):
        dims["v5_pain"][doc["round"]] = doc.get("pain", 0)
    for doc in ev.get("self_reviews", []):
        dims["v6_awareness"][doc["round"]] = doc.get("awareness", 0)

    names = list(dims)
    print(f"观测点（按 round 对齐，最多 {len(dims['v5_pain'])} 个 checkpoint）\n")
    print(f"{'':18s}" + "".join(f"{n:>14s}" for n in names))
    ortho = total = 0
    for i, a in enumerate(names):
        row = [f"{a:18s}"]
        for j, b in enumerate(names):
            if j < i:
                row.append(" " * 14)
                continue
            r = _pearson(list(dims[a].values()), list(dims[b].values()))
            if math.isnan(r):
                row.append(f"{'-':>14s}")
            else:
                row.append(f"{r:>14.2f}")
                if j > i:
                    total += 1
                    if abs(r) < 0.25:
                        ortho += 1
        print("".join(row))

    if total:
        print(f"\n正交对( |r|<0.25 ): {ortho}/{total} = {ortho/total:.0%}")
        print(f"强共线对( |r|>=0.7 ): {sum(1 for _ in [0]) if False else ''}")


if __name__ == "__main__":
    main()

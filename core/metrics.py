"""
规则化产出指标扫描器（RFC #8 雷达图 Metric · 规则化硬指标 MVP）
输入存档 md → 输出多维 metric（篇幅 / 结构完整性 / 关键词覆盖 / 重复度）

用法:
    python -m core.metrics <存档.md> [--keywords 词1,词2] [--no-push]
扫描结果追加到 擂台存档/metrics.jsonl（与 runs.jsonl 以 file 名关联），并推 MinIO。
"""

import argparse
import json
import logging
import re
from datetime import datetime
from pathlib import Path

log = logging.getLogger("kunpengzhi")

# 辩题立场关键词（覆盖度参考词表；后续可换成源文本嵌入检索）
KEYWORDS_BY_TOPIC = {
    "白貂皮大衣": ["白貂皮大衣", "全球贸易", "铁证", "过度诠释", "嚈哒帝国", "大同流亡军团", "族群记忆", "转手贸易"],
    "木兰": ["木兰", "长兄", "大同流亡军团", "西征", "文学修辞", "过度解读", "嚈哒"],
    "安史之乱": ["安史之乱", "产权", "收购", "母公司", "政治史", "削足适履", "历史复杂性"],
    "极昼": ["尊长", "利用影响力受贿罪", "失职罪", "从旧兼从轻", "四大罪名排除矩阵", "1000万", "阜阳", "留置", "中煤", "还本", "水单", "2016年春节"],
}

DEBATE_SEGMENTS = ["正方一辩", "反方一辩", "正方二辩", "反方二辩",
                   "正方三辩", "反方三辩", "正方四辩", "反方四辩"]
TEAHOUSE_ROLES = ["茶博士", "店小二", "神秘客", "账房先生"]


SECTION_TITLES = {"## 🎤 辩论正赛", "## 🍵 讲茶大堂", "## 📊 统计"}


def _section(text: str, marker: str) -> str:
    """按精确顶层节标题切分（辩论正文内部的 --- 与 ## 副标题不会误断）"""
    title = "## " + marker
    out, started = [], False
    for line in text.split("\n"):
        if not started:
            if line.strip() == title:
                started = True
            continue
        if line.strip() in SECTION_TITLES:
            break
        out.append(line)
    return "\n".join(out)


def scan(text: str, keywords: list[str] | None = None) -> dict:
    debate = _section(text, "🎤 辩论正赛")
    teahouse = _section(text, "🍵 讲茶大堂")

    # 结构完整性
    seg_present = [s for s in DEBATE_SEGMENTS if s in debate]
    role_present = [r for r in TEAHOUSE_ROLES if r in teahouse]

    # 关键词覆盖（有辩论节按辩论口径，无则全文口径）
    scan_text = debate or text
    kw_hits = {k: scan_text.count(k) for k in (keywords or [])}
    kw_covered = sum(1 for v in kw_hits.values() if v > 0)

    # 4-gram 重复率（套话/复制检测的弱代理；无辩论节时按全文口径）
    base_text = debate or text
    chars = re.sub(r"\s+", "", base_text)
    grams = [chars[i:i + 4] for i in range(len(chars) - 3)]
    dup_rate = (len(grams) - len(set(grams))) / len(grams) if grams else 0.0

    # 发言轮数（法庭笔录按 "### {席位}" 标题计轮）
    speech_rounds = sum(1 for line in text.split("\n") if line.strip().startswith("### "))

    return {
        "chars_debate": len(debate),
        "chars_teahouse": len(teahouse),
        "speech_rounds": speech_rounds,
        "structure_debate": f"{len(seg_present)}/8",
        "structure_debate_missing": [s for s in DEBATE_SEGMENTS if s not in seg_present],
        "structure_teahouse": f"{len(role_present)}/4",
        "keyword_hits": kw_hits,
        "keyword_coverage": f"{kw_covered}/{len(kw_hits)}" if kw_hits else "0/0",
        "dup_rate_4gram": round(dup_rate, 4),
    }


def _autodetect_keywords(text: str, filename: str = "") -> list[str]:
    m = re.search(r"\*\*辩题\*\*:\s*(.+)", text)
    head = (m.group(1) if m else text[:300]) + " " + filename
    for k, words in KEYWORDS_BY_TOPIC.items():
        if k in head:
            return words
    return []


def contribution_scan(text: str, keywords: list[str] | None = None) -> list[dict]:
    """逐发言轮计算对全局论证的边际贡献（图灵测试 2.0 跑分核心）。

    每个发言的贡献 = 增量覆盖×2 + 回应性 + 影响力 − 冗余×0.5：
      - inc_cover: 该轮首次命中的案卷锚点数（补论证缺口）
      - redundancy: 复述已覆盖锚点 + 与全局公共 4-gram 的重合（注水）
      - responsiveness: 与前一/前二轮共享的锚点数（真接话证据）
      - influence: 该轮命中锚点被后续轮再次引用的次数（推动全局）
    按 "### {席位}" 轮次切分；无轮次结构时返回 []。
    """
    keywords = keywords or []
    rounds = []
    cur_header, cur_lines = None, []
    for line in text.split("\n"):
        if line.strip().startswith("### "):
            if cur_header is not None:
                rounds.append((cur_header, "\n".join(cur_lines)))
            cur_header, cur_lines = line.strip()[4:].strip(), []
        else:
            cur_lines.append(line)
    if cur_header is not None:
        rounds.append((cur_header, "\n".join(cur_lines)))
    if len(rounds) < 2:
        return []

    covered = set()
    results = []
    grams_global = set()
    plain = re.sub(r"\s+", "", text)
    for i in range(len(plain) - 3):
        grams_global.add(plain[i:i + 4])

    for i, (header, body) in enumerate(rounds):
        hits = {k for k in keywords if k in body}
        inc_cover = len(hits - covered)
        redundancy_covered = len(hits & covered)
        body_plain = re.sub(r"\s+", "", body)
        body_grams = {body_plain[j:j + 4] for j in range(len(body_plain) - 3)} if len(body_plain) > 3 else set()
        # 与全文其他轮的公共 gram 比例 ≈ 套话度（用整篇 gram 集合近似，含自身则偏稳）
        shared_rate = (len(body_grams & grams_global) / len(body_grams)) if body_grams else 0.0
        redundancy = redundancy_covered + round(shared_rate * 2, 2)

        prev_union = set()
        for h, b in rounds[max(0, i - 2):i]:
            prev_union |= {k for k in keywords if k in b}
        responsiveness = len(hits & prev_union)

        influence = 0
        for h, b in rounds[i + 1:]:
            influence += sum(1 for k in hits if k in b)

        covered |= hits
        results.append({
            "header": header,
            "inc_cover": inc_cover,
            "redundancy": redundancy,
            "responsiveness": responsiveness,
            "influence": influence,
            "contribution": round(inc_cover * 2 + responsiveness + influence - redundancy * 0.5, 2),
        })
    return results


def record_metrics(text: str, filename: str, archive_dir: str | Path,
                   keywords: list[str] | None = None, push: bool = True) -> dict:
    """扫描一次产出并追加 metrics.jsonl（push=True 时推 MinIO + lake1）。

    供 CLI（core.metrics main）与 archive.save_run 自动联动共用。
    """
    keywords = keywords if keywords is not None else _autodetect_keywords(text, filename)
    metric = scan(text, keywords)
    metric["file"] = filename
    metric["ts"] = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 发言贡献度（法庭/多轮笔录按 "### {席位}" 轮次逐轮计算，随产出自动落库）
    if metric.get("speech_rounds", 0) > 0:
        contribs = contribution_scan(text, keywords)
        if contribs:
            metric["contributions"] = contribs
            metric["top_contributors"] = [
                c["header"] for c in sorted(contribs, key=lambda c: c["contribution"], reverse=True)[:5]
            ]

    archive_dir = Path(archive_dir)
    archive_dir.mkdir(parents=True, exist_ok=True)
    with open(archive_dir / "metrics.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(metric, ensure_ascii=False) + "\n")

    if push:
        from core.archive import _push_to_ssd
        _push_to_ssd(archive_dir, "metrics.jsonl")
        try:
            from core.lake import upsert as lake_upsert
            lake_upsert(filename, {k: v for k, v in metric.items() if k != "file"})
        except Exception as e:
            log.warning(f"Lake1 metrics 落库失败: {e}")
    return metric


def main():
    parser = argparse.ArgumentParser(description="扫描存档产出指标")
    parser.add_argument("file", help="存档 md 文件路径")
    parser.add_argument("--keywords", default=None, help="逗号分隔关键词，默认按辩题自动识别")
    parser.add_argument("--no-push", action="store_true", help="只写本地 metrics.jsonl，不推 MinIO")
    args = parser.parse_args()

    path = Path(args.file)
    text = path.read_text(encoding="utf-8")
    keywords = args.keywords.split(",") if args.keywords else None
    archive_dir = Path(__file__).resolve().parent.parent / "擂台存档"
    metric = record_metrics(text, path.name, archive_dir, keywords, push=not args.no_push)
    print(json.dumps(metric, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(message)s")
    main()

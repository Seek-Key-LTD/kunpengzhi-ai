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


def record_metrics(text: str, filename: str, archive_dir: str | Path,
                   keywords: list[str] | None = None, push: bool = True) -> dict:
    """扫描一次产出并追加 metrics.jsonl（push=True 时推 MinIO + lake1）。

    供 CLI（core.metrics main）与 archive.save_run 自动联动共用。
    """
    keywords = keywords if keywords is not None else _autodetect_keywords(text, filename)
    metric = scan(text, keywords)
    metric["file"] = filename
    metric["ts"] = datetime.now().strftime("%Y%m%d_%H%M%S")

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

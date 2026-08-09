"""
统一存档出口：本地 擂台存档/ + runs.jsonl 索引 + MinIO (ssd) 推送
所有出口（CLI / Chainlit / Streamlit）都走 save_run，保证逐版本可追踪。
"""

import datetime
import json
import logging
import os
import shutil
import subprocess
from pathlib import Path

log = logging.getLogger("kunpengzhi")

ARCHIVE_DIR = Path(__file__).resolve().parent.parent / "擂台存档"
SSD_BUCKET = "ssd/kunpengzhi-archive/擂台存档/"
RUNS_INDEX = "runs.jsonl"
MC_BIN = shutil.which("mc") or "/home/ben/.local/bin/mc"


def _git_commit() -> str:
    try:
        repo = Path(__file__).resolve().parent.parent
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo, capture_output=True, text=True, timeout=10,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except Exception:
        pass
    return "unknown"


def _push_to_ssd(archive_dir: Path, relpath: str) -> bool:
    """mc cp 到 MinIO；失败只告警，本地落盘已算成功。"""
    if not os.path.exists(MC_BIN):
        log.warning(f"Archive: mc 不存在 ({MC_BIN})，跳过 MinIO 推送")
        return False
    try:
        r = subprocess.run(
            [MC_BIN, "cp", str(archive_dir / relpath), SSD_BUCKET],
            capture_output=True, text=True, timeout=120,
        )
        if r.returncode != 0:
            log.warning(f"Archive: mc cp {relpath} 失败: {r.stderr.strip()[:300]}")
            return False
        return True
    except Exception as e:
        log.warning(f"Archive: mc cp {relpath} 异常: {e}")
        return False


def _finalize(target_dir: Path, filename: str, ts: str, kind: str, title: str, meta: dict, text: str) -> None:
    """存档收尾（save_run 与 close_stream 共用）：索引 + MinIO + lake1 + 指标。

    meta 可带 "_steps"：每步过程元数据（耗时/模型/上下文注入清单），
    摘要进索引行，完整数组仅落 lake1 文档（不进 runs.jsonl）。
    """
    steps_detail = meta.pop("_steps", None)
    entry = {
        "kind": kind,
        "title": title,
        "ts": ts,
        "file": filename,
        "chars": len(text),
        "commit": _git_commit(),
        "env": os.environ.get("HOSTNAME", os.environ.get("COMPUTERNAME", "unknown")),
    }
    if steps_detail:
        entry["steps_count"] = len(steps_detail)
        entry["duration_total_sec"] = round(sum(s.get("duration_sec", 0) for s in steps_detail), 2)
        entry["avg_step_sec"] = round(entry["duration_total_sec"] / max(len(steps_detail), 1), 2)
        entry["steps_failed"] = sum(1 for s in steps_detail if not s.get("ok", True))
    entry.update({k: v for k, v in meta.items() if k not in entry})

    with open(target_dir / RUNS_INDEX, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    _push_to_ssd(target_dir, filename)
    _push_to_ssd(target_dir, RUNS_INDEX)

    try:
        from core.lake import upsert as lake_upsert
        doc = dict(entry)
        if steps_detail:
            doc["steps"] = steps_detail
        lake_upsert(filename, doc)
    except Exception as e:
        log.warning(f"Archive: lake1 落库失败: {e}")

    try:
        from core.metrics import record_metrics
        record_metrics(text, filename, target_dir)
    except Exception as e:
        log.warning(f"Archive: metrics 扫描失败: {e}")

    log.info(f"📝 已落盘存档: {filename} ({entry['chars']} 字符, commit {entry['commit']})")


def save_run(kind: str, title: str, markdown: str, meta: dict, archive_dir: str | Path | None = None) -> str:
    """
    统一落盘一次运行实录（一次性：文本已完整时用）。

    kind: 运行类别（辩论 / 法庭 / 擂台 / 测试）
    title: 辩题或案卷标题（取前 12 字符作文件名）
    meta: 附加索引字段（model / topic_id 等）
    archive_dir: 本地存档目录，默认项目根 擂台存档/

    返回文件名（不含目录），如 擂台-白貂皮大衣：全球贸易网络-20260609_120000.md
    """
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c for c in title[:12] if c not in "/\\:*?\"<>|")
    filename = f"擂台-{safe_title}-{ts}.md"

    target_dir = Path(archive_dir) if archive_dir else ARCHIVE_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / filename).write_text(markdown, encoding="utf-8")

    _finalize(target_dir, filename, ts, kind, title, meta, markdown)
    return filename


def open_stream(kind: str, title: str, archive_dir: str | Path | None = None) -> tuple[str, str, str]:
    """创建流式会话文件（法庭实录边跑边写），返回 (path, filename, ts)。

    配合 append_stream / close_stream 使用；中途崩溃则会话文件保留在前半段。
    """
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c for c in title[:12] if c not in "/\\:*?\"<>|")
    filename = f"擂台-{safe_title}-{ts}.md"

    target_dir = Path(archive_dir) if archive_dir else ARCHIVE_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / filename
    path.write_text(f"# 🦅 鲲鹏志 · {kind}实录 · 流式会话\n\n", encoding="utf-8")
    return str(path), filename, ts


def append_stream(path: str, header: str, content: str) -> None:
    """流式追加一轮发言。"""
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"### {header}\n\n{content}\n\n")


def close_stream(path: str, filename: str, ts: str, kind: str, title: str, meta: dict,
                 archive_dir: str | Path | None = None) -> str:
    """流式会话收尾：正文已逐轮写入，此处做索引 + MinIO + lake1 + 指标。"""
    target_dir = Path(archive_dir) if archive_dir else ARCHIVE_DIR
    text = Path(path).read_text(encoding="utf-8")
    _finalize(target_dir, filename, ts, kind, title, meta, text)
    return filename

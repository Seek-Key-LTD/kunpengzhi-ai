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


def save_run(kind: str, title: str, markdown: str, meta: dict, archive_dir: str | Path | None = None) -> str:
    """
    统一落盘一次运行实录。

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

    entry = {
        "kind": kind,
        "title": title,
        "ts": ts,
        "file": filename,
        "chars": len(markdown),
        "commit": _git_commit(),
        "env": os.environ.get("HOSTNAME", os.environ.get("COMPUTERNAME", "unknown")),
    }
    entry.update({k: v for k, v in meta.items() if k not in entry})

    with open(target_dir / RUNS_INDEX, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    _push_to_ssd(target_dir, filename)
    _push_to_ssd(target_dir, RUNS_INDEX)

    try:
        from core.lake import upsert as lake_upsert
        lake_upsert(filename, entry)
    except Exception as e:
        log.warning(f"Archive: lake1 落库失败: {e}")

    try:
        from core.metrics import record_metrics
        record_metrics(markdown, filename, target_dir)
    except Exception as e:
        log.warning(f"Archive: metrics 扫描失败: {e}")

    log.info(f"📝 已落盘存档: {filename} ({entry['chars']} 字符, commit {entry['commit']})")
    return filename

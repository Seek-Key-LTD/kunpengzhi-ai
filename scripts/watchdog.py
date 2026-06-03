#!/usr/bin/env python3
"""
鲲鹏志 · 夜间看门狗 🐕
=====================
监控 burn_night.py 的运行状态。
如果进程挂了，自动重启。
每 5 分钟记录一次 Token 消耗和估算成本。
"""

import os
import sys
import time
import json
import signal
import subprocess
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s - WATCHDOG - %(message)s")
log = logging.getLogger("watchdog")

SCRIPT = os.path.join(os.path.dirname(__file__), "burn_night.py")
LOG_FILE = "/tmp/burn_output.log"
PROGRESS_FILE = "/tmp/burn_progress.json"
PID_FILE = "/tmp/burn_pid.txt"
RESTART_LOG = "/tmp/burn_restarts.txt"


def log_restart(reason: str):
    with open(RESTART_LOG, "a") as f:
        f.write(f"[{datetime.now().isoformat()}] {reason}\n")


def read_progress() -> dict:
    try:
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    except:
        return {"done": {}}


def count_done() -> int:
    p = read_progress()
    total = 0
    for k, v in p.get("done", {}).items():
        total += len(v)
    return total


def is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except:
        return False


def start_process() -> int:
    with open(LOG_FILE, "a") as log_f:
        proc = subprocess.Popen(
            [sys.executable, SCRIPT],
            stdout=log_f,
            stderr=log_f,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
    with open(PID_FILE, "w") as f:
        f.write(str(proc.pid))
    log.info(f"🚀 进程启动 PID={proc.pid}")
    log_restart(f"启动 PID={proc.pid}")
    return proc.pid


def main():
    log.info("=" * 60)
    log.info("🦅 鲲鹏志 · 夜间看门狗启动")
    log.info("=" * 60)
    log.info(f"  脚本: {SCRIPT}")
    log.info(f"  日志: {LOG_FILE}")
    log.info(f"  进度: {PROGRESS_FILE}")
    log.info("")

    pid = start_process()
    last_done = count_done()
    last_check = time.time()
    start_time = time.time()
    token_estimates = []

    try:
        while True:
            time.sleep(120)  # 每 2 分钟检查一次

            # 检查进程是否还在
            if not is_running(pid):
                log.error(f"❌ 进程 {pid} 已崩溃！")
                log_restart(f"崩溃 PID={pid}")
                # 查看最后几行日志
                try:
                    with open(LOG_FILE) as f:
                        lines = f.readlines()[-20:]
                    log.error("最后20行日志:")
                    for l in lines:
                        log.error(f"  {l.rstrip()}")
                except:
                    pass
                pid = start_process()
                last_done = count_done()
                continue

            # 每 10 分钟报告一次进度
            now = time.time()
            if now - last_check >= 600:  # 10 分钟
                elapsed = now - start_time
                done = count_done()
                rate = (done - last_done) / ((now - last_check) / 3600)  # 每小时完成数
                
                # 从日志中提取 token 信息
                token_info = ""
                try:
                    with open(LOG_FILE) as f:
                        content = f.read()
                    # 查找最新的 token 统计
                    for line in content.split('\n')[-50:]:
                        if 'tokens' in line.lower() or 'Token' in line:
                            token_info = line.strip()
                except:
                    pass
                
                log.info(f"📊 [{elapsed/3600:.1f}h] 已完成: {done} 项 | 速率: {rate:.0f} 项/小时")
                if token_info:
                    log.info(f"   {token_info}")
                
                last_check = now
                last_done = done

    except KeyboardInterrupt:
        log.info("👋 看门狗被手动停止")
        os.kill(pid, signal.SIGTERM)
    except Exception as e:
        log.error(f"💥 看门狗异常: {e}")
        os.kill(pid, signal.SIGTERM)


if __name__ == "__main__":
    main()

"""
辩论引擎 — Phase1 MVP
"""

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

from core.seats import get_seat, get_pro_seats, get_con_seats

class DebateOrchestrator:
    @staticmethod
    async def run(topic_id: str, save_dir: Path) -> dict:
        """
        运行一场辩论
        返回: {
            "title": str,
            "debate": str,      # 辩论全文
            "teahouse": str,    # 讲茶大堂评论
            "scores": dict,     # 席位评分
            "file": str,        # 保存路径
        }
        """
        save_dir.mkdir(exist_ok=True, parents=True)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        file_path = save_dir / f"debate_{topic_id}_{timestamp}.json"

        # Phase1 模拟数据
        pro_seats = get_pro_seats()[:2]  # 2正
        con_seats = get_con_seats()[:2]  # 2反

        debate_text = ""
        for round_num in range(1, 4):  # 3轮
            debate_text += f"\n\n=== 第 {round_num} 轮 ===\n"
            for seat in pro_seats + con_seats:
                side = "正方" if seat["role"].value == "pro" else "反方"
                debate_text += (
                    f"\n{side} {seat['name']}{seat['gua']} ({seat['note']}调):\n"
                    f"  关于《牧人记》第{topic_id}章的论点："
                    f"  {'支持' if side == '正方' else '反对'}本轮辩题。\n"
                    f"  （模拟发言，Phase1用）\n"
                )

        teahouse_text = (
            "讲茶大堂评论：\n"
            "  正方论点扎实，但音乐表达略显单调。\n"
            "  反方逻辑严密，螺旋谱展现出良好的调性一致性。\n"
            "  总体而言，本场辩论礼分高于乐分，符合预期。\n"
        )

        scores = {}
        for seat in pro_seats + con_seats:
            scores[seat["id"]] = {
                "li": 7.5 + (0.5 if seat["role"].value == "pro" else -0.5),
                "yue": 6.0 + (0.8 if seat["note"] in ["G", "C"] else 0.3),
                "spiral": 8.0,
                "total": 0.0,  # 后面计算
            }
            scores[seat["id"]]["total"] = (
                scores[seat["id"]]["li"] *
                scores[seat["id"]]["yue"] *
                scores[seat["id"]]["spiral"]
            )

        result = {
            "title": f"辩题 {topic_id} 模拟辩论",
            "debate": debate_text,
            "teahouse": teahouse_text,
            "scores": scores,
            "file": str(file_path),
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return result
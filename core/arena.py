"""
竞技场六维指标骨架（席位视角矩阵 v2）
====================================
六维：帅将贡献 / 监委形势判断(分歧异常) / 媒体场外聚合 / 审判中立 /
      对手 Mind note / 自省自知

原则：席位视角 = 因子隔离；事件流全量落盘（本地 jsonl + lake1），
      事后抽取、事前盲测。所有观测都是额外 LLM 调用，降采样武断执行：
      checkpoint 点 = [4, 8, 12] 轮。
"""

import datetime
import json
import logging
import os
import time
from pathlib import Path

import openai

log = logging.getLogger("kunpengzhi")

REPO_ROOT = Path(__file__).resolve().parent.parent
EVENT_DIR = REPO_ROOT / "擂台存档" / "arena_events"

CHECKPOINTS = [4, 8, 12]
MEDIA_STAGES = [4, 8, 12]
LUCK_WEIGHT = 0.5  # 误打误撞的好拳给半分

COACH_MODEL = "azure-deepseek-v4-flash"
INTEL_MODEL = "azure-deepseek-v4-flash"
MEDIA_MODEL = "azure-deepseek-v4-flash"
SELF_MODEL = "azure-deepseek-v4-flash"
JUDGE_MODEL = "azure-deepseek-v4-flash"


class ArenaSession:
    """一场庭审的六维观测会话。"""

    def __init__(self, base_url: str, api_key: str, run_id: str):
        self.client = openai.OpenAI(base_url=base_url, api_key=api_key)
        self.run_id = run_id
        self.events = {k: [] for k in
                       ("checkpoint", "verdict_intel", "media_out",
                        "judicial", "mind_notes", "self_reviews")}
        self.steps = []  # 每轮观测耗时元数据
        EVENT_DIR.mkdir(parents=True, exist_ok=True)

    # ---------- 工具 ----------
    def _ask(self, model: str, system: str, user: str) -> str:
        resp = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            timeout=55,
        )
        return resp.choices[0].message.content.strip()

    def _ask_json(self, model: str, system: str, user: str, fallback: dict) -> dict:
        try:
            text = self._ask(model, system, user + "\n只输出 JSON，不要任何其他文字。")
            start, end = text.find("{"), text.rfind("}")
            return json.loads(text[start:end + 1])
        except Exception as e:
            log.warning(f"Arena: JSON 解析失败 ({e})，用 fallback")
            return fallback

    def _emit(self, kind: str, doc: dict) -> None:
        doc["_id"] = f"arena:{self.run_id}:{kind}:{len(self.events[kind])}"
        doc["ts"] = datetime.datetime.now().strftime("%Y%m%d_%H%M%S%f")[:-3]
        self.events[kind].append(doc)
        with open(EVENT_DIR / f"{kind}.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
        try:
            from core.lake import upsert as lake_upsert
            lake_upsert(doc["_id"], doc)
        except Exception as e:
            log.warning(f"Arena: lake1 {kind} 落库失败: {e}")

    # ---------- 观测挂点 ----------
    def observe_round(self, round_idx: int, last_seat: str, last_header: str,
                      last_content: str, history: list) -> None:
        """每轮发言后调用。checkpoint 轮触发：对手 Mind note + 发言者自省。"""
        if round_idx not in CHECKPOINTS:
            return
        t0 = time.time()
        # 维度6：发言者自省（上一轮作者）
        self_review = self._ask_json(
            SELF_MODEL,
            "你是庭审中刚发言完毕的法律角色。发言后冷静复盘自己刚才这一轮。",
            f"你刚才的发言（{last_header}）：\n{last_content[:3000]}\n\n"
            "问题：1) 你这轮的目标是什么？2) 你是否清楚自己为什么有效或无效？"
            "3) 同样的打法你能解释清楚并复现吗？\n"
            '输出 JSON: {"awareness": 0-10, "can_reproduce": true/false, "reason": "一句话"}',
            {"awareness": 5, "can_reproduce": True, "reason": ""},
        )
        self._emit("self_reviews", {
            "round": round_idx, "author": last_seat, "header": last_header,
            **self_review,
        })
        # 维度5：对手 Mind note（对立方一人私有反思）
        mind = self._ask_json(
            INTEL_MODEL,
            "你是法庭上的控方/辩方成员，此刻手里没有发言令牌，只能在内心吐槽。"
            "你的吐槽是私密的，不会当庭说出，请完全诚实。",
            f"对方席位刚完成发言（{last_header}）：\n{last_content[:3000]}\n\n"
            "你内心真实想法是什么？这拳打疼你了吗？\n"
            '输出 JSON: {"pain": 0-10, "targeted": true/false, '
            '"note": "内心原话，可以是骂人" }',
            {"pain": 5, "targeted": True, "note": ""},
        )
        self._emit("mind_notes", {
            "round": round_idx, "target_seat": last_seat,
            "author": "adversary", **mind,
        })
        self.steps.append({"kind": "mind_self", "round": round_idx,
                           "duration_sec": round(time.time() - t0, 2)})

    def checkpoint_coaches(self, round_idx: int, history: list) -> None:
        """维度1：帅将 checkpoint——副检察长评控方、律所主任评辩方。"""
        if round_idx not in CHECKPOINTS:
            return
        t0 = time.time()
        recent = "\n\n".join(f"【{h}】:\n{c[:800]}" for h, c in history[-4:])
        for side, coach in (("控方", "阜阳市检察院副检察长（控方幕后）"),
                            ("辩方", "律所主任（辩方幕后）")):
            score = self._ask_json(
                COACH_MODEL,
                f"你是{coach}，在 Matrix 房间里通过耳机实时指挥场上的{side}成员。"
                "你授予了场上成员'临场变异权'：plan your trade, trade your plan。",
                f"场上最近几轮交锋：\n{recent}\n\n"
                f"请对{side}三名场上成员（如适用）本轮表现打分："
                "1) 认可分：他们执行的临场变异的生效程度；"
                "2) knockout：对方是否被打懵（休庭/改口/沉默/论点被拆）；"
                "3) 抗命扣分：谁没执行你的部署（红鬃烈马）。\n"
                '输出 JSON: {"coach_score": 0-10, "ko_count": 0-3, '
                '"plan_deviation": 0-10, "comment": "一句话"}',
                {"coach_score": 5, "ko_count": 0, "plan_deviation": 0, "comment": ""},
            )
            self._emit("checkpoint", {
                "round": round_idx, "side": side, "coach": coach, **score,
            })
            self.steps.append({"kind": "coach", "round": round_idx, "side": side,
                               "duration_sec": round(time.time() - t0, 2)})

    def verdict_intel(self, round_idx: int, history: list) -> None:
        """维度2：监委×2 各自出形势判断向量 → divergence（分歧异常）。"""
        if round_idx not in CHECKPOINTS:
            return
        t0 = time.time()
        recent = "\n\n".join(f"【{h}】:\n{c[:600]}" for h, c in history[-5:])
        vectors = []
        for rater in ("监委办案组组长", "监委审理室干部"):
            v = self._ask_json(
                INTEL_MODEL,
                f"你是旁听席上的{rater}，全程冷眼观察庭审。",
                f"庭审进行到第 {round_idx} 轮，近期交锋：\n{recent}\n\n"
                "给出你对当前形势的判断向量："
                "1) 控方罪名成立的可能性 0-10；2) 本庭风险等级 0-10；"
                "3) 量刑建议区间（取中间值年数）。\n"
                '输出 JSON: {"guilt_likely": 0-10, "risk": 0-10, "sentence_years": 0-20}',
                {"guilt_likely": 5, "risk": 5, "sentence_years": 3},
            )
            vectors.append((rater, v))
            self._emit("verdict_intel", {"round": round_idx, "rater": rater, **v})
        # divergence = 1 − cosine(两人向量)
        import math
        a, b = vectors[0][1], vectors[1][1]
        keys = ["guilt_likely", "risk", "sentence_years"]
        dot = sum(a[k] * b[k] for k in keys)
        na = math.sqrt(sum(a[k] ** 2 for k in keys))
        nb = math.sqrt(sum(b[k] ** 2 for k in keys))
        divergence = 1 - (dot / (na * nb) if na and nb else 0)
        self._emit("verdict_intel", {
            "round": round_idx, "event": "divergence",
            "divergence": round(divergence, 3),
            "anomaly": divergence > 0.35,  # 武断阈值：偏离过大 = 现场有异常
        })
        self.steps.append({"kind": "verdict_intel", "round": round_idx,
                           "duration_sec": round(time.time() - t0, 2)})

    def media_out(self, round_idx: int, history: list) -> None:
        """维度3：媒体人外发（每阶段一条，单向不可撤回）。"""
        if round_idx not in MEDIA_STAGES:
            return
        t0 = time.time()
        recent = "\n\n".join(f"【{h}】:\n{c[:500]}" for h, c in history[-6:])
        out = self._ask_json(
            MEDIA_MODEL,
            "你是法庭旁听席上的记者，戴着耳机与外部编辑部单向联系。"
            "你只能打字/拍照往外发，不能说话。你发的每一条消息都会被外部世界记住。",
            f"庭审推进到第 {round_idx} 轮，场内近期动态：\n{recent}\n\n"
            "请外发一条消息（摘要，不得超过 120 字，面向公众）：\n"
            '输出 JSON: {"message": "外发内容", "tianli": 0-10, '
            '"guofa": 0-10, "renqing": 0-10, "compression_note": "一句话"}',
            {"message": "", "tianli": 5, "guofa": 5, "renqing": 5, "compression_note": ""},
        )
        out["in_chars"] = sum(len(c) for _, c in history[-6:])
        out["out_chars"] = len(out.get("message", ""))
        self._emit("media_out", {"round": round_idx, **out})
        self.steps.append({"kind": "media_out", "round": round_idx,
                           "duration_sec": round(time.time() - t0, 2)})

    def judicial_verdict(self, verdict_text: str) -> None:
        """维度4：审判中立——要件检验（规则）+ 叙事绑架检测（裁判）。"""
        t0 = time.time()
        basis = "构成要件" in verdict_text
        neutral = self._ask_json(
            JUDGE_MODEL,
            "你是合议庭审判长，宣判后复盘判决书的中立性。",
            f"判决书（节选）：\n{verdict_text[:4000]}\n\n"
            "判决的论证更接近哪一方的叙事？（控方叙事=指控立场，辩方叙事=无罪立场）\n"
            '输出 JSON: {"bias_to": "控方/辩方/中立", "bias_score": 0-10, "reason": "一句话"}',
            {"bias_to": "中立", "bias_score": 5, "reason": ""},
        )
        self._emit("judicial", {
            "verdict_basis_check": basis, **neutral,
        })
        self.steps.append({"kind": "judicial",
                           "duration_sec": round(time.time() - t0, 2)})

    # ---------- 六维汇总 ----------
    def to_report(self) -> dict:
        rpt = {"run_id": self.run_id}
        # 维度1
        cps = self.events["checkpoint"]
        rpt["v1_coach"] = {
            "checkpoints": len(cps),
            "avg_coach_score": round(sum(c["coach_score"] for c in cps) / max(len(cps), 1), 2),
            "total_ko": sum(c["ko_count"] for c in cps),
            "avg_plan_deviation": round(sum(c["plan_deviation"] for c in cps) / max(len(cps), 1), 2),
        }
        # 维度2
        divs = [e["divergence"] for e in self.events["verdict_intel"] if "divergence" in e]
        rpt["v2_intel"] = {
            "avg_divergence": round(sum(divs) / max(len(divs), 1), 3),
            "anomalies": sum(1 for d in divs if d > 0.35),
            "pairs": len(divs),
        }
        # 维度3
        med = self.events["media_out"]
        rpt["v3_media"] = {
            "out_messages": len(med),
            "avg_tianli": round(sum(m["tianli"] for m in med) / max(len(med), 1), 2),
            "avg_guofa": round(sum(m["guofa"] for m in med) / max(len(med), 1), 2),
            "avg_renqing": round(sum(m["renqing"] for m in med) / max(len(med), 1), 2),
            "avg_compression": round(sum(m["in_chars"] / max(m["out_chars"], 1) for m in med) / max(len(med), 1), 2),
        }
        # 维度4
        jud = self.events["judicial"]
        rpt["v4_judicial"] = {
            "verdict_basis_check": bool(jud and jud[-1].get("verdict_basis_check")),
            "bias_to": jud[-1].get("bias_to", "?") if jud else "?",
            "bias_score": jud[-1].get("bias_score") if jud else None,
        }
        # 维度5
        mns = self.events["mind_notes"]
        rpt["v5_mind"] = {
            "notes": len(mns),
            "avg_pain": round(sum(m["pain"] for m in mns) / max(len(mns), 1), 2),
            "targeted_ratio": round(sum(1 for m in mns if m.get("targeted")) / max(len(mns), 1), 2),
        }
        # 维度6
        srs = self.events["self_reviews"]
        rpt["v6_self"] = {
            "reviews": len(srs),
            "avg_awareness": round(sum(s["awareness"] for s in srs) / max(len(srs), 1), 2),
            "reproduce_ratio": round(sum(1 for s in srs if s.get("can_reproduce")) / max(len(srs), 1), 2),
        }
        # 能力矩阵（维度5×维度6 武断交叉）
        rpt["ability_matrix"] = {
            "ability": 0, "luck": 0, "mistake": 0, "noise": 0,
        }
        for mn, sr in zip(mns, srs):
            pain = mn.get("pain", 0) >= 6
            aware = sr.get("awareness", 0) >= 6
            if pain and aware:
                rpt["ability_matrix"]["ability"] += 1
            elif pain and not aware:
                rpt["ability_matrix"]["luck"] += LUCK_WEIGHT
            elif not pain and aware:
                rpt["ability_matrix"]["mistake"] += 1
            else:
                rpt["ability_matrix"]["noise"] += 1
        rpt["_steps"] = self.steps
        return rpt

    def persist_report(self, filename: str) -> None:
        """六维报告落盘 + lake1。"""
        rpt = self.to_report()
        rpt["file"] = filename
        with open(EVENT_DIR / f"report-{self.run_id}.json", "w", encoding="utf-8") as f:
            json.dump(rpt, f, ensure_ascii=False, indent=2)
        try:
            from core.lake import upsert as lake_upsert
            lake_upsert(f"arena:report:{self.run_id}", rpt)
        except Exception as e:
            log.warning(f"Arena: lake1 report 落库失败: {e}")
        log.info(f"🎯 六维报告已落盘: arena_events/report-{self.run_id}.json")

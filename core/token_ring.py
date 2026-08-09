"""RobertTokenRingEngine — 完整令牌环庭审引擎（黄道内阁版）
从 6a5d8ee 原版逻辑适配 VAULT_ZODIAC_CABINETS 结构：
token_holder 令牌持有 / 定向接话共享上下文 / 前发言人陈词 / 极昼全量记忆。

互通策略（v2 定向接话，替代 v1 全量广播）：
- 起诉书锚点：全局唯一，始终注入（控方立场权威文本）
- 前一位发言人陈词：始终注入（后手必须接话）
- 同阵营既往陈词：按 team 定向注入（prosecutor/defense/judge/court）
- 小花组：普通成员只接前一位（独立维度防复读），violet 注入全部小花（汇总所需）
"""
import openai


class RobertTokenRingEngine:
    def __init__(self, base_url, api_key, article_text, scenario="court"):
        self.client = openai.OpenAI(base_url=base_url, api_key=api_key)
        self.article_text = article_text or ""
        self.scenario = scenario
        self.token_holder = "ruby"          # 令牌初始在审判长（红宝石）手中
        self.shared_context = []            # 共享法庭笔录上下文 (Shared Memory)
        self._model = "nova-deepseek-v4-flash-aggr"

    # ---- 共享上下文 ----
    def add_to_shared_context(self, avatar, content, team=""):
        self.shared_context.append({"header": str(avatar), "content": str(content), "team": team})

    def get_shared_context_str(self):
        return "\n\n".join(
            f"【{m['header']}】:\n{m['content']}" for m in self.shared_context
        )

    # ---- 定向接话上下文 ----
    def _build_context_blocks(self, team, en_key):
        """按互通策略组装注入块：起诉书锚 + 前一位 + 同阵营定向。"""
        blocks = []
        for m in self.shared_context:
            if m.get("team") == "indictment":
                blocks.append(("起诉书（全局控方立场锚）", m["content"]))
                break
        if self.shared_context and self.shared_context[-1].get("team") != "indictment":
            last = self.shared_context[-1]
            blocks.append((f"前一位发言人 ({last['header']}) 的陈词", last["content"]))
        if en_key == "violet":
            flowers = [m for m in self.shared_context if m.get("team") == "flower"]
            blocks += [(f"小花组既往合议 ({m['header']})", m["content"]) for m in flowers]
        elif team and team != "flower":
            last_header = self.shared_context[-1]["header"] if self.shared_context else ""
            same = [m for m in self.shared_context
                    if m.get("team") == team and m["header"] != last_header]
            blocks += [(f"同阵营既往陈词 ({m['header']})", m["content"]) for m in same]
        return blocks

    # ---- 起诉书 ----
    def draft_official_indictment(self):
        return (
            f"【起诉书】就《极昼》案，指控尊长（原中煤集团党组成员，2026年8月3日被带至"
            f"安徽省阜阳市留置）涉嫌违规参与民间借贷、利用职务影响力为亲友企业拆借资金。"
            f"（场景：{self.scenario}；完整指控与证据链由令牌环庭审逐阶段生成）"
        )

    # ---- 完整令牌环发言 ----
    def execute_speech(self, seat_info, instruction):
        """按令牌环发言：持令牌者基于定向接话上下文 + 极昼全量记忆发言"""
        avatars = seat_info.get("avatars", {})
        header = avatars.get(self.scenario, avatars.get("court", seat_info.get("en_key", "席位")))
        model = seat_info.get("model") or self._model
        team = seat_info.get("team", "")
        en_key = seat_info.get("en_key", "")

        blocks = self._build_context_blocks(team, en_key)
        ctx_str = "\n\n".join(f"【{label}】:\n{content}" for label, content in blocks) or "(空)"

        doc_mem = (
            f"\n【《极昼.md》全量案卷记忆】:\n{self.article_text[:18000]}\n"
            if self.article_text else ""
        )

        prompt = (
            f"你是模拟法庭角色：【{header}】。\n"
            f"你当前持有【法庭发言令牌 Token】！令牌现在在你手中，你必须发言。\n"
            f"{doc_mem}\n"
            f"【定向接话上下文 (Shared Memory)】:\n{ctx_str}\n"
            f"你的任务指令：{instruction}\n"
            f"发言要求：沉静、严肃、有法理深度，直接切入，不超 400 字。"
        )
        try:
            resp = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                timeout=60,
            )
            content = resp.choices[0].message.content.strip()
        except Exception as e:
            content = f"（{header} 引擎调用失败: {e}）"
        self.add_to_shared_context(header, content, team)
        return (header, content)

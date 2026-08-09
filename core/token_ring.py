"""RobertTokenRingEngine — 完整令牌环庭审引擎（黄道内阁版）
从 6a5d8ee 原版逻辑适配 VAULT_ZODIAC_CABINETS 结构：
token_holder 令牌持有 / 共享上下文 / 前发言人陈词 / 极昼全量记忆。
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
    def add_to_shared_context(self, avatar, content):
        self.shared_context.append({"header": str(avatar), "content": str(content)})

    def get_shared_context_str(self):
        return "\n\n".join(
            f"【{m['header']}】:\n{m['content']}" for m in self.shared_context
        )

    # ---- 起诉书 ----
    def draft_official_indictment(self):
        return (
            f"【起诉书】就《极昼》案，指控尊长（原中煤集团党组成员，2026年8月3日被带至"
            f"安徽省阜阳市留置）涉嫌违规参与民间借贷、利用职务影响力为亲友企业拆借资金。"
            f"（场景：{self.scenario}；完整指控与证据链由令牌环庭审逐阶段生成）"
        )

    # ---- 完整令牌环发言 ----
    def execute_speech(self, seat_info, instruction):
        """按令牌环发言：持令牌者基于前发言人陈词 + 共享上下文 + 极昼全量记忆发言"""
        avatars = seat_info.get("avatars", {})
        header = avatars.get(self.scenario, avatars.get("court", seat_info.get("en_key", "席位")))
        model = seat_info.get("model") or self._model

        # 前一位发言人（令牌环关键：基于前发言陈词）
        prev_speaker_str = ""
        if self.shared_context:
            last = self.shared_context[-1]
            prev_speaker_str = (
                f"\n【前一位发言人 ({last['header']}) 的陈词】:\n\"\"\"\n{last['content']}\n\"\"\"\n"
            )

        doc_mem = (
            f"\n【《极昼.md》全量案卷记忆】:\n{self.article_text[:18000]}\n"
            if self.article_text else ""
        )

        prompt = (
            f"你是模拟法庭角色：【{header}】。\n"
            f"你当前持有【法庭发言令牌 Token】！令牌现在在你手中，你必须发言。\n"
            f"{doc_mem}\n"
            f"【共享法庭笔录上下文 (Shared Memory)】:\n{self.get_shared_context_str() or '(空)'}\n"
            f"{prev_speaker_str}\n"
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
        return (header, content)

"""RobertTokenRingEngine — 令牌环庭审引擎（最小可用版）
协作代码引用了此类但未实现；此处补最小实现：按席位令牌环轮流调 LLM 发言。
"""
import openai


class RobertTokenRingEngine:
    def __init__(self, base_url, api_key, article_text, scenario):
        self.client = openai.OpenAI(base_url=base_url, api_key=api_key)
        self.article = article_text or ""
        self.scenario = scenario
        self.shared_context = {}
        self._model = "nova-deepseek-v4-flash-aggr"

    def execute_speech(self, seat_info, instruction):
        name = seat_info.get("agent") or seat_info.get("en_key", "席位")
        avatar = (
            seat_info.get("avatars", {})
            .get(self.scenario, seat_info.get("avatars", {}).get("court", name))
        )
        model = seat_info.get("model") or self._model
        prompt = (
            f"你是【{avatar}】（席位：{name}）。当前场景：{self.scenario}\n"
            + (f"《极昼》文献参考：\n{self.article[:5000]}\n" if self.article else "")
            + ("共享上下文：\n" + "\n".join(
                f"- {k}: {str(v)[:400]}" for k, v in self.shared_context.items()
            ) + "\n" if self.shared_context else "")
            + f"你的任务：{instruction}\n"
            + "发言要求：沉静、严肃、有法理深度，不超 400 字。"
        )
        try:
            resp = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                timeout=55,
            )
            content = resp.choices[0].message.content.strip()
        except Exception as e:
            content = f"（{avatar} 引擎调用失败: {e}）"
        return (avatar, content)

    def draft_official_indictment(self):
        return (
            f"【起诉书】就《极昼》案，指控尊长（原中煤集团党组成员）"
            f"涉嫌违规参与民间借贷、利用职务影响力为亲友企业拆借资金（场景：{self.scenario}）。"
            f"具体指控与证据链由令牌环完整庭审生成。"
        )

    def add_to_shared_context(self, avatar, text):
        self.shared_context[str(avatar)] = text

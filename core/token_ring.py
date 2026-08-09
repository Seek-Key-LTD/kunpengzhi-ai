"""RobertTokenRingEngine — 完整令牌环庭审引擎（黄道内阁版）
从 6a5d8ee 原版逻辑适配 VAULT_ZODIAC_CABINETS 结构：
token_holder 令牌持有 / 定向接话共享上下文 / 前发言人陈词 / 极昼全量记忆。

互通策略（v2 定向接话，替代 v1 全量广播）：
- 起诉书锚点：全局唯一，始终注入（控方立场权威文本）
- 前一位发言人陈词：始终注入（后手必须接话）
- 同阵营既往陈词：按 team 定向注入（prosecutor/defense/judge/court）
- 小花组：普通成员只接前一位（独立维度防复读），violet 注入全部小花（汇总所需）

MVP 契约驱动：execute_contract() 消费 Session Contract（Coding Agent 编译产物），
取代 streamlit_app 里写死的 COURT_FLOW 循环。
"""
import datetime
import time
import openai


class RobertTokenRingEngine:
    def __init__(self, base_url, api_key, article_text, scenario="court"):
        self.client = openai.OpenAI(base_url=base_url, api_key=api_key)
        self.article_text = article_text or ""
        self.scenario = scenario
        self.token_holder = "ruby"          # 令牌初始在审判长（红宝石）手中
        self.shared_context = []            # 共享法庭笔录上下文 (Shared Memory)
        self.steps = []                     # 过程元数据：每步耗时/模型/上下文注入清单
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
    def draft_official_indictment(self, meta=None):
        """公诉机关起诉书。meta（Session Contract 的 meta 字段）存在时按素材插值。"""
        if meta:
            defendant = meta.get("defendant") or "被告人"
            charge = meta.get("charge") or "涉嫌违法犯罪"
            court = meta.get("court_name") or "人民法院"
            org = meta.get("prosecutor_org") or "检察机关"
            case_no = meta.get("case_number") or ""
            facts = meta.get("key_facts") or ""
            claim = meta.get("prosecution_claim") or ""
            case_str = f"（{case_no}）" if case_no else ""
            return (
                f"【起诉书】{org}就《{meta.get('title', '本案')}》案{case_str}，指控{defendant}涉嫌{charge}。"
                f"关键事实：{facts}。控方主张：{claim}。"
                f"（审理机构：{court}；完整指控与证据链由令牌环庭审逐阶段生成）"
            )
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
            f"\n【素材全量记忆】:\n{self.article_text[:18000]}\n"
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
        start_ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        t0 = time.time()
        try:
            resp = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                timeout=60,
            )
            content = resp.choices[0].message.content.strip()
            ok = True
        except Exception as e:
            content = f"（{header} 引擎调用失败: {e}）"
            ok = False
        self.steps.append({
            "seat": en_key,
            "header": header,
            "team": team,
            "model": model,
            "start_ts": start_ts,
            "duration_sec": round(time.time() - t0, 2),
            "chars": len(content),
            "ok": ok,
            "ctx": [{"label": label, "chars": len(c)} for label, c in blocks],
        })
        self.add_to_shared_context(header, content, team)
        return (header, content)

    # ---- 契约驱动执行（MVP：Coding Agent 编译的 Session Contract） ----
    @staticmethod
    def _avatar_for(seat_info):
        team = seat_info.get("team", "")
        if team == "judge":
            return "🏛️"
        if team == "prosecutor":
            return "⚖️"
        if team == "defense":
            return "🛡️"
        if team == "court":
            return "📜"
        return "👤" if seat_info.get("en_key") == "leopard" else "🌸"

    def execute_contract(self, contract, seat_registry, progress_cb=None, emit_cb=None):
        """按 Session Contract 执行全部 acts。
        seat_registry: {en_key: seat_info}（VAULT_ZODIAC_CABINETS + FLOWER_PLEIADES_TABLE + 附席）
        progress_cb(idx, total, act, header): 每步进度回调
        emit_cb(msg, idx, total, act): 每步发言产出回调（UI 实时落地用）
        返回 messages: [{role, header, content, avatar}]
        """
        acts = contract.get("acts", [])
        total = len(acts)
        messages = []
        for idx, act in enumerate(acts, 1):
            seat_key = act.get("seat")
            seat_info = seat_registry.get(seat_key)
            if seat_info is None:
                content = f"（席位 {seat_key} 未注册，跳过）"
                msg = {
                    "role": seat_key, "header": seat_key,
                    "content": content, "avatar": "❓",
                }
            else:
                header, content = self.execute_speech(seat_info, act.get("instruction", ""))
                msg = {
                    "role": header,
                    "header": header,
                    "content": content,
                    "avatar": self._avatar_for(seat_info),
                }
            messages.append(msg)
            if progress_cb:
                progress_cb(idx, total, act, msg["header"])
            if emit_cb:
                emit_cb(msg, idx, total, act)
        return messages

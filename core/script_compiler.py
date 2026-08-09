"""
Coding Agent（Underlay 编剧室）— 剧本编译管线
============================================
输入任意文本 → 输出可执行的 Session Contract：
    ① parse_source()    文章元数据与争议焦点解析（LLM ×1）
    ② bind_cast()       化身绑定（MVP：协议模板固定 12 石 7 花人格，只插值角色名）
    ③ mount_protocol()  协议挂载（按文章类型路由）
    ④ generate_acts()   阶段级议题编排（LLM ×1，不逐句台词）
    ⑤ validate_contract() 强制闸门（确定性校验，不走 LLM；失败回退内置契约）

成本：每次编译 2 次 LLM 调用，比庭审 21 步便宜一个数量级。
"""
from __future__ import annotations

import json
import logging

import openai

from .contract import (
    default_contract,
    validate_contract,
    summarize_contract,
    STAGE_COUNT,
    SEAT_WHITELIST,
)
from .protocols import get_protocol, route_protocol

logger = logging.getLogger(__name__)

_MODEL = "nova-deepseek-v4-flash-aggr"


class CompileError(Exception):
    pass


def _chat_json(client, prompt: str, model: str = _MODEL, timeout: int = 90) -> dict:
    """调 LLM 并严格解析 JSON 输出。解析失败抛 CompileError（上层回退）。"""
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        timeout=timeout,
    )
    text = resp.choices[0].message.content.strip()
    # 剥离可能的 ```json 代码块围栏
    if text.startswith("```"):
        text = text.split("```", 2)[1] if "```" in text[3:] else text[3:]
        text = text.strip().lstrip("json").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise CompileError(f"LLM 输出非 JSON: {e}\n---\n{text[:300]}")


def parse_source(client, article_text: str) -> dict:
    """① 文章元数据与争议焦点解析"""
    prompt = f"""你是鲲鹏志编剧室（Underlay）的剧本解析员。给定一篇文本（可能是案件材料/纪实/小说章节），抽取刑事法庭剧本所需的要素，只输出一个 JSON 对象（不要任何解释文字、不要 markdown 围栏）：

{{
  "title": "文本标题（若无法判断取前 8 字）",
  "source_type": "素材类型（如：留置案/纪实/小说章节/社会事件）",
  "defendant": "被告/主角姓名（无则空串）",
  "charge": "指控罪名或核心冲突（一句话）",
  "court_name": "审理机构（如：安徽省阜阳市中级人民法院；无法判断则空串）",
  "prosecutor_org": "控方/发起方（如：阜阳市人民检察院；无则空串）",
  "case_number": "案号（无则空串）",
  "key_facts": "2-3 条关键事实（分号分隔）",
  "prosecution_claim": "控方主张（指控的核心逻辑）",
  "defense_claim": "辩方主张（辩护的核心逻辑）",
  "focus": "争议焦点（一句话，法理/事实层面）"
}}

文本内容（前 6000 字）：
{article_text[:6000]}"""
    meta = _chat_json(client, prompt)
    for k in ["title", "defendant", "charge", "focus", "prosecution_claim", "defense_claim"]:
        meta.setdefault(k, "")
    meta.setdefault("source_type", "纪实")
    meta.setdefault("court_name", "")
    meta.setdefault("prosecutor_org", "")
    meta.setdefault("case_number", "")
    meta.setdefault("key_facts", "")
    return meta


def generate_acts(client, protocol: dict, meta: dict) -> list[dict]:
    """④ 阶段级议题编排：协议阶段模板 + 文章焦点 → 发言序列（不逐句台词）"""
    stage_lines = []
    for s in protocol["stage_flow"]:
        stage_lines.append(f"阶段 {s['id']}【{s['name']}】{s['desc']}")
    seat_lines = []
    for c in protocol["cast"]:
        seat_lines.append(f"{c['seat']}={c['role']}({c['team']})")
    stage_seats_lines = []
    for sid in sorted(protocol["stage_seats"]):
        stage_seats_lines.append(f"阶段 {sid}: {', '.join(protocol['stage_seats'][sid])}")

    prompt = f"""你是鲲鹏志编剧室（Underlay）的流程编剧。给定 5 阶段刑事法庭协议与案件要素，为每阶段编排「发言序列」。

【5 阶段协议】：
{chr(10).join(stage_lines)}

【席位表】（seat=角色，含阵营）：
{chr(10).join(seat_lines)}

【各阶段可出场席位】：
{chr(10).join(stage_seats_lines)}

【本案要素】：
标题：{meta.get('title')}
案由：{meta.get('charge')}
被告：{meta.get('defendant')}
控方主张：{meta.get('prosecution_claim')}
辩方主张：{meta.get('defense_claim')}
关键事实：{meta.get('key_facts')}
争议焦点：{meta.get('focus')}

【编排规则】：
1. 每阶段按该阶段席位表出场；同一席位每阶段至多 1 次发言（阶段 4 可让控辩核心席位 carbonado/diamond 二次回应合议庭质询）
2. 每项指令写清「该席位在此阶段的具体行动」，必须落到本案事实（具体罪名/证据/主张），禁止泛泛而谈
3. 审判长 ruby 开场（阶段 1）与宣判（阶段 5）必须有；被告 leopard 在阶段 1 应答、阶段 5 最后陈述
4. 阶段 4 必须有 7 位花仙子（meigui/qiangwei/tumi/zhuyu/moli/muxu/violet）的合议评议，violet 最后汇总
5. 指令 40-100 字；语气沉静严肃

只输出一个 JSON 数组（不要解释、不要 markdown 围栏），每项为：
{{"stage": 阶段号1-5, "seat": "席位en_key", "instruction": "行动指令"}}"""
    acts = _chat_json(client, prompt)
    if not isinstance(acts, list):
        raise CompileError("acts 应为 JSON 数组")
    return acts


def compile_contract(
    article_text: str,
    base_url: str,
    api_key: str,
    *,
    model: str = _MODEL,
    source_type: str = "",
) -> dict:
    """完整编译管线：解析 → 挂载协议 → 编排 → 校验（失败回退内置契约）。"""
    client = openai.OpenAI(base_url=base_url, api_key=api_key)

    # ③ 协议挂载（先路由，解析后可再校正）
    proto_id = route_protocol(article_text, source_type)
    protocol = get_protocol(proto_id)

    try:
        # ① 解析
        meta = parse_source(client, article_text)
        meta["source_type"] = source_type or meta.get("source_type", "")

        # ② 化身绑定（MVP：协议固定人格映射；角色名用 meta 校正）
        cast = []
        for c in protocol["cast"]:
            item = dict(c)
            if c["seat"] == "leopard" and meta.get("defendant"):
                item["role"] = f"被告人·{meta['defendant']}"
            if c["seat"] == "topaz" and meta.get("prosecutor_org"):
                item["role"] = f"{meta['prosecutor_org']}公诉人"
            cast.append(item)

        # ④ 阶段级议题编排
        acts = generate_acts(client, protocol, meta)

        contract = {
            "protocol": proto_id,
            "meta": meta,
            "stage_flow": protocol["stage_flow"],
            "cast": cast,
            "acts": acts,
            "constraints": protocol["constraints"],
            "token_policy": protocol["token_policy"],
        }

        ok, problems = validate_contract(contract)
        if not ok:
            logger.warning("契约校验未通过，回退内置极昼契约: %s", problems[:3])
            fb = default_contract()
            fb["meta"]["compile_note"] = f"编译校验失败({problems[0]})，已回退内置极昼契约"
            return fb
        return contract
    except CompileError as e:
        logger.warning("编译失败，回退内置契约: %s", e)
        fb = default_contract()
        fb["meta"]["compile_note"] = f"编译失败({str(e)[:60]})，已回退内置极昼契约"
        return fb
    except Exception as e:  # 网络/LLM 全面兜底
        logger.warning("编译异常，回退内置契约: %s", e)
        fb = default_contract()
        fb["meta"]["compile_note"] = f"编译异常({str(e)[:60]})，已回退内置极昼契约"
        return fb


if __name__ == "__main__":
    # 自测：契约校验
    ok, probs = validate_contract(default_contract())
    print("默认契约校验:", "✅ 通过" if ok else probs)
    print()
    print(summarize_contract(default_contract()))

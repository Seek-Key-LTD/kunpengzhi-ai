"""
协议注册表 — 按文章类型挂载议事协议（Flow Protocol）
====================================================
MVP：criminal_court 一个协议。结构：阶段模板 + 席位分布 + 发言序列编排规则。
后续扩展：treaty_negotiation（国际条约谈判）、academic_debate（学术辩论）等。
"""
from __future__ import annotations

from .contract import default_stage_flow, default_cast

# 每阶段应出现的席位（编译器编排 acts 时的约束参考）
CRIMINAL_COURT_STAGE_SEATS = {
    1: ["ruby", "leopard"],
    2: ["ruby", "topaz", "carbonado", "obsidian"],
    3: ["diamond", "jasper", "quartz", "argentite"],
    4: ["luna", "azure", "emerald", "carbonado", "diamond",
        "meigui", "qiangwei", "tumi", "zhuyu", "moli", "muxu", "violet"],
    5: ["leopard", "ruby"],
}

CRIMINAL_COURT_PROTOCOL = {
    "id": "criminal_court",
    "name": "刑事模拟法庭协议",
    "source_types": ["留置案", "刑事案", "职务犯罪", "庭审", "court"],
    "stage_flow": default_stage_flow(),
    "cast": default_cast(),
    "stage_seats": CRIMINAL_COURT_STAGE_SEATS,
    "constraints": {"max_speech_chars": 400, "tone": "沉静、严肃、有法理深度"},
    "token_policy": "fixed_order",
    "stage_topics": {
        1: "准备与核对身份：审判长宣布开庭、核对被告人基本信息、告知回避权",
        2: "控方起诉与举证：公诉机关宣读起诉书、出示指控证据与监察卷宗",
        3: "辩方无罪质证：辩护团队逐项反驳指控、出示无罪证据与法理依据",
        4: "法庭辩论与质询：合议庭追问关键争议、控辩正面交锋、专家合议评议",
        5: "陈述与宣判：被告人最后陈述、审判长逐项检验要件后宣判",
    },
}

PROTOCOLS = {
    "criminal_court": CRIMINAL_COURT_PROTOCOL,
}

# 协议默认路由（MVP：按关键词粗路由，未命中默认刑事法庭）
SOURCE_TYPE_KEYWORDS = {
    "criminal_court": ["留置", "监委", "起诉书", "法院", "庭审", "职务犯罪", "受贿", "公诉"],
}


def route_protocol(source_text: str = "", source_type: str = "") -> str:
    """按文章类型挂载协议。MVP：关键词粗路由，未命中回退 criminal_court。"""
    haystack = (source_text or "")[:3000] + " " + (source_type or "")
    for proto_id, keywords in SOURCE_TYPE_KEYWORDS.items():
        if any(k in haystack for k in keywords):
            return proto_id
    return "criminal_court"  # MVP 默认


def get_protocol(proto_id: str) -> dict:
    return PROTOCOLS.get(proto_id, CRIMINAL_COURT_PROTOCOL)

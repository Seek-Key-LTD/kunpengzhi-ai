"""
Session Contract — Coding Agent（Underlay 编剧室）编译产物数据模型
=================================================================
契约 = 可执行的数据（不是代码）。Overlay（Acting Agent / token ring）消费它开演。

结构：
    protocol      : 协议类型（criminal_court / treaty_negotiation / ...）
    meta          : 文章元数据（标题/被告/罪名/争议焦点/控辩主张...）
    stage_flow    : 阶段流 [{id, name, emoji, desc}]
    cast          : 席位映射 [{seat, archetype, role, team}]
    acts          : 发言序列 [{stage, seat, instruction}]（阶段级议题，不逐句台词）
    constraints   : 硬约束（字数/语气）
    token_policy  : 令牌策略（MVP: fixed_order；动态令牌环为 #6 预留）
"""
from __future__ import annotations

# 席位白名单（协议可引用的 en_key —— 与 streamlit_app 的座位表一致）
SEAT_WHITELIST = {
    # 12 黄道内阁
    "ruby", "topaz", "amber", "emerald", "azure", "diamond",
    "obsidian", "jasper", "carbonado", "argentite", "agate", "quartz",
    # 附席
    "luna", "leopard",
    # 昴宿七姐妹
    "meigui", "qiangwei", "tumi", "zhuyu", "moli", "muxu", "violet",
}

STAGE_COUNT = 5


def default_stage_flow() -> list[dict]:
    """刑事法庭协议的标准阶段流（刑事诉讼法流程）"""
    return [
        {"id": 1, "name": "1. 准备与核对身份", "emoji": "⚖️", "desc": "审判长核对被告人基本信息，告知回避权，被告人现场应答"},
        {"id": 2, "name": "2. 控方起诉与举证", "emoji": "📜", "desc": "公诉机关宣读起诉书并出示证据"},
        {"id": 3, "name": "3. 辩方无罪质证", "emoji": "🛡️", "desc": "辩护团队针对指控逐项质证答辩"},
        {"id": 4, "name": "4. 法庭辩论与质询", "emoji": "⚔️", "desc": "合议庭追问，控辩双方交锋，专家合议"},
        {"id": 5, "name": "5. 陈述与宣判", "emoji": "🏛️", "desc": "被告人最后陈述，审判长敲响法槌宣判"},
    ]


def default_cast() -> list[dict]:
    """刑事法庭协议的默认席位映射（12 石 7 花固定人格，绑定原型不绑定职务）"""
    return [
        {"seat": "ruby",      "archetype": "judge",      "role": "审判长",     "team": "judge"},
        {"seat": "azure",     "archetype": "judge",      "role": "审判员",     "team": "judge"},
        {"seat": "luna",      "archetype": "judge",      "role": "审判员",     "team": "judge"},
        {"seat": "topaz",     "archetype": "prosecutor", "role": "首席公诉人", "team": "prosecutor"},
        {"seat": "carbonado", "archetype": "prosecutor", "role": "助理公诉人", "team": "prosecutor"},
        {"seat": "obsidian",  "archetype": "prosecutor", "role": "监察特派员", "team": "prosecutor"},
        {"seat": "diamond",   "archetype": "defense",    "role": "首席辩护律师", "team": "defense"},
        {"seat": "jasper",    "archetype": "defense",    "role": "资深合规官", "team": "defense"},
        {"seat": "quartz",    "archetype": "defense",    "role": "法理分析员", "team": "defense"},
        {"seat": "argentite", "archetype": "defense",    "role": "伦理质证员", "team": "defense"},
        {"seat": "emerald",   "archetype": "court",      "role": "资产审计师", "team": "court"},
        {"seat": "amber",     "archetype": "court",      "role": "庭审书记员", "team": "court"},
        {"seat": "leopard",   "archetype": "defendant",  "role": "被告人",     "team": "defendant"},
        {"seat": "meigui",    "archetype": "flower",     "role": "程序合议员", "team": "flower"},
        {"seat": "qiangwei",  "archetype": "flower",     "role": "证据合议员", "team": "flower"},
        {"seat": "tumi",      "archetype": "flower",     "role": "常情合议员", "team": "flower"},
        {"seat": "zhuyu",     "archetype": "flower",     "role": "谦抑合议员", "team": "flower"},
        {"seat": "moli",      "archetype": "flower",     "role": "舆情合议员", "team": "flower"},
        {"seat": "muxu",      "archetype": "flower",     "role": "伦理合议员", "team": "flower"},
        {"seat": "violet",    "archetype": "flower",     "role": "合议汇总人", "team": "flower"},
    ]


def default_contract() -> dict:
    """内置《极昼》契约 —— 零 LLM 回退，行为与既有硬编码 COURT_FLOW 一致"""
    return {
        "protocol": "criminal_court",
        "meta": {
            "title": "极昼",
            "source_type": "留置案",
            "defendant": "尊长",
            "charge": "利用影响力受贿罪、国有公司人员失职罪",
            "court_name": "安徽省阜阳市中级人民法院",
            "prosecutor_org": "阜阳市人民检察院",
            "case_number": "阜检刑诉〔2026〕88号",
            "key_facts": "2016年春节尊长筹措1000万划转亲家企业，分10次平价还本；2026年8月3日被带至阜阳留置",
            "prosecution_claim": "构成利用影响力受贿罪与失职罪，职务影响隐形背书、破窗效应",
            "defense_claim": "四大罪名排除矩阵：资金闭环零亏空、从旧兼从轻、程序瑕疵非罪",
            "focus": "利用影响力与私人信用的边界；《刑法》第12条从旧兼从轻对2016年4月新司法解释的阻断效力",
        },
        "stage_flow": default_stage_flow(),
        "cast": default_cast(),
        "acts": [
            {"stage": 1, "seat": "ruby", "instruction": "敲响法槌！宣布：‘安徽省阜阳市中级人民法院刑事审判第一庭，现在开庭！带被告人尊长到庭！’核对尊长基本信息，告知回避权！"},
            {"stage": 1, "seat": "leopard", "instruction": "【被告人尊长实时应答】回答：‘报告审判长，我叫尊长，原中煤党组成员，2026年8月3日被带至阜阳留置... 身份属实！听清了权利，不申请回避！’"},
            {"stage": 2, "seat": "ruby", "instruction": "宣布准备结束，请阜阳市检察院公诉团队宣读《阜检刑诉〔2026〕88号起诉书》！"},
            {"stage": 2, "seat": "topaz", "instruction": "宣读《阜检刑诉〔2026〕88号起诉书》：指控2016年春节尊长筹措1000万划转亲家企业，构成利用影响力受贿罪与失职罪！"},
            {"stage": 2, "seat": "carbonado", "instruction": "受公诉人指派主动进攻质证：抓住辩方尚未回答的三个命门逐一逼问——①1000万为何借道第三方筹集、分10次归还，若问心无愧为何不堂堂正正走公开程序？②尊长作为党组成员，是否向组织报备过此次筹资？不报备本身就是对‘职务影响可能外溢’的明知！③水单只是归还记录，谁证明筹款来源清白？要求辩方当庭出示筹款来源凭证！语气沉静但刀刀见血，绝不自我软化！"},
            {"stage": 2, "seat": "obsidian", "instruction": "【黑曜石监察特派员】监察法务补强举证：强调监委调查留置移送卷宗合规性！"},
            {"stage": 3, "seat": "diamond", "instruction": "发表无罪答辩：针对起诉书，掏出《极昼.md》【四大罪名排除矩阵】与1000万10次平价还本水单书证！"},
            {"stage": 3, "seat": "jasper", "instruction": "【碧石大律师 (vault LXC)】补充资深合规辩护：引用《刑法》第12条从旧兼从轻原则，阻断2016年4月新司法解释的违宪追溯！"},
            {"stage": 3, "seat": "quartz", "instruction": "法理分析：证明主观非法占有目的为零，客观中煤财产零亏空！"},
            {"stage": 3, "seat": "argentite", "instruction": "伦理与法理双重质证：还原2015-2016山河四省最冷冬天背景，致敬时代的承重梁！"},
            {"stage": 4, "seat": "luna", "instruction": "【合议庭质询】审判员月华石发难质询：追问公诉人有无公款损失凭证，追问辩护人如何证明脱离职务影响？"},
            {"stage": 4, "seat": "azure", "instruction": "【合议庭质询】审判员天蓝石质询：要求控辩双方说明从旧兼从轻在2016年2月行为着手点的适用边界！"},
            {"stage": 4, "seat": "emerald", "instruction": "【资产审计质询】祖母绿审计师核查账目审计书证！"},
            {"stage": 4, "seat": "carbonado", "instruction": "【回应合议庭质询】必须正面回答审判员关于‘损失凭证’的质询：失职罪的构成不以损失已现实发生为限，监委调查终结认定的‘重大损失风险’即为损害后果；并反守为攻，提请法庭注意：辩方至今未能解释借道第三方与不报备的程序缺口。不得回避质询，不得答非所问！"},
            {"stage": 4, "seat": "diamond", "instruction": "【回应合议庭质询】必须正面回答审判员关于‘脱离职务影响’的质询：论证标准为三项排除——未动用公章、未批公文、未动用公权意志，资金全程在私人信用网络闭环流转；并回应公诉人逼问：借道第三方系因2016年银行全面抽贷的金融现实，报备并非刑事义务。不得回避质询！"},
            {"stage": 4, "seat": "meigui", "instruction": "你是昴宿一【玫瑰】。针对庭审发表程序合议评议：复核阜阳留置与最高法指定管辖程序，重点评议《刑法》第12条从旧兼从轻对2016年4月新规的阻断效力！"},
            {"stage": 4, "seat": "qiangwei", "instruction": "你是昴宿二【蔷薇】。针对庭审发表实体证据合议评议：复核1000万10次平价还本水单，确认中煤账目零亏空，认定四大罪名完全不成立！"},
            {"stage": 4, "seat": "tumi", "instruction": "你是昴宿三【荼蘼】。针对庭审发表社会常情合议评议：还原2015-2016山河四省最冷冬天的真实背景，认定尊长救助亲家属于无罪义举！"},
            {"stage": 4, "seat": "zhuyu", "instruction": "你是昴宿四【茱萸】。针对庭审发表刑法谦抑性评议：强调无财物收受与权钱交易对价时，不得以道德或拟制罪名构陷无辜！"},
            {"stage": 4, "seat": "moli", "instruction": "你是昴宿五【茉莉】。针对庭审发表舆情公信评议：评估本案公开审判的社会观感与程序公信力，指出程序瑕疵与实体无罪的界限！"},
            {"stage": 4, "seat": "muxu", "instruction": "你是昴宿六【苜蓿】。针对庭审发表伦理合议评议：辨析‘救急不救穷’的私人道义与公职廉洁义务之间的张力，为合议庭提供伦理参照！"},
            {"stage": 4, "seat": "violet", "instruction": "你是昴宿七【紫罗兰】（Flower Manager）。汇总六位花仙子的合议意见，给出权威专家合议结论书：事实层面资金闭环无亏空，程序层面存在‘未报备’瑕疵——法理与情理在此对峙，供合议庭参考！"},
            {"stage": 5, "seat": "leopard", "instruction": "【被告人尊长最后陈述】发表最后陈述：‘在阜阳留置室的这半年极昼里我问心无愧，我救的是企业和工人，未占公家一分钱！’"},
            {"stage": 5, "seat": "ruby", "instruction": "收回发言权！发表判词：必须逐项检验两项罪名的构成要件——①利用影响力受贿罪：有无财物对价？尊长系借出方而非收受方，权力与财物是否发生交换？②国有公司人员失职罪：有无‘重大损失’这一实害要件？‘风险’能否替代‘损失’？每一要件均须给出明确判断，然后依据《刑事诉讼法》第二百条第（二）项或第一百九十五条第（一）项作出有罪或无罪结论——结论必须基于要件检验的结果，不得预设立场！"},
        ],
        "constraints": {"max_speech_chars": 400, "tone": "沉静、严肃、有法理深度"},
        "token_policy": "fixed_order",
    }


def validate_contract(contract: dict) -> tuple[bool, list[str]]:
    """确定性校验（强制闸门，不走 LLM）。返回 (是否通过, 问题清单)。"""
    problems = []
    if not isinstance(contract, dict):
        return False, ["契约不是 dict"]
    acts = contract.get("acts") or []
    stages = contract.get("stage_flow") or []

    # 阶段流：5 阶段编号 1..5 连续
    if len(stages) != STAGE_COUNT:
        problems.append(f"阶段数应为 {STAGE_COUNT}，实为 {len(stages)}")
    else:
        for i, s in enumerate(stages, 1):
            if s.get("id") != i:
                problems.append(f"阶段 {i} 编号错位: {s.get('id')}")

    # acts 非空、stage 合法、seat 在白名单
    if not acts:
        problems.append("acts 为空——没有发言序列")
    stage_ids = {s.get("id") for s in stages}
    for idx, a in enumerate(acts):
        if a.get("stage") not in stage_ids:
            problems.append(f"acts[{idx}] stage={a.get('stage')} 不在阶段流中")
        if a.get("seat") not in SEAT_WHITELIST:
            problems.append(f"acts[{idx}] seat={a.get('seat')} 不在席位白名单")
        if not (a.get("instruction") or "").strip():
            problems.append(f"acts[{idx}] 指令为空")

    # 结构约束：审判长开场与收场
    if acts and acts[0].get("seat") != "ruby":
        problems.append("阶段 1 首发言席应为 ruby（审判长开场）")
    last_act = acts[-1] if acts else {}
    if last_act.get("seat") != "ruby":
        problems.append("末位发言席应为 ruby（审判长宣判收场）")

    return (len(problems) == 0), problems


def summarize_contract(contract: dict) -> str:
    """契约摘要（展示给用户看）"""
    meta = contract.get("meta", {})
    stages = contract.get("stage_flow", [])
    acts = contract.get("acts", [])
    by_stage = {}
    for a in acts:
        by_stage.setdefault(a["stage"], []).append(a["seat"])
    lines = [
        f"🎭 协议：{contract.get('protocol')}",
        f"📰 素材：{meta.get('title', '?')}（{meta.get('source_type', '?')}）",
        f"⚖️ 案由：{meta.get('charge', '?')}",
        f"🎯 争议焦点：{meta.get('focus', '?')}",
        f"📜 阶段流：{' → '.join(s['name'] for s in stages)}",
        f"🗣️ 发言序列：{len(acts)} 幕",
    ]
    for s in stages:
        seats = by_stage.get(s["id"], [])
        lines.append(f"  · 阶段 {s['id']}：{len(seats)} 席（{', '.join(seats)}）")
    return "\n".join(lines)

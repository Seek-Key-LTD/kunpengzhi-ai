"""
《极昼》案 10 席位沉静严肃法庭引擎（阜阳中院 · 令牌环）
========================================================
从 streamlit_app.py 抽取的纯逻辑层（无 UI 依赖），供网页与 headless CLI 共用。

- SEATS_DICT: 10 席位物理节点与模型映射
- ROBERTS_STEPS: 11 步令牌环庭审流程（罗伯特议事规则）
- RobertTokenRingEngine: 共享上下文 + 令牌发言执行器 + 独立起诉书撰写
"""

import datetime
import time

import openai

OPENAI_BASE_URL = "https://litellm.capitaltrain.cn/v1"

# 10 席位定义（阜阳中院 · 含被告人尊长 leopard@suse）
SEATS_DICT = {
    "judge_chief": {
        "role": "🏛️ 审判长",
        "agent": "ruby",
        "node": "nuc",
        "model": "nova-deepseek-v4-flash-aggr",
        "team": "judge"
    },
    "defendant": {
        "role": "👤 被告人 (尊长)",
        "agent": "leopard",
        "node": "suse",
        "model": "azure-deepseek-v4-flash",
        "team": "defendant"
    },
    "prosecutor_chief": {
        "role": "⚖️ 首席公诉人 (阜阳市检察院)",
        "agent": "topaz",
        "node": "raccoon",
        "model": "topaz-deepseek-v4-flash",
        "team": "prosecutor"
    },
    "prosecutor_asst1": {
        "role": "⚖️ 助理公诉人 1",
        "agent": "carbonado",
        "node": "pve2",
        "model": "carbonado-deepseek-v4-flash",
        "team": "prosecutor"
    },
    "defense_chief": {
        "role": "🛡️ 首席辩护律师",
        "agent": "diamond",
        "node": "pve",
        "model": "diamond-deepseek-v4-flash",
        "team": "defense"
    },
    "defense_asst1": {
        "role": "🛡️ 辩护助理 1",
        "agent": "argentite",
        "node": "pve3",
        "model": "argentite-deepseek-v4-flash",
        "team": "defense"
    },
    "defense_asst2": {
        "role": "🛡️ 辩护助理 2",
        "agent": "agate",
        "node": "xgp",
        "model": "agate-deepseek-v4-flash",
        "team": "defense"
    },
    "judge_a": {
        "role": "🏛️ 审判员 A (常理)",
        "agent": "luna",
        "node": "onecloud2",
        "model": "azure-deepseek-v4-flash",
        "team": "judge"
    },
    "judge_b": {
        "role": "🏛️ 审判员 B (程序)",
        "agent": "meigui",
        "node": "ash1",
        "model": "azure-deepseek-v4-flash",
        "team": "judge"
    }
}

# 11 步令牌环庭审流程（阜阳案 · 沉静严肃）
ROBERTS_STEPS = [
    ("judge_chief", "敲响法槌！宣布：‘安徽省阜阳市中级人民法院刑事审判第一庭，现在开庭！带被告人尊长到庭！’现场核对尊长基本信息（2026年8月3日带至阜阳留置等），告知诉讼权利与回避权，将令牌派给被告人！"),
    ("defendant", "【被告人尊长实时应答】向审判长明确回答：‘报告审判长，我叫尊长，原中煤集团党组成员，退休两年。2026年8月3日被带至安徽阜阳留置... 身份属实！我听清了权利，不申请回避！’归还令牌！"),
    ("judge_chief", "收回令牌！宣布法庭准备结束，正式进入法庭调查阶段，请安徽省阜阳市人民检察院公诉人宣读刚刚独立撰写完成的《阜检刑诉〔2026〕88号起诉书》！将令牌派发给首席公诉人！"),
    ("prosecutor_chief", "拿到了令牌！宣读《阜检刑诉〔2026〕88号起诉书》：说明由阜阳市监委调查终结移送起诉，指控2016年春节尊长利用职务影响筹措1000万划转亲家企业，构成利用影响力受贿罪与失职罪！归还令牌！"),
    ("prosecutor_asst1", "受公诉人指派补充举证：强调职务影响与私情拆借的隐形背书与破窗效应！归还令牌！"),
    ("defense_chief", "拿到了令牌！发表全盘无罪答辩：针对阜阳起诉书，掏出《极昼.md》【四大罪名排除矩阵】与1000万10次平价还本水单书证！归还令牌！"),
    ("defense_asst1", "补充辩护：引用《刑法》第12条从旧兼从轻原则，阻断2016年4月新司法解释在阜阳案中的违宪追溯！归还令牌！"),
    ("defense_asst2", "还原2015-2016山河四省最冷冬天背景，致敬时代的承重梁！归还令牌！"),
    ("judge_a", "合议庭审判员A发难质询：追问阜阳公诉人有无公款损失凭证，追问辩护人如何证明脱离职务影响？归还令牌！"),
    ("defendant", "【被告人尊长最后陈述】发表最后陈述：‘在阜阳留置室的这半年极昼里我问心无愧，我救的是企业和工人，未占公家一分钱！’归还令牌！"),
    ("judge_chief", "收回令牌！综合合议庭评议，敲响法槌，宣告被告人尊长无罪，发表判词！")
]


class RobertTokenRingEngine:
    """令牌环法庭引擎：共享上下文 (Shared Memory) + 令牌发言执行"""

    def __init__(self, base_url, api_key, article_text=""):
        self.client = openai.OpenAI(base_url=base_url, api_key=api_key)
        self.article_text = article_text
        self.shared_context = []
        self.steps = []

    def add_to_shared_context(self, seat_key, content, team=None):
        seat = SEATS_DICT[seat_key]
        header = f"{seat['role']} ({seat['agent']} @ {seat['node']})"
        team = team if team is not None else seat.get("team", "")
        self.shared_context.append({"seat_key": seat_key, "header": header, "content": content, "team": team})

    def get_shared_context_str(self):
        return "\n\n".join(f"【{m['header']}】:\n{m['content']}" for m in self.shared_context)

    def _build_context_blocks(self, seat_key):
        """定向接话上下文：起诉书锚 + 前一位陈词 + 同阵营既往陈词。"""
        seat = SEATS_DICT[seat_key]
        team = seat.get("team", "")
        blocks = []
        for m in self.shared_context:
            if m.get("team") == "indictment":
                blocks.append(("起诉书（全局控方立场锚）", m["content"]))
                break
        if self.shared_context and self.shared_context[-1].get("team") != "indictment":
            last = self.shared_context[-1]
            blocks.append((f"前一位发言人 ({last['header']}) 的具体陈词", last["content"]))
        if team and team != "flower":
            last_header = self.shared_context[-1]["header"] if self.shared_context else ""
            same = [m for m in self.shared_context
                    if m.get("team") == team and m["header"] != last_header]
            blocks += [(f"同阵营既往陈词 ({m['header']})", m["content"]) for m in same]
        return blocks

    def draft_official_indictment(self):
        """公诉机关独立自主撰写完整起诉书"""
        prompt = (
            "你是安徽省阜阳市人民检察院首席公诉人。请以正式公文格式自主撰写《安徽省阜阳市人民检察院起诉书》（字号：阜检刑诉〔2026〕88号）。\n"
            "案卷根据《极昼.md》：\n"
            "被告人尊长，男，196X年生，原中煤集团党组成员，退休两年，2026年8月3日被带至安徽省阜阳市由阜阳市监察委员会留置并调查终结移送起诉。\n"
            "指控事实：2016年春节，尊长筹集1000万元划转至其亲家民营房企账户化解爆雷危机，分10次平价还本。\n"
            "指控罪名：利用影响力受贿罪、国有公司人员失职罪。\n"
            "格式要求：标准公文格式，字数400字左右，严谨严肃。"
        )
        try:
            resp = self.client.chat.completions.create(
                model=SEATS_DICT["prosecutor_chief"]["model"],
                messages=[{"role": "user", "content": prompt}],
                timeout=55
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            return f"起诉书生成异常: {e}"

    def execute_token_speech(self, seat_key, specific_instruction):
        seat = SEATS_DICT[seat_key]
        header = f"{seat['role']} ({seat['agent']} @ {seat['node']})"

        blocks = self._build_context_blocks(seat_key)
        ctx_str = "\n\n".join(f"【{label}】:\n{content}" for label, content in blocks) or "(刚开场)"

        doc_mem = f"\n【《极昼.md》案卷记忆】:\n{self.article_text[:18000]}\n" if self.article_text else ""

        prompt_user = (
            f"你是模拟法庭角色：【{header}】。\n"
            f"你当前持有【法庭发言令牌 Token】！\n"
            f"{doc_mem}\n"
            f"【定向接话上下文 (Shared Memory)】:\n{ctx_str}\n"
            f"你的具体庭审任务：{specific_instruction}\n\n"
            f"💥 沉静严肃·人文关怀庭审指令：\n"
            f"1. 严格尊重《极昼.md》案卷真实事实：尊长于2026年8月3日从住处被带走送至【安徽省阜阳市】留置！起诉机关为【安徽省阜阳市人民检察院】！\n"
            f"2. 语言必须极其沉静、严肃、专业，带有法理温度与力量，严禁急躁喧嚣！\n"
            f"3. 发言完毕后，宣告归还令牌给审判长。字数控制在 380 字以内。"
        )

        system_prompt = (
            "【安徽省阜阳市中级人民法院 沉静法庭沙盒】你正在参加安徽省阜阳市中级人民法院《极昼》案公开审理。"
            "本案关乎一个人、一个家族与时代的承重。请以极其严肃专业、沉静有力的语气陈词与答辩。"
        )

        start_ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        t0 = time.time()
        try:
            resp = self.client.chat.completions.create(
                model=seat["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt_user}
                ],
                timeout=55
            )
            content = resp.choices[0].message.content.strip()
            ok = True
        except Exception as e:
            content = f"（{header} 连线超时: {e}）"
            ok = False

        self.steps.append({
            "seat": seat_key,
            "header": header,
            "team": seat.get("team", ""),
            "model": seat["model"],
            "start_ts": start_ts,
            "duration_sec": round(time.time() - t0, 2),
            "chars": len(content),
            "ok": ok,
            "ctx": [{"label": label, "chars": len(c)} for label, c in blocks],
        })
        self.add_to_shared_context(seat_key, content)
        return header, content

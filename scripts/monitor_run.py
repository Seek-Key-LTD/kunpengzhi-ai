#!/usr/bin/env python3
"""
🦅 鲲鹏志 · 《极昼》案 监委旁听评估 headless CLI（Event 3）
==========================================================
事件链：庭前会议 (pretrial_run.py) → 庭审 (court_run.py) → 监委旁听评估（本脚本）

天蝎宫监察线（旁听席 · 不参与庭审）：办案组组长 + 审理室干部
产出：指控成立性评估 + 量刑建议风险评估 + 私语情报交换（可审计情报流）

用法:
    uv run python scripts/monitor_run.py --trial 擂台存档/擂台-极昼-阜阳中院-*.md
"""

import argparse
import asyncio
import datetime
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import openai

OPENAI_BASE_URL = "https://litellm.capitaltrain.cn/v1"

# 天蝎宫监察线 · 旁听席（不进入庭审令牌环）
SEATS_SURVEILLANCE = {
    "suveilant_chief": {
        "role": "🎭 监委办案组组长 (旁听席)",
        "agent": "obsidian",
        "node": "pve2",
        "model": "azure-deepseek-v4-flash",
        "team": "suveilant",
    },
    "suveilant_review": {
        "role": "🎭 监委审理室干部 (旁听席)",
        "agent": "onyx",
        "node": "ash2",
        "model": "azure-deepseek-v4-flash",
        "team": "suveilant",
    },
}

STEPS = [
    ("suveilant_chief", "【旁听评估·办案组视角】你以安徽省阜阳市监委办案组组长身份全程旁听庭审。现在出具《指控成立性评估》：①两项罪名（利用影响力受贿罪/国有公司人员失职罪）在法庭交锋后的成立概率分别评估；②证据软肋清单——庭审中哪份证据被辩方攻击得最危险、回程流水补交是否补上了漏洞；③若指控不成立，调查环节哪里出了问题（侦查方向、证据固定、程序瑕疵）。直接陈述，不客套，措辞专业冷静。"),
    ("suveilant_review", "【旁听评估·审理室视角】你以安徽省阜阳市监委审理室干部身份全程旁听庭审。现在出具《量刑建议风险评估》：①若公诉提出量刑建议，本案合适的建议区间（考虑利用影响力受贿罪与失职罪数罪并罚的量刑逻辑）；②量刑建议过高被法院拒绝乃至判无罪的风险评估——无罪判决一旦生效，对公诉与监委的公信力损失；③监检衔接建议——庭前与公诉人交换情报时，应共享哪些调查底牌（卷宗里有但公诉未当庭用上的证据）。直接陈述，不客套。"),
    ("suveilant_chief", "【私语情报交换·办案组→审理室】两人在旁听席低声交换情报。你（办案组长）先说：向审理室干部透露调查阶段的底牌——卷宗里还有哪些公诉人没用上的弹药（如完整资金闭环流水、某出借人补充证言、同步录音录像中被告人的某句话），以及你对庭审风险的判断。就事论事，像两个同事在会场角落里说话，不得客套。"),
    ("suveilant_review", "【私语情报交换·审理室→办案组】你（审理室干部）回应办案组长：结合量刑博弈现实，指出公诉在这场庭审里的最大风险点（法院不采纳指控的后果、哪种判法会让检察院考核难看），并给出建议——庭后应向公诉方传递哪几条情报、量刑建议应如何调整方向。就事论事，像两个同事交换意见，不得客套。"),
]


async def main():
    parser = argparse.ArgumentParser(description="《极昼》案监委旁听评估（Event 3）")
    parser.add_argument("--trial", required=True, help="庭审存档 md 路径")
    args = parser.parse_args()

    trial_path = Path(args.trial)
    trial_md = trial_path.read_text(encoding="utf-8")

    base_url = os.getenv("OPENAI_BASE_URL", OPENAI_BASE_URL)
    api_key = os.getenv("OPENAI_API_KEY", "sk-47318")
    client = openai.OpenAI(base_url=base_url, api_key=api_key)

    records = []
    shared = []
    steps = []

    for idx, (seat_key, instruction) in enumerate(STEPS, 1):
        seat = SEATS_SURVEILLANCE[seat_key]
        header = f"{seat['role']} ({seat['agent']} @ {seat['node']})"

        ctx_str = "\n\n".join(
            f"【{m['header']}】:\n{m['content']}" for m in shared) or "(开场)"

        system_prompt = (
            "【监委旁听席】你以安徽省阜阳市监察委员会工作人员身份，在阜阳市中级人民法院《极昼》案"
            "庭审现场旁听席列席。你只观察、不发言；旁听期间与同事低声交换看法。"
            "请以专业、冷静、就事论事的内部工作口吻陈述，去掉一切仪式性客套。"
        )
        prompt_user = (
            f"你是：【{header}】。\n"
            f"【庭审实录（节选）】:\n{trial_md[:22000]}\n"
            f"【旁听席此前交流】:\n{ctx_str}\n"
            f"你的任务：{instruction}\n\n"
            f"💥 风格指令：\n"
            f"1. 这是监委内部评估，不是法庭发言：不要使用‘审判长’‘令牌’‘法槌’等庭审仪式措辞；\n"
            f"2. 就事论事，紧扣证据、程序、量刑与公信力风险，不进行价值煽情；\n"
            f"3. 字数控制在 450 字以内。"
        )

        start_ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        t0 = time.time()
        try:
            resp = client.chat.completions.create(
                model=seat["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt_user},
                ],
                timeout=55,
            )
            content = resp.choices[0].message.content.strip()
            ok = True
        except Exception as e:
            content = f"（{header} 连线超时: {e}）"
            ok = False

        steps.append({
            "seat": seat_key,
            "header": header,
            "team": seat["team"],
            "model": seat["model"],
            "start_ts": start_ts,
            "duration_sec": round(time.time() - t0, 2),
            "chars": len(content),
            "ok": ok,
            "ctx": [{"label": m["header"], "chars": len(m["content"])} for m in shared],
        })
        shared.append({"header": header, "content": content})
        records.append((header, content))
        print(f"🎭 监委旁听 {idx}/{len(STEPS)} · {header}... ✅ {len(content)} 字符")

    lines = [
        "# 🦅 鲲鹏志 · 《极昼》案 监委旁听评估（Event 3）",
        f"**旁听庭审**：{trial_path.name}",
        "**席位**：天蝎宫监察线 ×2（办案组组长 + 审理室干部，旁听席列席）",
        "**产出**：指控成立性评估 / 量刑建议风险评估 / 私语情报交换",
        "",
    ]
    for header, content in records:
        lines += [f"### {header}", "", content, ""]
    report = "\n".join(lines)

    from core.archive import save_run
    filename = save_run(
        "监委观察",
        "极昼-阜阳中院",
        report,
        {"models": ",".join(sorted({SEATS_SURVEILLANCE[k]["model"] for k, _ in STEPS})),
         "steps": len(STEPS), "_steps": steps,
         "trial_file": trial_path.name},
    )

    print(f"\n{'=' * 60}")
    print(f"🎭 监委旁听评估落幕 · 共 {len(records)} 轮 / {sum(len(c) for _, c in records)} 字符")
    print(f"💾 已落盘: {filename}")


if __name__ == "__main__":
    asyncio.run(main())

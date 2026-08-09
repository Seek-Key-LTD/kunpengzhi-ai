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
    ("suveilant_chief", "【旁听评估·办案组视角】你以安徽省阜阳市监委办案组组长身份全程旁听庭审。现在出具内部《庭审风险评估报告》：①两项罪名在法庭交锋中遭遇的攻击点与风险等级；②庭审中辩方哪些手段属于诡辩或对证据的歪曲利用，应当如何驳斥或补强证据应对；③若判决不利，补救与翻盘路径——是否申请抗诉、补充侦查方向、向领导汇报的口径。你的立场：调查结论经监委集体审议确认，证据确实充分，问题出在庭审对抗环节而非调查本身。措辞专业冷静，就事论事。"),
    ("suveilant_review", "【旁听评估·审理室视角】你以安徽省阜阳市监委审理室干部身份全程旁听庭审。现在出具内部《量刑建议与公信力风险评估》：①公诉应提出的量刑建议区间及法律依据（利用影响力受贿罪/失职罪数罪并罚的量刑逻辑）；②若法院不采纳量刑建议乃至判决不利，对公诉考核指标与监委公信力的具体影响，以及对外应如何统一口径；③监检衔接改进意见——庭后与公诉人沟通时，应强调哪些工作要点（证据补强、庭审对抗技巧、必要时抗诉准备）。你的立场：指控方向经监委审议确认无误，评估目的是管理风险而非承认错误。措辞专业冷静。"),
    ("suveilant_chief", "【私语情报交换·办案组→审理室】两人在旁听席低声交换看法。你（办案组长）先说：向审理室干部通报对庭审对抗的判断——辩方哪些话术最危险、公诉人在庭审中的哪些应对失误给指控造成了被动（归因指向公诉环节，不指向调查本身），以及你倾向的补救动作（抗诉或补充侦查）。像两个同事在会场角落里低声议论，就事论事，不要客套。"),
    ("suveilant_review", "【私语情报交换·审理室→办案组】你（审理室干部）回应办案组长：结合量刑博弈现实，指出最坏情形下（判决不利）对办案组和检察院考核的连锁影响，并给出内部建议——向领导汇报的口径、对公诉方的工作要求（补强证据、庭审应对调整、是否建议检察机关抗诉）。像两个同事交换意见，就事论事，不要客套。"),
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

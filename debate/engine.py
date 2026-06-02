"""
辩论引擎 — 4v4 大专辩论会 + 讲茶大堂
=====================================

源于 Flow（4v4 辩论），高于 Flow（讲茶大堂 + TTS 语音）

用法:
    from debate.engine import DebateOrchestrator
    
    # 运行完整擂台（辩论 + 讲茶大堂）
    result = await DebateOrchestrator.run("白貂皮大衣: 铁证 vs 过度诠释")
"""

import asyncio
import os
from typing import Optional


# ─── 辩论正赛 ─────────────────────────────────────

class DebateMatch:
    """单场 4v4 辩论赛"""

    # 预设辩题
    TOPICS = {
        "1": {
            "title": "白貂皮大衣：全球贸易网络的铁证 vs 过度诠释",
            "pro": "白貂皮大衣是嚈哒帝国与东北亚保持联系的铁证，证明大同流亡军团理论",
            "con": "白貂皮大衣不过是转手贸易的结果，用来论证族群记忆是过度诠释",
            "emoji": "🧥",
        },
        "2": {
            "title": "木兰的哥哥：历史真相 vs 叙事虚构",
            "pro": "木兰无长兄的真正含义是长兄参加大同流亡军团西征",
            "con": "木兰无长兄是文学修辞，强行关联嚈哒帝国是过度解读",
            "emoji": "⚔️",
        },
        "3": {
            "title": "产权分割：安史之乱的经济学本质 vs 庸俗经济学滥用",
            "pro": "安史之乱=大股东收购母公司，产权理论是理解政治史的利器",
            "con": "用企业并购解释安史之乱是削足适履，忽略历史复杂性",
            "emoji": "💰",
        },
    }

    def __init__(self, topic_id: str):
        self.topic = self.TOPICS.get(topic_id, self.TOPICS["1"])
        self.transcript = []

    def build_prompt(self) -> str:
        """构建辩论 prompt"""
        t = self.topic
        return f"""
你是一个 4v4 大专辩论会的现场。

## 辩题
{t['title']}

## 正方立场
{t['pro']}

## 反方立场
{t['con']}

## 格式
请模拟完整辩论赛，按以下顺序：

【正方一辩】开篇立论（3分钟，激情澎湃）
【反方一辩】开篇立论（3分钟，冷静犀利）
【正方二辩】驳论（2分钟，接招拆招）
【反方二辩】驳论（2分钟，针锋相对）
【正方三辩】自由辩论攻防（至少3回合）
【反方三辩】自由辩论攻防（至少3回合）
【正方四辩】总结陈词（2分钟，升华）
【反方四辩】总结陈词（2分钟，致命一击）

风格像真正的大专辩论会，有火药味、有金句、有急智。
"""

    async def run(self, model: str = "gemini-2.5-flash") -> str:
        """运行辩论赛，返回完整文本"""
        prompt = self.build_prompt()

        proc = await asyncio.create_subprocess_exec(
            "pi", "--model", f"google-vertex/{model}",
            "--no-session", "-p", prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.getcwd(),
        )
        stdout, _ = await proc.communicate()
        debate_text = stdout.decode("utf-8", errors="replace")
        self.transcript.append(debate_text)
        return debate_text


# ─── 讲茶大堂 ─────────────────────────────────────

class Teahouse:
    """场外评论席"""

    @staticmethod
    async def comment(debate_text: str, model: str = "gemini-2.5-flash") -> str:
        """对辩论进行讲茶大堂评论"""
        prompt = f"""
你是一个茶馆里的各路食客，正在观看一场辩论赛。

## 辩论实录（节选）
{debate_text[:4000]}

## 角色
请模拟以下四人发表评论：

【茶博士】德高望重的老茶客，见多识广："呵呵，正方最大的问题是……反方虽然犀利但……"
【店小二】消息灵通的跑堂："哎哟喂，我刚听说啊……"
【神秘客】戴斗笠的独行客，压低声音："你们都忽略了更关键的问题……"
【账房先生】拨着算盘珠子："我算笔账啊，正方成功率……按赔率……"

每人至少一段，风格鲜活。
"""

        proc = await asyncio.create_subprocess_exec(
            "pi", "--model", f"google-vertex/{model}",
            "--no-session", "-p", prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        return stdout.decode("utf-8", errors="replace")


# ─── 擂台编排 ─────────────────────────────────────

class DebateOrchestrator:
    """完整擂台编排器：辩论 + 讲茶大堂 + 存档"""

    @staticmethod
    async def run(
        topic_id: str,
        model: str = "gemini-2.5-flash",
        save_dir: str = None,
    ) -> dict:
        """
        运行完整擂台

        返回:
            {"title": str, "debate": str, "teahouse": str, "file": str}
        """
        # 1. 辩论
        match = DebateMatch(topic_id)
        debate_text = await match.run(model)

        # 2. 讲茶大堂
        teahouse_text = await Teahouse.comment(debate_text, model)

        # 3. 存档
        result = {
            "title": match.topic["title"],
            "emoji": match.topic["emoji"],
            "debate": debate_text,
            "teahouse": teahouse_text,
        }

        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            import datetime
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"擂台-{match.topic['title'][:12]}-{ts}.md"
            filepath = os.path.join(save_dir, filename)

            with open(filepath, "w") as f:
                f.write(f"# 🦅 鲲鹏志 · 擂台\n\n")
                f.write(f"**辩题**: {match.topic['title']}\n\n")
                f.write(f"---\n\n## 🎤 辩论正赛\n\n{debate_text}\n\n")
                f.write(f"---\n\n## 🍵 讲茶大堂\n\n{teahouse_text}\n\n")
                f.write(f"---\n\n## 📊 统计\n")
                f.write(f"- 辩论: {len(debate_text)} 字符\n")
                f.write(f"- 评论: {len(teahouse_text)} 字符\n")
                f.write(f"- 模型: {model}\n")

            result["file"] = filepath

        return result


# ─── CLI ──────────────────────────────────────────

if __name__ == "__main__":
    import sys

    async def main():
        topic_id = sys.argv[1] if len(sys.argv) > 1 else "1"
        save_dir = sys.argv[2] if len(sys.argv) > 2 else "./擂台存档"

        result = await DebateOrchestrator.run(topic_id, save_dir=save_dir)

        print(f"\n{'='*60}")
        print(f"🦅 鲲鹏志 · 擂台")
        print(f"辩题: {result['title']}")
        print(f"{'='*60}")
        print(f"\n🎤 辩论 ({len(result['debate'])} 字符)")
        print(result['debate'][:300])
        print(f"\n🍵 讲茶大堂 ({len(result['teahouse'])} 字符)")
        print(result['teahouse'][:200])
        if result.get('file'):
            print(f"\n💾 已保存: {result['file']}")

    asyncio.run(main())

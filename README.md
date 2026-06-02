# 🦅 鲲鹏志 AI 辩论系统 v2.0

4v4 大专辩论会 + 🍵 讲茶大堂 + 🔊 微软免费 TTS

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境（复制并编辑）
cp .env.example .env

# 启动 Web 界面
chainlit run app.py --host 0.0.0.0 --port 8080

# 打开浏览器 → http://localhost:8080
# 密码: 3131
```

## 功能

### 🎤 4v4 大专辩论会
- 正方 4 人 vs 反方 4 人
- 开篇立论 → 驳论 → 自由辩论 → 总结陈词
- 预设 3 个辩题 + 自定义辩题
- 使用 Gemini 2.5 Flash（或配置其他模型）

### 🍵 讲茶大堂
- 茶博士：德高望重的老茶客
- 店小二：消息灵通的跑堂
- 神秘客：意想不到的视角
- 账房先生：算赔率、打分

### 🔊 微软免费 TTS
- 基于 edge-tts，无需 API Key
- 支持多种中文语音
- 辩论过程自动朗读

### CLI 独立运行

```bash
# 直接运行辩论赛
python debate/engine.py 1 ./存档目录

# 运行讲茶大堂
python app.py --teahouse debate_output.md
```

## 预设辩题

| # | 辩题 |
|---|------|
| 1 | 白貂皮大衣：全球贸易铁证 vs 过度诠释 |
| 2 | 木兰的哥哥：历史真相 vs 叙事虚构 |
| 3 | 产权分割：安史之乱的经济学本质 |

## 架构

```
用户输入辩题
    ↓
Chainlit Web 界面
    ↓
pi --model gemini-2.5-flash 运行辩论
    ↓
逐人逐句流式输出 + TTS 语音朗读
    ↓
辩论完成后 → 讲茶大堂场外评论
    ↓
存档 Markdown 文件
```

## 录制脚本示例

```python
from debate.engine import DebateOrchestrator
import asyncio

result = asyncio.run(
    DebateOrchestrator.run("1", save_dir="./擂台存档")
)
print(f"辩论完成: {result['file']}")
```

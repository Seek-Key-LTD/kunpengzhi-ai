# 🐋🦅 鲲鹏志 AI · 4v4 鹰洋鱼盲测辩论

## 📊 三屏联动监控

| 路由 | 用途 |
|------|------|
| [`/bagua`](/bagua) | 八卦乾坤看板（SVG 太极 + 八卦节点实时高亮 + MIDI 律吕和声） |
| [`/left-board`](/left-board) | CRT 终端监控（Bloomberg Telemetry + TTY Shell + Sequencer 灯条） |
| [`/status`](/status) | 系统健康检查 + 日志缓冲 |

---

### 核心机制
- **🦅 鹰洋鱼 (China vs US) 100% 盲测对抗** — 中美模型池各抽 4 个，辩论结束才解密
- **📊 Moneyball 数据驱动教练** — 正反方双教练并行策略 + 实时耳语指导
- **🏛️ 罗伯特议事规则** — 议事长每轮归纳交锋，8 辩位配八仙词牌定场诗
- **🔊 edge-tts 语音合成** — 书面语→口头语转换 + 拼接完整辩论录音
- **📐 运筹学并发流水线** — 教练耳语 / 议事长总结 / TTS 三路并发

### 技术栈
- LLM: Gemini 2.5 Flash via LiteLLM Proxy
- 向量检索: Cloudflare Vectorize (bge-m3, 1024d)
- 对象存储: Cloudflare R2 (TTS / 辩论实录)
- 实录归档: 内网 MinIO SSD (`ssd/kunpengzhi-archive/`)

---

输入 `1` / `2` / `3` 选择辩题开始辩论，或直接输入自定义辩题。

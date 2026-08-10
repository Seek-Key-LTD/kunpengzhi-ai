# 🦅 鲲鹏志 AI · 内容驱动辩论系统 v4.6

围绕《鲲鹏志》系列小说（牧人记 / 牧兰记 / 双约记 / 牧月记）的多场景 AI 辩论平台。
三套子系统并行：**4v4 鹰洋鱼盲测辩论**、**极昼案模拟法庭**、**Vibe Debating 礼乐评价**。

---

## 子系统全景

| 子系统 | 入口 | 框架 | 状态 |
|--------|------|------|------|
| 🥊 4v4 鹰洋鱼盲测辩论 | [`app.py`](app.py) | Chainlit | 主线（本地运行） |
| ⚖️ 极昼案模拟法庭 | [`streamlit_app.py`](streamlit_app.py) | Streamlit | dev=nuc / staging+prod=Heroku |
| 🎼 Vibe Debating 礼乐评价 | [`vibe-debating/`](vibe-debating/) | 设计稿 + ERC-20 | 设计阶段 |
| 🦞 Shrimp 打赏网关 | https://shrimp-agent.seekkey.eu.org | FastAPI + Base Sepolia | ✅ 全网可达（领豆/打赏/广播） |
| 🎫 VibeTicket 链上确权 | [`contracts/vibe-ticket/`](contracts/vibe-ticket/) | Solidity | Base Sepolia 部署 |

---

## 一、4v4 鹰洋鱼盲测辩论（`app.py` · Chainlit）

### 核心机制

**🦅 鹰洋鱼 (China vs US) 100% 盲测对抗**
- 中国模型池（DeepSeek / Qwen / GLM / Baichuan / Doubao / Moonshot / Hunyuan / Ernie）vs 美国模型池（GPT / Claude / Gemini / Llama）
- 各池无重复抽 4 个，随机分配正反方
- 盲测 ID `Model_1..8` 完全打乱，**辩论结束才解密**真实身份

**📊 Moneyball 数据驱动教练**
- 正反方双教练并行生成赛前策略（asyncio.gather 运筹学并发）
- 实时耳语指导 (teacher model) 80 字以内
- 历史辩论通过 Vectorize 检索作为数据参考

**🏛️ 罗伯特议事规则**
- 8 辩位 = 八仙八卦（乾☰坤☷艮☶兑☱离☲坎☵震☳巽☴）
- 议事长每轮归纳交锋焦点
- 每位辩手配词牌定场诗（鹊桥仙 / 卷珠帘 / 临江仙 / 苏幕遮 / 一剪梅 / 西江月 / 卜算子 / 虞美人）

**🔊 微软免费 TTS**
- edge-tts 合成 + 书面语→口头语转换
- pydub 拼接（带静音间隔），失败回退二进制拼接
- 上传 Cloudflare R2，生成完整辩论录音回放

**📐 运筹学并发流水线**
- 后台预取下一轮发言（关键路径并行）
- 教练耳语 / 议事长总结 / TTS 三路并发
- 打字机流式渲染 + 全局速度倍率（0.5x / 1x / 2x / 5x / 10x）+ 暂停

### 三屏联动 UI

| 路由 | 用途 |
|------|------|
| `/` (Chainlit 主界面) | 辩论交互 + 流式打字机 + TTS 回放 |
| [`/bagua`](public/dashboard.html) | 八卦乾坤看板（SVG 太极 + 八卦节点实时高亮 + MIDI 律吕和声） |
| [`/left-board`](public/kunpengzhi-qa.html) | CRT 终端风格监控（Bloomberg Telemetry + TTY Shell + Sequencer 灯条） |
| `/status` | 系统健康检查 + 日志缓冲 |

### 预设辩题

| # | 辩题 | 出处 |
|---|------|------|
| 1 | 白貂皮大衣：全球贸易铁证 vs 过度诠释 | 牧人记·第08章 半江瑟瑟半江红 |
| 2 | 木兰的哥哥：历史真相 vs 叙事虚构 | 牧人记·第07章 木兰无长兄 |
| 3 | 产权分割：安史之乱的经济学本质 | 牧人记·第01章 玉玺 |

---

## 二、极昼案模拟法庭（`streamlit_app.py` · Streamlit）

基于真实案卷 [`research/极昼.md`](research/极昼.md) 的多场景模拟法庭演练。

### 三种 Scenario

| Key | 场景 | 风格 |
|-----|------|------|
| `court` | ⚖️ 严肃刑事法庭模式 | 阜阳市中级人民法院刑事审判第一庭 |
| `honglou` | 📿 红楼梦贾府大观园模式 | 大观园家宴议事 |
| `fengyue` | 🍶 潇洒风月风流雅集模式 | 文人雅集品评 |

### 角色阵容

- **12 黄道内阁**（宝石命名：ruby/topaz/jasper/diamond/quartz/...）— 落宫规划至 `vault` LXC
- **紫罗兰掌门带领的七姐妹星团**（Violet Petal Group）— 落宫规划至 `warden` LXC
- 加锁访问（PIN `3131`），通过 `st.session_state` 保护 staging

---

## 三、Vibe Debating 礼乐评价（设计阶段）

**图灵测试平方 (Turing Test²)**：机器能不能像文明的中国人一样，说话时知礼知乐？

### 礼乐双轴评价

```
  言之有理（礼）          言之有乐（乐）
  ─────────────          ─────────────
  逻辑自洽               旋律美感
  辞藻精准               和弦适配
  回应切题               情绪连贯
  典故运用               词牌韵律贴合度
```

**最终得分 = 礼 × 乐**（非简单相加，二者缺一不可）

### 八席位词牌定基

| 席位 | 词牌 | 基调 |
|------|------|------|
| ☰ 乾 | 鹊桥仙 | G 小调 ✅ |
| ☷ 坤 | 卷珠帘 | TBD |
| ☶ 艮 | 临江仙 | TBD |
| ☱ 兑 | 苏幕遮 | TBD |
| ☲ 离 | 一剪梅 | TBD |
| ☵ 坎 | 西江月 | TBD |
| ☳ 震 | 虞美人 | TBD |
| ☴ 巽 | 卜算子 | TBD |

详见 [`vibe-debating/`](vibe-debating/) 与 [`vibe-debating/issues/`](vibe-debating/issues/)。

---

## 技术栈

| 层 | 技术 |
|----|------|
| Web UI | Chainlit (主线) + Streamlit (极昼支线) |
| LLM | Gemini 2.5 Flash via LiteLLM Proxy |
| 向量检索 | Cloudflare Vectorize (bge-m3, 1024d) |
| 对象存储 | Cloudflare R2 (TTS/实录) + 内网 MinIO SSD (归档) |
| TTS | edge-tts (微软免费) |
| 包管理 | **uv**（唯一，禁用 pip / requirements.txt） |
| 链上确权 | Solidity VibeTicket ERC-20 (Base Sepolia) |
| 多智能体 | AutoGen + pyautogen |

---

## 部署链路

| 环境 | 位置 | 入口 | 触发 |
|------|------|------|------|
| **dev** | nuc 本地 | `streamlit run streamlit_app.py --server.port 8501` | systemd `kunpengzhi-dev` |
| **staging+prod** | Heroku | `streamlit run streamlit_app.py`（[Procfile](Procfile)） | GitHub push → Heroku auto-deploy |
| **辩论主线** | 本地 / 独立部署 | `chainlit run app.py --port 8080` | 手动 |
| **Gitea 镜像** | `seekkey/kunpengzhi-ai` | - | git push |
| **Codeup 镜像** | 阿里云 Codeup | - | GHA [`mirror-to-codeup.yml`](.github/workflows/mirror-to-codeup.yml) |

CI：
- [`.github/workflows/issue-automation.yml`](.github/workflows/issue-automation.yml) — Issue 看板自动化
- [`.github/workflows/mirror-to-codeup.yml`](.github/workflows/mirror-to-codeup.yml) — 镜像到阿里云 Codeup

---

## 项目结构

```
├── app.py                      # Chainlit 主线：4v4 鹰洋鱼盲测辩论 (v4.6)
├── streamlit_app.py            # Streamlit 支线：极昼案模拟法庭
├── arena.py                    # CLI 擂台入口
├── chainlit.md                 # Chainlit 欢迎页内容
├── pyproject.toml              # 项目配置 + 依赖（uv 管理）
├── Procfile                    # Heroku 部署入口
├── AGENT.md                    # Agent 协作约定
├── DEV.md                      # 三环境（dev/staging/prod）运维总览
│
├── core/                       # 核心模块
│   ├── config.py               # 配置
│   ├── retriever.py            # 原文检索（本地优先 → GitHub raw 兜底）
│   ├── vectorize.py            # Cloudflare Vectorize + R2 映射表 RAG
│   └── graph_rag.py            # GraphRAG 知识图谱
│
├── debate/
│   └── engine.py               # 4v4 辩论 + 讲茶大堂编排
│
├── scripts/                    # 批处理工具
│   ├── checkpoint_runner.py    # 批处理调度
│   ├── burn_night.py           # 夜间批处理
│   ├── batch_processor.py      # 批量处理器
│   ├── index_books.py          # 书库索引
│   └── watchdog.py             # 状态监控
│
├── public/                     # 静态资源
├── contracts/vibe-ticket/      # VibeTicket ERC-20 合约
│
├── docs/                       # 架构 / 会议 / 计划文档（见 docs/INDEX.md）
│   ├── minutes/                # 8 agent 思辨会纪要
│   ├── hierarchy-plan.md       # V2.0 5 层架构蓝图
│   ├── whatif-analysis.md      # What-If 压力测试
│   └── 指标空间设计-v2.md       # 六维指标空间设计
│
├── dossiers/                   # 案卷（按案分目录）
│   ├── 极昼/                   # 诉讼阶段（真实案件）
│   │   ├── 极昼.md             # 案卷正文
│   │   ├── 反方弹药-恶意揣测.md # 公诉内部研判
│   │   ├── 实录/               # 辩论实录（.gitignore 忽略）
│   │   └── metrics/            # 竞技场指标（.gitignore 忽略）
│   └── 似有暗香来/             # 侦察阶段（虚构剧本杀，极昼创作渊源）
│
├── research/                   # 内容研究
│   └── deep-research-brief.md  # 《鲲鹏志》深度研究简报
│
└── vibe-debating/              # 礼乐双轴评价设计稿
    ├── 0001-螺线谱与礼乐评价体系.md
    └── issues/                 # 4 个议题
```

**运行时产物归档**：辩论实录 + 竞技场指标按案归入 `dossiers/<案名>/`（.gitignore 忽略），长期归档到 `ssd/kunpengzhi-archive/`（`mc alias ssd = minio-s3`）。

---

## 快速开始

```bash
# 安装依赖（仅 uv，禁用 pip）
uv sync

# 配置环境
cp .env.example .env

# 启动 4v4 辩论主线（Chainlit）
uv run chainlit run app.py --host 0.0.0.0 --port 8080
# → http://localhost:8080  密码: 3131

# 启动极昼案模拟法庭（Streamlit）
uv run streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
# → http://localhost:8501  PIN: 3131

# CLI 擂台（无 Web UI）
uv run python arena.py 1                # 跑辩题 1
uv run python arena.py --all            # 跑全部 3 个辩题
uv run python arena.py 1 --no-tts       # 跑辩题 1，无语音
```

---

## 环境变量

| 变量 | 用途 | 默认值 |
|------|------|--------|
| `DEBATE_MODEL` | 辩论模型名 | `gemini-2.5-flash` |
| `OPENAI_BASE_URL` | LiteLLM 代理地址 | `http://localhost:4000/v1` |
| `OPENAI_API_KEY` | LiteLLM 密钥 | - |
| `CLOUDFLARE_ACCOUNT_ID` | CF 账号 ID（Vectorize + R2） | - |
| `CLOUDFLARE_API_TOKEN` | CF API Token | - |
| `R2_BUCKET` | R2 桶名 | `kunpengzhi-tts` |
| `R2_PUBLIC_BASE` | R2 公开基址 | `https://kunpengzhi-debate.seekkey.eu.org` |
| `TTS_ENABLED` | 是否启用 TTS | `true` |
| `TTS_VOICE` | TTS 语音 | `zh-CN-YunxiNeural` |
| `CHAINLIT_AUTH_SECRET` | JWT 密钥 | - |
| `CHAINLIT_AUTH_ENABLED` | 是否开启认证 | - |
| `APP_PASSWORD` | 应用密码 | `3131` |

---

## 内容来源

- **小说文本**：GitHub `Seek-Key-LTD/kunpengzhi`（raw 直读，`digest` 分支）
- **评论文章**：`digest/彩虹屁/` 与 `digest/批判/`
- **极昼案卷**：[`dossiers/极昼/极昼.md`](dossiers/极昼/极昼.md)（诉讼阶段·真实案件）
- **似有暗香来**：[`dossiers/似有暗香来/红色剧本杀——似有暗香来.md`](dossiers/似有暗香来/红色剧本杀——似有暗香来.md)（侦察阶段·虚构剧本杀，极昼创作渊源）
- **深度研究**：[`research/deep-research-brief.md`](research/deep-research-brief.md)

---

## 文档导航

见 [`docs/INDEX.md`](docs/INDEX.md)。

## Agent 协作

见 [`AGENT.md`](AGENT.md)。

## 运维总览

见 [`DEV.md`](DEV.md)。

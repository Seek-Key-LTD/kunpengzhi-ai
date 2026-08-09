# 鲲鹏志 AI 辩论系统 — Agent Guide

## 项目定位

内容驱动的 AI 辩论系统，围绕《鲲鹏志》系列小说（牧人记/牧兰记/双约记/牧月记），提供：
- 4v4 八股辩论（开篇立论→驳论→自由辩论→总结陈词）
- Moneyball 数据驱动教练（正反方并行策略生成）
- RAG 原文检索（Vectorize + GitHub raw）
- Vertex AI Search Widget（知识库 Q&A）
- TTS 语音合成（edge-tts）
- 讲茶大堂（场外 AI 评论）

## 技术栈

| 层 | 技术 |
|------|------|
| Web UI | Chainlit (主线 app.py) + Streamlit (极昼支线 streamlit_app.py) |
| 静态文件 | public/ (custom.js, custom.css) |
| LLM | Gemini 2.5 Flash (via liteLLM proxy) |
| 向量检索 | Cloudflare Vectorize (bge-m3, 1024d) |
| 对象存储 | Cloudflare R2 (TTS/实录) + 内网 MinIO SSD (归档) |
| 包管理 | **uv** (仅 uv，不用 pip / requirements.txt) |
| 部署 | Heroku (Procfile auto-deploy) + nuc 本地 systemd |
| 语音 | edge-tts (微软免费 TTS) |
| 链上确权 | Solidity VibeTicket ERC-20 (Base Sepolia) |

## 关键约定（Agent 必读）

### 包管理
- **只用 uv**：`uv sync` / `uv add pkg` / `uv pip install pkg`
- 不要创建或修改 `requirements.txt`（已删除）
- 不要创建 `runtime.txt`（已删除，改用 `.python-version`）
- `pyproject.toml` 和 `uv.lock` 是唯一的依赖声明

### 项目结构
```
├── app.py              # Chainlit 主线：4v4 鹰洋鱼盲测辩论 (v4.6)
├── streamlit_app.py    # Streamlit 支线：极昼案模拟法庭（3 scenarios）
├── arena.py            # CLI 擂台入口
├── pyproject.toml      # 项目配置 + 依赖
├── chainlit.md         # Chainlit 欢迎页面内容
├── Procfile            # Heroku 部署入口（streamlit_app.py）
├── public/
│   ├── custom.js       # 注入脚本（侧栏、🔍 按钮、Widget）
│   └── custom.css      # 自定义样式
├── core/
│   ├── config.py       # 配置
│   ├── retriever.py    # 原文检索
│   ├── vectorize.py    # Vectorize 封装
│   └── graph_rag.py    # GraphRAG 知识图谱
├── debate/
│   └── engine.py       # 辩论引擎（4v4 + 讲茶大堂）
├── scripts/
│   ├── checkpoint_runner.py    # 批处理调度
│   ├── burn_night.py           # 夜间批处理
│   ├── batch_processor.py      # 批量处理器
│   ├── index_books.py          # 书库索引
│   └── watchdog.py             # 状态监控
├── contracts/vibe-ticket/      # VibeTicket ERC-20 合约
├── vibe-debating/              # 礼乐双轴评价设计稿
└── docs/                       # 架构 / 会议 / 计划文档（见 docs/INDEX.md）
```

### 部署
- **dev**: nuc 本地 systemd `kunpengzhi-dev`（streamlit_app.py :8501）
- **staging+prod**: Heroku 自动部署（GitHub push → [Procfile](Procfile) → `streamlit run streamlit_app.py`）
- **辩论主线 (app.py)**: 本地 `chainlit run app.py` 或独立部署
- **Gitea 镜像**: `seekkey/kunpengzhi-ai` 分支 `dev`
- **Codeup 镜像**: GHA [`.github/workflows/mirror-to-codeup.yml`](.github/workflows/mirror-to-codeup.yml)
- **辩论实录归档**: `ssd/kunpengzhi-archive/擂台存档/`（`mc alias ssd = minio-s3`；本地 `擂台存档/` 同步 + `runs.jsonl` 版本索引，含 git commit，供逐版本质量对比）

### 环境变量
| 变量 | 用途 |
|------|------|
| CHAINLIT_AUTH_SECRET | JWT 密钥 |
| CHAINLIT_AUTH_ENABLED | 是否开启认证 |
| OPENAI_BASE_URL | litellm 代理地址 |
| OPENAI_API_KEY | litellm 密钥 |
| DEBATE_MODEL | 辩论模型名（默认 gemini-2.5-flash） |

### 内容来源
- 小说文本：GitHub `Seek-Key-LTD/kunpengzhi`（raw 直读）
- 评论文章：`digest/彩虹屁/` 和 `digest/批判/`

## 开发环境

```bash
# 启动本地
export CHAINLIT_AUTH_SECRET=test123
export CHAINLIT_AUTH_ENABLED=false
uv run chainlit run app.py --port 8999 --host 127.0.0.1

# staging 验证（traefik 自动路由）
# → https://staging-chainlit.seekkey.eu.org/
```

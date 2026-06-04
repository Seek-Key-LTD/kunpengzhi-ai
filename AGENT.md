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
| Web UI | Chainlit (Python) |
| 静态文件 | public/ (custom.js, custom.css) |
| LLM | Gemini 2.5 Flash (via liteLLM proxy) |
| 向量检索 | Cloudflare Vectorize |
| 知识库搜索 | Vertex AI Agent Builder / Discovery Engine |
| 包管理 | **uv** (仅 uv，不用 pip / requirements.txt) |
| 部署 | Heroku + GitHub Actions CI/CD |
| 存储 | Cloudflare R2 |
| 语音 | edge-tts (微软免费 TTS) |

## 关键约定（Agent 必读）

### 包管理
- **只用 uv**：`uv sync` / `uv add pkg` / `uv pip install pkg`
- 不要创建或修改 `requirements.txt`（已删除）
- 不要创建 `runtime.txt`（已删除，改用 `.python-version`）
- `pyproject.toml` 和 `uv.lock` 是唯一的依赖声明

### 项目结构
```
├── app.py              # Chainlit 主应用（含辩论引擎、路由、API）
├── pyproject.toml      # 项目配置 + 依赖
├── chainlit.md         # Chainlit 欢迎页面内容
├── .chainlit/config.toml       # Chainlit 配置
├── public/
│   ├── custom.js       # 注入脚本（侧栏、🔍 按钮、Widget）
│   └── custom.css      # 自定义样式
├── core/
│   ├── config.py       # 配置
│   ├── retriever.py    # 原文检索
│   ├── vectorize.py    # Vectorize 封装
│   └── graph_rag.py    # GraphRAG 知识图谱
├── debate/
│   ├── engine.py       # 辩论引擎（4v4 + 讲茶大堂）
│   └── modern_engine.py
└── scripts/
    ├── checkpoint_runner.py    # 批处理调度
    ├── burn_night.py           # 夜间批处理
    ├── batch_processor.py      # 批量处理器
    └── watchdog.py             # 状态监控
```

### 部署
- **推 GitHub → GHA 自动部署 Heroku**（不要直接 git push heroku）
- 审核流程：本地改 → staging 验证 → git push → GHA deploy
- CI/CD 配置：`.github/workflows/deploy-heroku.yml`

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

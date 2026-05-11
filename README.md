# 鲲鹏志 AI 辩论服务

基于 Chainlit + AutoGen 的 4v4 智能辩论系统，集成 Wiki.js 知识库。

## 技术栈

- **Chainlit**: AI 应用前端
- **AutoGen**: 多智能体协作框架
- **Wiki.js GraphQL API**: 知识库检索
- **Heroku**: 云平台部署

## 功能特性

- ✅ 4v4 辩论队（正方 4 人 vs 反方 4 人）
- ✅ 实时查询 Wiki.js 获取背景知识
- ✅ 支持历史、地缘政治、文明演进等辩题
- ✅ 流式响应展示辩论过程

## 本地开发

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export OPENAI_API_KEY=your_key
export WIKI_JS_URL=https://wiki.git4ta.fun
export WIKI_JS_TOKEN=your_token

# 启动服务
chainlit run app.py
```

## Heroku 部署

```bash
# 创建应用
heroku create kunpengzhi-ai-debate

# 设置环境变量
heroku config:set OPENAI_API_KEY=xxx
heroku config:set WIKI_JS_URL=https://wiki.git4ta.fun
heroku config:set WIKI_JS_TOKEN=xxx

# 部署
git push heroku main

# 查看日志
heroku logs --tail

# 打开应用
heroku open
```

## 架构说明

```
用户输入辩题
    ↓
Chainlit 接收请求
    ↓
查询 Wiki.js GraphQL API 获取相关知识
    ↓
创建 8 个 AutoGen Agents（4v4）
    ↓
Agents 基于背景知识展开辩论
    ↓
流式返回辩论结果
```

## 下一步

- [ ] 集成 GraphRAG 知识图谱检索
- [ ] 实现真正的多轮辩论对话
- [ ] 添加辩论评分系统
- [ ] 支持导出辩论记录

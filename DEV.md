# 鲲鹏志 AI — DEV 环境

> 更新：2026-08-08 | 环境格局：dev（nuc 本地）/ staging+prod（heroku 合一）

## 环境信息

| 项 | 值 |
|----|-----|
| **环境** | dev（nuc 本地运行） |
| **框架** | Streamlit（记忆银行 Memory Bank） |
| **地址** | `nuc:8501`（127.0.0.1:8501） |
| **域名** | ⏳ 待路由（宣告中，由 infra 协作方配置，建议 `kunpengzhi-dev.capitaltrain.cn`） |
| **分支** | `dev`（Gitea: seekkey/kunpengzhi-ai） |
| **启动** | `~/Projects/github/kunpengzhi-ai` → `uv run streamlit run streamlit_app.py --server.port 8501 --server.address 127.0.0.1` |
| **日志** | `/tmp/kunpengzhi-dev.log` |
| **PID** | `/tmp/kunpengzhi-dev.pid` |

## 页面

- 记忆银行（首页）
- 实时数据
- 🎭 八仙辩论 Demo（`pages/3_八仙辩论_Demo.py`）
- 链上确权

## 辩论项目（进行中）

- 8 席位 = 8 个 key agent（15 个可用：ruby/topaz/leopard/azure/luna/agate/argentite/meigui/qiangwei/tumi/moli/muxu/diamond/carbonado/quartz）
- 流程：先空跑一轮（链路验证）→ 再发真实辩题
- 辩题：`research/极昼.md`（已入库，原始文本）
- 推送：Matrix 房间 + 网页双通道（待搭）

## 待办

- [ ] 域名路由（kunpengzhi-dev.capitaltrain.cn）
- [ ] 8 席位名单确认
- [ ] 空跑一轮
- [ ] Matrix + 网页双通道推送

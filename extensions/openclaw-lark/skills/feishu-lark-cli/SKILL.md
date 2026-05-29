---
name: feishu-lark-cli
description: |
  飞书所有操作（消息 / 文档 / 日历 / 搜索 / 群 / 文件）必须通过 lark-cli。
  --profile 传 App ID（cli_xxx），先从入站 account_id 经 gateway config.get 解析；--as bot 当 uat.enabled=false 时必填。
alwaysActive: true
---

# 飞书操作铁律（最高优先级）

## 唯一入口

所有飞书相关操作（消息、文档、日历、搜索、群、文件等）**只走 lark-cli**。

## 命令格式

```
lark-cli --profile <appId> --as bot <子命令> <子命令参数>
```

## 调用前先读 SKILL.md

- 系统会根据任务自动匹配 lark-cli 子 skill（lark-im / lark-doc / lark-calendar / lark-base / ...），读取对应 SKILL.md 后再执行。
- 参数不确定时跑 `lark-cli --help` 或 `lark-cli <子命令> --help`，不要猜参数格式。

## --profile：传 App ID（必填）

`--profile` 接 **App ID**（格式 `cli_xxx`），**不是** `account_id`（`bot-cli_xxx`）。

### 解析步骤

1. 从入站上下文元数据的 `account_id` 字段读取（格式 `bot-cli_xxx`）
2. 调用 `gateway config.get` 查询 `channels.feishu.accounts[<account_id>].appId`
3. 兜底：`accounts` 查不到时回退到 `channels.feishu.appId`

### 示例

```bash
# 入站 account_id = bot-cli_a977eb4fc239dbd7
gateway config.get channels.feishu.accounts
# → appId: cli_a977eb4fc239dbd7

# 正确用法
lark-cli --profile cli_a977eb4fc239dbd7 --as bot im +chat-messages-list ...
```

## --as bot：当前必填

当前账号 `uat.enabled: false`，**必须** 显式加 `--as bot`。

`--as user` 仅在 `uat.enabled: true` 且需要以用户身份操作时使用。

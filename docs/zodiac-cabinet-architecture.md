# 鲲鹏志 AI — 架构设计目标（Zodiac Cabinets & Underlay/Overlay）

> 更新：2026-08-08 | 状态：开发中（dev 优先，staging 加锁）
> 本文档沉淀 2026-08-08 讨论的架构设计，防止信息丢失（原讨论 agent 额度耗光未沉淀）。

---

## 一、总范式：从「静态剧本（HTML）」到「动态 Flow 引擎（PHP）」

当前模拟法庭/辩论 = 每本书每章节**手动硬编码 prompt**（HTML 范式）。目标 = 通用引擎（PHP 范式）：输入任意章节文本，引擎自动完成：

```
① 文章元数据与争议焦点解析（Context & Focus Extraction）
② 星象底色 → 章节化身动态绑定（Archetype-to-Avatar Binding）
③ 动态议事协议与令牌环（Flow Protocol：刑事法庭 / 国际条约谈判 / 学术探讨）
```

例：《极昼》→ 刑事模拟法庭协议；《双约记》（二战战后秩序）→ 国际外交条约谈判协议。

## 二、双层架构：Underlay（Coding Agent）→ Overlay（Acting Agent）

| 层 | 角色 | 中文定位 | 职责 |
|----|------|---------|------|
| **Underlay** | Coding Agent | 幕后编剧室 / 执局官 | 无观众闭门博弈几百轮（互相挑刺/据理力争）、Credit 打赏与掉落、编译《Session Contract（演练契约）》：协议 + 化身映射 + 硬约束 + 令牌 |
| **Overlay** | Acting Agent | 台前履职团 / 化身官（10 石 7 花） | 拿终极剧本，面对观众（网页/Heroku），以严肃沉静姿态完成法庭/地缘推演 |

**原则**：自制先于演绎——Overlay 开口前，Underlay 必须先完成规则自制（演员不能既当选手又当裁判）。

## 三、满编工位：12 黄道内阁（Zodiac Cabinets）+ 昴宿七姐妹（Flowers）

权威名单来自 **OpenBao/Vault Space**（`iac/providers/vault/variables.tf` agents 列表）——不是 Jade，是 **Jasper（碧石）与 Obsidian（黑曜石）**。

### 石头组（12 黄道内阁 · 门徒工位）→ 充当 **Acting Agent**

| 工位 | 石 | 黄道 | 角色示例 | 节点 |
|------|-----|------|---------|------|
| ruby | 红宝石 | ♌ 狮子座 | 审判长·首席掌盘 | nuc |
| topaz | 黄玉 | ♏ 天蝎座 | 首席公诉人·执法锐锋 | raccoon |
| amber | 琥珀 | ♊ 双子座 | 庭审书记员·时代记忆 | ash2 |
| emerald | 祖母绿 | ♉ 金牛座 | 资产评估员·审计 | mbp |
| azure | 天蓝石 | ♒ 水瓶座 | 陪审法官·逻辑防线 | onecloud1 |
| diamond | 金刚石 | ♎ 天秤座 | 首席辩护律师·铁壁 | pve |
| obsidian | 黑曜石 | ♏ 天蝎座 | 监察调查员·深邃监察 | xgp |
| jasper | 碧石 | — | 12 内阁补齐位 | ✅ **已落宫**（vault LXC 111） |
| carbonado | 黑金刚石 | ♈ 白羊座 | 助理公诉人·锐意 | pve2 |
| argentite | 辉银矿 | ♒ 水瓶座 | 自由法国/敏捷断理 | pve3 |
| agate | 玛瑙 | — | 四方辩手 | xgp |
| quartz | 石英 | ♐ 射手座 | 辩护法理员·规则透明 | ch1 |

（另有 luna 月华石、leopard 豹纹石 → 被告人尊长席 等。）

### 小花组（昴宿七姐妹）→ 负责场景专家合议（Review/Jury Panel）

moli（茉莉）/ muxu（苜蓿）/ zhuyu（竹芋）/ tumi（土豆花？）/ meigui（玫瑰）/ qiangwei（蔷薇）/ violet（紫罗兰）

- **Flower Manager = Violet（紫罗兰）**——小花组掌门人（✅ **已落宫**：warden LXC 108）
- 职责：针对大国划分做独立合议评议、人道主义与和平观察团

### Group Policy

- **石头（10 石 + Jasper + Obsidian = 12 内阁）** → 纯 Acting Agent（台前博弈履职）
- **小花（7 花）** → 场景合议/评估（专家评审团）
- **Violet** → 小花组 Manager

## 四、落宫计划（未完成 · 待办）

| 工位 | 状态 | 规划 |
|------|------|------|
| **Jasper（碧石）** | ✅ 已落宫（2026-08-09） | vault LXC 111，nomad 节点 ，keyagent + 静态注入 |
| **Violet（紫罗兰）** | ✅ 已落宫（2026-08-09） | warden LXC 108，nomad 节点 ，Flower Manager |

XGP 资源充足（58GiB RAM / 21GiB 可用，有 debian-12 标准底包）——可直接在 XGP 拉起同构 LXC（VMID 121 jasper / 122 violet）。

**落宫三步**：
1. 东西直接跑在 Console 的 BC1 里面
2. 密钥直接让 Vault Agent 跑起来（动态密钥物理注入到纯粹环境变量，零交叉污染）
3. 再调入 Nomad（jasper.nomad / violet.nomad 同构 job）

## 五、环境策略

- **dev**（NUC 本地，优先开发）：`kunpengzhi-dev.capitaltrain.cn`
- **staging/云端（Heroku）**：加 **PIN 锁 3131**（极简认证，阻断公网爬虫；未来可一行解开）
- 暂缓 Heroku 云端构建推送，优先本地 dev 开发

## 六、关键待办（tickets 待提）

- [x] jasper 落宫（✅ vault LXC 111，静态注入）
- [x] violet 落宫（✅ warden LXC 108，Flower Manager）
- [ ] staging PIN 3131 锁（云端）
- [ ] Flow 引擎范式落地（通用解析 → 化身绑定 → 协议调度）
- [ ] Underlay/Overlay 双层实现（编剧室博弈 + Credits + Session Contract）

## 附：昴宿七姐妹（Flowers）权威映射表（固定）

> 权威源：`infra/providers/vault/variables.tf`（agents 列表）+ vault gitea token 节点映射
> 本表为**唯一真相**——所有人统一按此称呼，勿另起名。

| agent | 花名 | 物理节点 | 定位 | 状态 |
|-------|------|---------|------|------|
| meigui | 玫瑰 | ash1 | 小花合议团 · 人道观察 | ✅ 落宫 |
| qiangwei | 蔷薇 | ash2 | 小花合议团 · 人道观察 | ✅ 落宫 |
| moli | 茉莉 | ch1 | 小花合议团 · 人道观察 | ✅ 落宫 |
| muxu | 苜蓿 | ch2 | 小花合议团 · 人道观察 | ✅ 落宫 |
| tumi | 荼蘼 | ash3 | 小花合议团 · 人道观察 | ✅ 落宫 |
| zhuyu | 茱萸 | de | 小花合议团 · 人道观察 | ✅ 落宫 |
| **violet** | **紫罗兰** | ⏳ warden（规划） | **Flower Manager（小花组掌门）** | ⏳ 未落宫 |

**Group Policy（固定）**：
- 石头组（12 黄道内阁）→ **Acting Agent**（台前博弈履职）
- 小花组（昴宿七姐妹）→ **场景专家合议 / Review / Jury Panel**
- **Violet（紫罗兰）= Flower Manager**（小花组掌门，未落宫）

## 附：12 黄道内阁权威名单补充（石头组）

| agent | 石 | 节点 | 状态 |
|-------|-----|------|------|
| jasper | 碧石（非 Jade！） | ⏳ vault 宿主（规划） | ⏳ 未落宫 |
| obsidian | 黑曜石 | xgp | ✅ |
| luna | 月华石 | onecloud2 | ✅ |
| leopard | 豹纹石 | suse（被告人尊长席） | ✅ |

> ⚠️ **非权威**：`jade`、`opal`、`garnet`、`pearl` 等不在 Vault Space 名单内，勿用于工位。

# 当前工作状态（交接给下一个 Session）

> 更新：2026-08-09 | 目标：看盘式庭审 · 一个人办成凤凰卫视
> 环境：dev = nuc :8501（systemd kunpengzhi-dev）｜ staging = Heroku

---

## 一、当前已完成（可跑）

- **12 黄道内阁 + 昴宿七姐妹**（紫罗兰 Flower Manager）法庭（《极昼》案）
- **完整令牌环引擎**（RobertTokenRingEngine：token_holder / 共享上下文 / 前发言人 / 全量记忆）— `core/token_ring.py`
- 极昼案卷事实（2026.8.3 阜阳留置）+ 起诉书模块
- 5 阶段双进度（顶部 banner + 右下角圆环）
- PIN 锁（dev 跳过，staging 需 3131）
- **对称看盘布局（初版）**：左 sidebar ticker（300px 可滚）/ 中核心 / 右进度（CSS 可滚）

## 二、认知要点（务必先理解，别急着写码）

### 看盘的本质（用户反复强调）
```
中间 2/3 trading panel = FIXED，不滚动（进化论/大脑驯化：核心焦点锚定「现在」）
左/右 = 可滚动信息流（ticker / order flow——历史与细节）
下 = newsfeed（实时报道流）
fixed 的要义 = 只显示「此刻」的一个画面（当前阶段/当前发言），不是历史堆叠
滚动 = 灾难（错过实时关键变化，大脑无法滚+盯同时）
```

### 布局目标（用户定的比例）
```
左 25% sidebar（可滚 ticker）| 中 50%（fixed 核心 + 下方 33% newsfeed）| 右 25%（可滚进度/证据）
```

### 架构愿景
- **Coding Agent（Underlay）剧本编译**：选题 → 自动定模式/角色/流程（非手动选）——目前 `selected_scenario_key = "court"` 是临时的
- **令牌环 = 动态发言权**（麦克风在谁手，实时流转）——目前是固定顺序执行
- **小花组 = 异步媒体评论团**（BBC/CCTV 等各立场，场外评价）
- 环境多配置：**代码 os.getenv，环境变量注入**（dev 本地 litellm 100.121.16.28:4000；Heroku seekkey.eu.org）——不要硬改代码默认值！

## 三、接下来要做（TODO）

1. **中区改真 fixed**：只渲染「当前阶段/当前发言」一个画面（固定视口），历史笔录移去滚动区/newsfeed —— **最高优先（用户当前最在意）**
2. 中区 60% 高度核心 + 下方 33% newsfeed（固定高度分割）
3. 比例微调（左 25 / 中 50 / 右 25）
4. 右栏完善（进度/证据/法条，可滚动）
5. **Coding Agent 剧本编译器**：选题 → 模式/角色/流程自动（Flow 引擎 #4）
6. **令牌环动态化**：发言权按规则实时流转（打断/响应）
7. **replay 模式**：不烧 token，回放之前成功笔录（调试用）
8. **暗黑模式切换**（先纯白）
9. 小花组媒体评论实时化（各立场动态生成）
10. 左侧 ticker 发言者 blinking 高亮

## 四、关键位置

```
代码：nuc ~/Projects/github/kunpengzhi-ai（Gitea dev 分支）
引擎：core/token_ring.py
布局：streamlit_app.py（render_speaker_ticker / render_stage_progress / 三列）
设计文档：docs/zodiac-cabinet-architecture.md（12 内阁/花名/落宫）
Vision：docs/flow-engine-vision.md（#4）、auction-allocation-vision.md（#6）、production-analysis-design.md（#7）
Gitea issues：seekkey/kunpengzhi-ai（#4 Flow 引擎 / #6 Auction / #7 产出分析 / #8 RFC 雷达图 / #9 看盘式庭审重构）
```

## 五、环境

```
dev：nuc:8501（http://192.168.31.239:8501 / kunpengzhi-dev.capitaltrain.cn）
staging：Heroku（PIN 3131）
litellm 本地：100.121.16.28:4000（模型见 /v1/models）
调试：Playwright CDP（raccoon 100.74.17.42:9223）——DOM 读布局，别截图+VLM
```

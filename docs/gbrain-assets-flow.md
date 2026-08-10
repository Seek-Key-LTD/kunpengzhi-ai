# G-Brain 资产灌入管线（Design v2）

> 状态：设计稿 · 作者：ruby · 日期：2026-08-10
> 原则：**先宣告，后灌入；先定义，后执行；引文必须可验证；真相单点在 nuc**

## 0. 背景与问题

高权重文档（论文 PDF、典籍全文、案卷）应落在 G-Brain 单源。当前基础设施三个病：

1. **没宣告**——agent 不知道上哪找什么（找不到鄂霍次克海/牛津剑桥/石器时代 PDF 就是症状）
2. **没灌入**——现成的高权重文档不在库里（道德经刚灌，古海洋学/文明起源类 PDF 未落）
3. **没验证**——引文可编造（圆桌第一轮编引文被用户抓，根因是验证管线不存在）

## 1. 资产分类（Asset Taxonomy）

| 类 | 内容 | 位置 | 状态 |
|---|---|---|---|
| A 章节 | 鲲鹏志章节 | gbrain 220 pages（单源） | ✅ 已灌 |
| B 案卷 | 极昼/似有暗香来/论述 | `dossiers/`（注册表定位器） | ✅ 已建 |
| C 文献 PDF | 论文/史料扫描件（牛津剑桥古海洋学、海生星/水生星、石器时代文明…） | 待宣告 | ⬜ 本管线 |
| D 典籍全文 | 道德经等公版全文 | gbrain | ✅ 道德经已灌 |

## 2. 管线（五步，先宣告后灌入）

```
① 宣告   资产条目 → Consul KV mcp/registry/assets/<slug>
② 提取   pdftotext（扫描件走 OCR）→ 清洗（去页眉/页脚/参考文献噪声）
③ 分块   按章/节/段落切块（中文语义块 500–1000 字）
④ 灌入   gbrain put <slug>（frontmatter: title/source/refs）
⑤ 验证   get 回读（字数/块数）→ 交叉验证（引文 ↔ 原文逐条核对）
```

## 3. 宣告协议（Consul KV 格式）

```json
// mcp/registry/assets/okhotsk-oxbridge-marine
{
  "title": "鄂霍次克海古海洋学 · 牛津/剑桥论文合集",
  "type": "paper-pdf",
  "source": "<飞书云盘 token | MinIO path | 本地路径>",
  "refs": ["黄河之水天上来", "木兰无长兄", "牧兰记"],
  "status": "declared | ingested | verified",
  "verifier": "<agent-id>",
  "verified_at": ""
}
```

## 4. 交叉验证协议

- 文章每个硬数据引文 → 在原文 PDF 定位 → 标注 `[已核对]` / `[存疑]` / `[作者推演]`
- 验证结果写回资产条目：`status=verified` + 验证报告（引文↔原文对照表）
- **红线**：无验证引文不得进讨论/节目（教训：编引文被用户抓）
- 分层证据标准：地质层看论文、语言层看音韵、叙事层看自洽（圆桌纪要已定）

## 5. 角色职责

| 角色 | 职责 |
|---|---|
| 灌入者 | 任意 agent，遵循管线五步 |
| 宣告者 | `mcp-registry` CLI（raccoon /opt/mcp-farm/mcp-registry） |
| 验证者 | 案卷内容：keyagent/adkgo；硬数据：searxng/原文核对；终审：用户（徐厚重） |
| 消费者 | field（法庭/讯问/演播）经 `load_material()` 统一调用层取资产 |

## 6. 触发时机

- 新 PDF/文献落地 → **宣告 + 灌入**（不得停留在「本地某处」）
- 文章引用新数据 → gbrain 查询未命中 → **提醒宣告**（防静默）
- 技能/文档提到「待考据」→ 进入验证队列，**24h 内闭环**（不得挂账）

## 7. 与现有系统关系

- gbrain：存储层（D 类已演示：道德经 81 章全文灌入，`河`字 0 次实证）
- dossiers/：案卷定位层（B 类）
- FIELD_REGISTRY + load_material()：统一调用层（C/D 类可被场消费）
- 本文档：宣告层的一部分，落 kunpengzhi-ai docs/（内容侧 SOP）

## 8. 工作流规矩（git 单一真相仓库）——2026-08-10 用户裁定

**背景**：git 多机协作的前提（可控制的协作者）不成立——keyagent/adkgo 的提交不受控；Mac/nuc 双副本导致 rebase 冲突、状态漂移、事后擦屁股。

**规矩**：
```
真相单点 = nuc ~/Projects/github/（kunpengzhi-ai / ai-ops 等）
所有 git 操作（add/commit/push/pull/rebase）一律 ssh nuc 执行
Mac 只做编辑暂存：写文件 → scp 到 nuc 仓库目录 → ssh nuc 提交推送
Mac 本地不保留 git 副本（~/code/github/...、/tmp/... 降级为只读引用）
keyagent/adkgo 不直接 push 共享分支——内容走 issue/PR 交付
nuc 部署目录 = 仓库本身（git pull 即部署，systemd 只读）
```

**协作面收窄原则**：协作的前提是控制——控制不了就收窄：git 降格为「单点写入的发布管道」，协作协议走宣告系统（Consul/mcp-registry），不信 git 分叉。

## 9. 待办（实施清单——由用户确认优先级后执行）

- [ ] 用户提供 C 类 PDF 的**源位置宣告**（飞书云盘/MinIO/本地）——拒绝 agent 瞎搜
- [ ] 逐份灌入 + 交叉验证（牛津剑桥古海洋学 / 海生星水生星 / 石器时代文明）
- [ ] mcp-registry 增加 `assets` 子命令（宣告/查询资产）
- [ ] 技能宣告：本文档写入 searxng/gitea 等技能引用链

# 论述型卷宗（鲲鹏志内容）

**内容不搬**——正文在 gbrain（nuc，220 pages，voyage-3-large 嵌入），本目录是**卷宗注册表**（每章 = 一个定位条目：slug 即 gbrain page key）。

## 检索通道（load_material type=essay）

- `gbrain search <词>`：tsvector 全文（不依赖外部 API，始终可用）
- `gbrain query <问句>`：向量混合 RRF + rerank-2-lite 重排（需 VOYAGE_API_KEY，已纳管 Vault kv/api/voyage）

## 书目

| 书 | 章节 | 注册表 | 说明 |
|---|---|---|---|
| 双约记 | 序言+目录+9 章 | 双约记.json | 1936-2022 世界秩序（雅尔塔/冷战/北约） |
| 牧人记 | 目录+19 章 | 牧人记.json | 华夏文明经济密码（玉玺/木兰/黄河） |
| 牧兰记 | 序言+目录+13 章 | 牧兰记.json | 史前大洪水/东亚迁徙（鲲鹏惊天变） |
| 牧月记 | 目录+序言+逻辑图 | 牧月记.json | 修订计划/逻辑地图（章节正文未发布） |

## 卷宗化语义

- 章节 ↔ 案件关联：如《木兰无长兄》（师卦军法）→ 极昼案件法理弹药；《黄河之水天上来》（大洪水时间线）→ 似有暗香来时间锚定素材
- 新增章节：gbrain pages put 入库 → 更新对应书 JSON

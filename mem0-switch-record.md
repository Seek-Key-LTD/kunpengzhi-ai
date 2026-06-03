# Mem0 切换记录

## 当前状态（已恢复）

- **配置文件**: `~/workspace/agent/openclaw.json`
- **绑定模式**: `loopback`（127.0.0.1:18789）
- **内存模式**: `platform`（Mem0 云 API）
- **网关运行**: 正常 ✅

```json
"env": {
  "vars": {
    "MEM0_MODE": "platform",
    "MEM0_USER_ID": "default",
    "MEM0_API_KEY": "mb1.bXBqLXphcHB5LWtha2EtNTM4N2Q2NGI.9NysgrnXZXfoq1WXDPZigCWlu0tQ_VU59Nlpr7VSi-s",
    "MEM0_HOST": "http://br-zappy-kaka-5387d64b.mem0.aidap-global.cn-beijing.volces.com"
  }
}
```

## 目标

切换到用户自建的 MongoDB 记忆库。

## 用户提供的连接信息

| 字段 | 值 |
|------|-----|
| MEM0_MODE | mongodb |
| MEM0_MONGODB_URL | `mongodb://admin:CZTqVMU9oMercE@GB975F8E58E2F38-LAKE3.adb.us-ashburn-1.oraclecloudapps.com:27017/admin?authMechanism=PLAIN&authSource=$external&ssl=true&retryWrites=false&loadBalanced=true` |
| VOYAGE_API_KEY | `pa-sclcuoqD4do_zRaymP91tT24eQ2Hi--CcVWddwMU6ry5` |
| OPENCODE_ZEN_API_KEY | `sk-DY7YQJJtJw9uLusp2bF3k5Okoo94QlE9NB4mfJEQZGx2ReRmHYoqy4Dski62HKph` |

MongoDB 网络连通性：✅ `GB975F8E58E2F38-LAKE3.adb.us-ashburn-1.oraclecloudapps.com:27017` 可达。

## 尝试过程与失败原因

### 尝试 1：MEM0_MODE=mongodb

直接把 `MEM0_MODE` 改成 `mongodb`，添加 `MEM0_MONGODB_URL` 等字段。

**结果**: ❌ 插件启动失败

**报错**:
```
Error: apiKey is required for platform mode (set mode: "open-source" for self-hosted)
```

**原因**: 插件 `index.ts` 第 429-430 行，mode 只识别 `oss` 和 `open-source`，其他值全部降级为 `platform`：

```typescript
const mode: Mem0Mode =
  cfg.mode === "oss" || cfg.mode === "open-source" ? "open-source" : "platform";
```

`mongodb` 被当成了 `platform`，platform 模式要求 `apiKey`，所以报错。

### 尝试 2：MEM0_MODE=open-source

理论上应该走 `OSSProvider`，但插件代码中 `OSSProvider` 类**没有实现**（类不存在，只有引用）。

```typescript
// index.ts:492-495
if (cfg.mode === "open-source") {
    return new OSSProvider(cfg.oss, cfg.customPrompt, (p) =>
      api.resolvePath(p),
    );
}
```

`OSSProvider` 未在任何文件中定义，也未从外部包导入。全网搜索不到 OSSProvider 实现。

### 尝试 3：安装 mem0ai Python 包

`pip3 install mem0ai` — 超时/无权限，未成功。

## 插件架构总结

- **插件路径**: `~/workspace/agent/extensions/openclaw-mem0-plugin/`
- **入口文件**: `index.ts`（1432 行）
- **API 客户端**: `lib/mem0.ts`（封装 Mem0 云 API HTTP 调用）
- **依赖**: `@sinclair/typebox`, `dotenv`（无 `mem0ai` npm 包）
- **支持的模式**:
  - `platform` ✅ — 调 Mem0 云 API（https://api.mem0.ai 或自定义 host）
  - `open-source` ❌ — OSSProvider 未实现，不可用
- **环境变量识别**: 通过 `resolveMem0EnvConfig()` 读取 `MEM0_*` 系列变量
- **外部 MongoDB URL、VOYAGE_API_KEY、OPENCODE_ZEN_API_KEY**: 当前版本插件**不读取也不使用**这些字段

## 后续方向

等待外部指导，通过百度消息提供下一步操作。

# 鉴权与 Token

SDK 的所有请求（REST 和 Socket.IO）都用同一个 Bearer Token 鉴权。

## Token 类型

| 类型 | 格式 | 有效期 | 用途 |
| --- | --- | --- | --- |
| API Key | `sk-blade-v2-...` | 长期有效，可吊销 | 后端服务、脚本、Vue/Node 应用 |
| Session JWT | 浏览器 cookie | 短期 | 已登录 Blade Agent 网页的同源前端 |

第三方集成优先使用 API Key。

## 创建 API Key

### 方式一：网页端创建

登录 Blade Agent 网页 -> 账号/设置 -> 创建 API Key -> 复制 `sk-blade-v2-...`。

### 方式二：前端 SDK 创建

用户已登录（带 cookie）时，可用 SDK 创建：

```ts
import { BladeClient } from "@blade-hq/agent-kit/client"

// 同源、已登录：浏览器自动带上 cookie
const client = new BladeClient({ baseUrl: "https://blade.example.com" })

const { plaintext } = await client.apiKeys.createApiKey("my-backend")
// plaintext 形如 "sk-blade-v2-..."，交给后端保存
```

`client.apiKeys` 还提供：
- `listApiKeys()` - 列出所有 key
- `renameApiKey(id, name)` - 重命名
- `deleteApiKey(id)` - 删除

::: warning
明文 key 只在创建响应里返回，请妥善保存。Python SDK 不负责创建 API Key，只消费已有的 key。
:::

## SDK 中注入 Token

Token 在构造 client 时注入，不要在单次方法调用里临时传。

### Node.js / 前端

```ts
import { BladeClient } from "@blade-hq/agent-kit/client"

const client = new BladeClient({
  baseUrl: "https://blade.example.com",
  token: "sk-blade-v2-...",
})
```

运行时会切换的 token 用 getter：

```ts
const client = new BladeClient({
  baseUrl,
  token: () => localStorage.getItem("blade-token"),
})
```

### Python

```python
from blade_agent_kit import BladeAgentClient

client = BladeAgentClient(
    "https://blade.example.com",
    token="sk-blade-v2-...",  # 不传则读环境变量 BLADE_AGENT_TOKEN
)
```

## 常见问题

| 问题 | 原因与修复 |
| --- | --- |
| REST 通但 Socket 不连 | REST 和 Socket.IO 共用同一个 token，确认用同一个 `BladeClient` 实例；换 token 后要重连 socket |
| 401 | token 过期、被吊销或未创建，重新获取 API Key |
| 本地 mock 环境 | 访问 `/api/auth/login` 签发登录态，再创建 API Key |

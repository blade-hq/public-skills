# 鉴权

SDK 的所有请求（REST 和 Socket.IO）都用同一个 Bearer Token 鉴权。

## 创建 API Key

登录 Blade Agent Web UI（`http://<host>:8020`）-> 账号/设置 -> 创建 API Key -> 复制 `sk-blade-v2-...` 格式的密钥。

```
┌─────────────────────────────────────────────┐
│  Blade Agent - 账号设置                       │
│                                             │
│  API Keys                                   │
│  ┌─────────────────────────────────────────┐ │
│  │ 名称           密钥              操作    │ │
│  │ my-backend     sk-blade-v2-***   [删除]  │ │
│  │                                         │ │
│  │              [+ 创建 API Key]            │ │
│  └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

也可以用前端 SDK 创建（用户已登录、浏览器带 cookie 时）：

```ts
import { BladeClient } from "@blade-hq/agent-kit/client"

const client = new BladeClient({ baseUrl: "http://<host>:8020" })
const { plaintext } = await client.apiKeys.createApiKey("my-backend")
// plaintext 形如 "sk-blade-v2-..."，交给后端保存
```

::: warning
明文 key 只在创建响应里返回，请妥善保存。
:::

## SDK 中注入 Token

Token 在构造 client 时注入，不要在单次方法调用里临时传。

### Node.js / 前端

```ts
import { BladeClient } from "@blade-hq/agent-kit/client"

const client = new BladeClient({
  baseUrl: "http://<host>:8020",
  token: "sk-blade-v2-...",
})
```

运行时会切换的 token 用 getter：

```ts
const client = new BladeClient({
  baseUrl: "http://<host>:8020",
  token: () => localStorage.getItem("blade-token"),
})
```

### Python

```python
from blade_agent_kit import BladeAgentClient

client = BladeAgentClient(
    "http://<host>:8020",
    token="sk-blade-v2-...",  # 不传则读环境变量 BLADE_AGENT_TOKEN
)
```

## Token 刷新

浏览器场景下，如果请求返回 401，SDK 会自动调用 `http://<host>:8020/api/auth/refresh` 续期。开发者通常不需要手动处理。

## 常见问题

| 问题 | 原因与修复 |
| --- | --- |
| REST 通但 Socket 不连 | REST 和 Socket.IO 共用同一个 token，确认用同一个 `BladeClient` 实例；换 token 后要重连 socket |
| 401 | Token 未注入或格式错误，确认 token 格式为 `sk-blade-v2-...` |
| 本地 mock 环境 | 访问 `/api/auth/login` 签发登录态，再创建 API Key |

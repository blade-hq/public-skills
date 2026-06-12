# 鉴权与 token

SDK 的所有请求（REST 和 Socket.IO）都用同一个 **Bearer token** 鉴权。接入前必须先拿到一个有效 token，否则建会话、发消息、读历史都会返回 401。

## token 是什么

Blade Agent 接受两类 Bearer token：

- **API key**（推荐第三方使用）：形如 `sk-blade-v2-...`，长期有效、可在管理界面或 SDK 里创建和吊销。后端服务、脚本、Vue / Node 应用都用它。
- **登录后的会话 JWT**：用户在浏览器登录后写入 cookie 的短期 token。仅适合"用户已经登录了 Blade Agent 网页"的同源前端场景。

第三方集成（尤其是后端）**优先用 API key**。

## 重要：API key 必须先登录才能创建

API key 属于某个登录用户。创建顺序是固定的：

1. 用户先登录 Blade Agent（拿到登录态 / cookie）。
2. 在登录态下调用「创建 API key」接口，拿到明文 key（`plaintext`）。
3. 把这个 key 交给后端 / SDK，作为 Bearer token 使用。

明文 key 只在创建响应里返回，请妥善保存。

## 创建 API key

### 方式一：网页端创建（最简单）

让用户登录 Blade Agent 网页，在账号 / 设置里创建一个 API key，复制 `sk-blade-v2-...`，配置到你的服务环境变量里（例如 `BLADE_AGENT_TOKEN`）。

### 方式二：前端 SDK 在登录态下创建

前端在用户已登录（带 cookie）时，可以用 client 直接创建：

```ts
import { BladeClient } from "@blade-hq/agent-kit/client"

// 同源、已登录：浏览器会自动带上登录 cookie
const client = new BladeClient({ baseUrl: "https://blade.example.com" })

const { plaintext } = await client.apiKeys.createApiKey("my-backend")
// plaintext 形如 "sk-blade-v2-..."，把它交给后端保存
```

`client.apiKeys` 还提供 `listApiKeys()`、`renameApiKey(id, name)`、`deleteApiKey(id)`。

> Python SDK（`blade-agent-kit`）**不负责创建** API key，只消费已创建好的 key。请用网页端或前端 SDK 创建。

## 在 SDK 里使用 token

token 在**构造 client 时**注入，不要在单次方法调用里临时传。

### 前端 / Node.js（`@blade-hq/agent-kit/client`）

```ts
import { BladeClient } from "@blade-hq/agent-kit/client"

const client = new BladeClient({
  baseUrl: "https://blade.example.com",
  token: "sk-blade-v2-...", // 或 token: () => getToken()
})
```

运行时会切换的 token 用 getter，方便换号后重连：

```ts
const client = new BladeClient({
  baseUrl,
  token: () => localStorage.getItem("blade-token"),
})
```

### Python（`blade-agent-kit`）

```python
from blade_agent_kit import BladeAgentClient

client = BladeAgentClient(
    "https://blade.example.com",
    token="sk-blade-v2-...",  # 不传则读环境变量 BLADE_AGENT_TOKEN
)
```

## 常见问题

- **REST 通但 Socket 不连**：REST 和 Socket.IO 共用同一个 token。确认 token 同时注入了两者（用同一个 `BladeClient` 即可），换 token 后要重连 socket。
- **401**：token 过期、被吊销，或根本没创建过。回到上面的创建流程重新拿一个 API key。
- **本地 mock 环境**：本地以 mock 模式启动后端时，浏览器访问 `/api/auth/login` 会直接签发登录态，之后即可按上面的流程创建 API key。

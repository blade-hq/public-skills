# 鉴权与 Token

SDK 的所有请求（REST 接口与实时通道）都用同一套凭证。

::: tip 浏览器场景看这里
前端页面不要直填令牌——用弹窗登录或 cookie 同域，见[登录配置](../frontend/login.md)。本页讲后端 / 自动化场景。
:::

## 创建访问令牌

访问令牌（也叫 API Key / PAT）是一个 `sk-blade-` 开头的长期密钥，代表某个用户的身份。两种获取方式：

**方式一：Web 界面**

登录 Blade Agent Web 界面（`http://<host>:8020`）→ 进入 `/env` 页面 → 创建 API Token → 复制 `sk-blade-...` 格式的密钥。

```
┌─────────────────────────────────────────────┐
│  Blade Agent - 账号设置                       │
│                                             │
│  API Keys                                   │
│  ┌─────────────────────────────────────────┐ │
│  │ 名称           密钥              操作    │ │
│  │ my-backend     sk-blade-***      [删除]  │ │
│  │                                         │ │
│  │              [+ 创建 API Key]            │ │
│  └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

**方式二：在浏览器里弹窗登录一次**

```html
<button id="login">登录 Blade 并获取令牌</button>
```

```ts
import { BladeClient } from "@blade-hq/agent-client"

const client = new BladeClient({ baseUrl: "http://<host>:8020" })
document.querySelector("#login")!.addEventListener("click", async () => {
  const { token } = await client.auth.login()   // 用户点"许可授权"后返回，30 天有效
  // 把 token 交给后端保存
})
```

::: warning
明文密钥只在创建时返回一次，请妥善保存。不要写进代码或提交到仓库，用环境变量。
:::

## 注入 Token

令牌在构造 client 时注入，不要在单次方法调用里临时传。

### Node.js

```ts
import { BladeClient } from "@blade-hq/agent-client"

const client = new BladeClient({
  baseUrl: "http://<host>:8020",
  token: process.env.BLADE_AGENT_TOKEN,
})
```

运行时会切换的令牌用 getter：

```ts
const client = new BladeClient({
  baseUrl: "http://<host>:8020",
  token: () => tokenStore.get(),
})
```

代码里主动换令牌用 `client.setToken(newToken)`——它会自动重建实时连接以携带新凭证。

### Python

```python
from blade_agent_kit import BladeAgentClient

client = BladeAgentClient(
    "http://<host>:8020",
    token="sk-blade-...",  # 不传则读环境变量 BLADE_AGENT_TOKEN
)
```

## Token 刷新

浏览器 cookie 同域场景下，如果请求返回 401，SDK 会自动调用 `/api/auth/refresh` 续期一次。直填令牌时不做自动续期。

## 常见问题

| 问题 | 原因与修复 |
| --- | --- |
| 401 | 令牌未注入或已失效，确认格式为 `sk-blade-...` 且未过期 |
| 403 | 令牌对应的账号无权访问该资源（比如不是会话所有者） |
| REST 通但实时通道不连 | 两者共用同一个凭证，确认用同一个 `BladeClient` 实例；换令牌要用 `client.setToken()` 触发重连 |
| 本地 mock 环境 | 访问 `/api/auth/login` 签发登录态，再创建 API Key |

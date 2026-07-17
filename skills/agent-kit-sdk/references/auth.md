# 登录与鉴权

SDK 的所有请求（REST 与实时通道）共用同一套凭证。有三种方式，按场景选择：

| 方式 | 适用场景 | 代码 | 后端配置 |
| --- | --- | --- | --- |
| 弹窗登录 | 浏览器第三方页面，让用户各自登录自己的 Blade 账号 | `await client.auth.login()` | 需要把页面 origin 加入 `BLADE_SDK_AUTH_ALLOWED_ORIGINS` |
| 直填访问令牌（PAT） | Node.js、脚本、CI 等自动化场景 | `new BladeClient({ baseUrl, token: "sk-blade-xxx" })` | 无 |
| cookie 同域 | 页面与 Blade 后端同域部署（或走同域反向代理） | `new BladeClient({ baseUrl: "" })` | 无 |

::: danger 浏览器里绝对不要直填令牌
访问令牌代表一个用户的完整身份。前端代码是公开的——把令牌写进前端（包括 `VITE_` / `NEXT_PUBLIC_` 等开头的环境变量，它们会被构建工具**明文编译进 JS 包**）等于把这个账号公开给所有访客。浏览器场景一律用弹窗登录或 cookie 同域。
:::

## 方式一：弹窗登录（浏览器）

```html
<button id="login">登录 Blade</button>
```

```ts
import { BladeClient } from "@blade-hq/agent-client"

const client = new BladeClient({ baseUrl: "https://blade.example.com" })

// 登录必须由用户点击触发：浏览器会拦截非用户操作弹出的窗口
document.querySelector("#login")!.addEventListener("click", async () => {
  const { user } = await client.auth.login()
  console.log("已登录:", user?.display_name)
})
```

流程：SDK 打开 Blade 的授权弹窗 → 用户（未登录则先登录）点击"许可授权" → 授权页把访问令牌发回你的页面（只发给发起登录的那个页面） → SDK 存起来并立即生效，REST 与实时通道立即生效。

- 令牌 30 天有效，默认存 localStorage（刷新页面不掉登录；改内存态传 `tokenStorage: "memory"`）。
- 退出登录：`client.logoutToken()`。
- React 项目直接用 `useAuth()`（见 react.md）；`ChatView` 在未登录时会自动显示内置登录按钮。

**后端配置（必须）**：出于安全考虑，只有允许列表内的页面来源能发起弹窗登录。管理员需在 Blade 后端设置环境变量：

```bash
# 逗号分隔多个来源；后端自己的域名默认放行，无需配置
BLADE_SDK_AUTH_ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com
```

未配置时弹窗会报"来源 xxx 未被允许发起 SDK 登录"。

## 方式二：直填访问令牌（自动化）

访问令牌（PAT，Personal Access Token）是一个 `sk-blade-` 开头的长期密钥，代表某个用户的身份。获取方式：

1. 在 Blade Web 界面的账号设置中创建 API 密钥；或
2. 在任意浏览器页面调用一次 `client.auth.login()`，返回值里的 `token` 即 PAT（30 天有效）。

```ts
const client = new BladeClient({
  baseUrl: "https://blade.example.com",
  token: process.env.BLADE_TOKEN,   // 不要把令牌写进代码或提交到仓库
})
```

运行时会变化的令牌用 getter：`token: () => store.getToken()`。

## 方式三：cookie 同域

页面与 Blade 后端部署在同一域名下时，浏览器 cookie 自动生效，什么都不用配：

```ts
const client = new BladeClient({ baseUrl: "" })  // 空字符串 = 当前域名
```

浏览器场景下 401 会自动尝试续期（`/api/auth/refresh`）一次。

## 探测当前登录态

```ts
try {
  const me = await client.auth.getMe()
  console.log("已登录:", me.username)
} catch {
  console.log("未登录")
}
```

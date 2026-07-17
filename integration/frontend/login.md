# 登录配置

SDK 的所有请求（REST 接口与实时通道）共用同一套凭证。有三种方式，按场景选一种：

| 方式 | 适用场景 | 代码 | 后端配置 |
| --- | --- | --- | --- |
| **弹窗登录** | 浏览器页面，让每个用户登录自己的 Blade 账号 | `await client.auth.login()` | 需要把页面来源加入 `BLADE_SDK_AUTH_ALLOWED_ORIGINS` |
| **直填访问令牌** | Node.js 后端、脚本、定时任务等自动化场景 | `new BladeClient({ baseUrl, token: "sk-blade-xxx" })` | 无 |
| **cookie 同域** | 页面与 Blade 后端同域部署（或走同域反向代理） | `new BladeClient({ baseUrl: "" })` | 无 |

::: danger 不要在浏览器里直填令牌
访问令牌代表一个用户的完整身份。前端代码是公开的——把令牌写进前端**等于把这个账号公开给所有访客**。

尤其注意：`VITE_` / `NEXT_PUBLIC_` 等开头的环境变量**会被构建工具明文编译进 JS 包**，它们不是密钥保管处。别写 `token: import.meta.env.VITE_BLADE_TOKEN`。

浏览器场景一律用弹窗登录或 cookie 同域。
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

流程：SDK 打开 Blade 的授权弹窗 → 用户（未登录则先登录）点击"许可授权" → 授权页把访问令牌发回你的页面（只发给发起登录的那个页面） → SDK 存起来并立即生效，REST 与实时通道立即生效。用户不需要手工创建、复制粘贴任何密钥。

- 令牌 30 天有效，默认存在浏览器 localStorage（刷新页面不掉登录）。要改成只存内存，传 `tokenStorage: "memory"`。
- 退出登录：`client.logoutToken()`。
- React 项目直接用 `useAuth()`（见 [React 接入](./react.md#登录态-useauth)）；`ChatView` 在用户未登录时会自动显示内置登录按钮。

### 后端必须配置允许来源

出于安全考虑（防止钓鱼页面骗授权），只有允许列表内的页面来源能发起弹窗登录。管理员需要在 Blade 后端设置环境变量：

```bash
# 逗号分隔多个来源；必须是形如 https://example.com 的 origin，不带路径
BLADE_SDK_AUTH_ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com
```

后端自己的域名默认放行，本机同源调试不需要配置。未配置时弹窗会报「来源 xxx 未被允许发起 SDK 登录」。

::: tip 弹窗必须由用户点击触发
`login()` 要放在按钮的 click 回调里调用。在页面加载时自动调用会被浏览器当作弹窗广告拦截，报"登录弹窗被浏览器拦截了"。
:::

## 方式二：直填访问令牌（自动化）

访问令牌（也叫 PAT）是一个 `sk-blade-` 开头的长期密钥，代表某个用户的身份。获取方式二选一：

1. 在 Blade Web 界面的账号设置里创建 API 密钥；
2. 在任意浏览器页面调用一次 `client.auth.login()`，返回值里的 `token` 就是（30 天有效）。

```ts
import { BladeClient } from "@blade-hq/agent-client"

const client = new BladeClient({
  baseUrl: "https://blade.example.com",
  token: process.env.BLADE_TOKEN,   // 从环境变量读，不要写进代码或提交到仓库
})
```

运行时会变化的令牌用 getter：

```ts
const client = new BladeClient({
  baseUrl: "https://blade.example.com",
  token: () => tokenStore.get(),
})
```

代码里主动换令牌用 `client.setToken(newToken)`——它会自动重建实时连接以携带新凭证。不要绕过 SDK 手动改。

## 方式三：cookie 同域

页面与 Blade 后端部署在同一域名下时（或你的网关把 `/api` 反向代理到 Blade），浏览器 cookie 自动生效，什么都不用配：

```ts
const client = new BladeClient({ baseUrl: "" })  // 空字符串 = 当前域名
```

浏览器场景下遇到 401，SDK 会自动尝试续期一次。

## 探测当前登录态

```ts
try {
  const me = await client.auth.getMe()
  console.log("已登录:", me.username)
} catch {
  console.log("未登录")
}
```

React 里用 `useAuth()` 的 `isAuthenticated` / `isLoading` 即可，不用自己写。

## 常见问题

| 现象 | 原因与解法 |
| --- | --- |
| 401 未登录或凭证已失效 | 浏览器：`await client.auth.login()`；自动化：检查 `token` 是否传入且未过期 |
| 403 当前账号无权访问该资源 | 令牌对应的账号不是该会话的所有者 |
| `登录弹窗被浏览器拦截了` | `login()` 没在用户点击的回调里调用；或站点被禁止弹窗 |
| 弹窗里报「来源 xxx 未被允许」 | 管理员没配 `BLADE_SDK_AUTH_ALLOWED_ORIGINS` |
| `登录窗口已关闭` / `登录超时` | 用户关掉了弹窗，或 5 分钟内没点"许可授权"，提示重试即可 |
| REST 通但实时通道连不上 | 换令牌后没重连——用 `client.setToken(...)` 而不是手改 |

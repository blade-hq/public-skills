# 常见报错与排查

## 速查表

| 报错 / 现象 | 原因 | 修复 |
| --- | --- | --- |
| `找不到 BladeClient：请在组件树外层包一个 <BladeProvider client={client}>` | React 组件不在 `BladeProvider` 内，也没传 `client` 属性 | 外层包 `<BladeProvider client={client}>`，或直接 `<ChatView client={client} />` |
| `Cannot find module '@blade-hq/agent-kit/client'` | 用了已废弃的旧包 | 换成 `@blade-hq/agent-client`（核心）/ `@blade-hq/agent-react`（React） |
| 401 未登录或凭证已失效 | 没有凭证，或令牌过期（弹窗登录拿到的令牌 30 天有效） | 浏览器：`await client.auth.login()`；自动化：检查 `token` 是否传入且未过期 |
| 403 当前账号无权访问该资源 | 令牌对应的账号不是该会话的所有者 | 用会话所有者的账号登录，或改用该账号的令牌 |
| `登录弹窗被浏览器拦截了` | `login()` 不是在用户点击的回调里调用的，或站点被禁止弹窗 | 把 `login()` 放进按钮的 click 回调；或在浏览器设置里允许本站弹窗；或改用直填令牌 |
| 弹窗里报 `来源 xxx 未被允许发起 SDK 登录` | 后端没把你的页面 origin 加入允许列表 | 管理员设置 `BLADE_SDK_AUTH_ALLOWED_ORIGINS=https://你的域名`（逗号分隔多个） |
| `登录窗口已关闭，未完成授权` / `登录超时` | 用户关掉了弹窗，或 5 分钟内没点"许可授权" | 提示用户重试 |
| 浏览器控制台报 CORS：`No 'Access-Control-Allow-Origin' header` | 后端未放行你的页面 origin | 管理员在后端 CORS 配置里加入你的 origin；或把页面与后端部署到同域/走同域反向代理 |
| `state.connection` 一直 `connecting`，聊天发不出去 | `baseUrl` 不可达 / 写错（带了路径、端口错、http 与 https 混用）；或跨域被拒 | `baseUrl` 必须是后端 origin，不带路径；浏览器 Network 里看 `socket.io` 请求的真实状态码 |
| 实时通道连不上但 REST 正常 | REST 与实时通道共用同一个凭证，但换令牌后没重连 | 用 `client.setToken(...)`（会自动重建连接），不要绕过 SDK 手动改令牌 |
| `onCommand` 收不到指令 | action 拼写与技能工具返回值里的 `_meta.bridge.action` 不一致；或技能根本没返回 `_meta.bridge` | 核对两侧字符串完全一致；让技能作者确认工具返回值结构（见 page-collaboration.md） |
| `connectEmbedded() 需要 allowedOrigins` | iframe 形态没传允许来源 | 传 `allowedOrigins: ["https://blade.example.com"]`，不能省略也不能填 `"*"` |
| React 界面没样式 / 布局错乱 | 忘了导入样式，或宿主写了全局 `button`、`input` 样式污染组件 | `import "@blade-hq/agent-react/style.css"`；宿主样式限定到自己的容器，不写全局选择器 |
| `ChatView` 高度塌陷、不滚动 | 外层容器没有确定高度 | 外层给 `height`（如 `100vh`）且是 `display:flex; flex-direction:column; min-height:0` 的可收缩容器 |
| Node 脚本跑完不退出 | 实时连接还开着 | 拿到结果后 `client.socket().disconnect()`，或显式 `process.exit(0)` |
| Node 报 `ERR_REQUIRE_ESM` / `require is not defined` | 包是 ESM，项目用了 CommonJS | `package.json` 加 `"type": "module"`，用 `import` 而非 `require` |
| 智能体只说不做，不调用工具 | 会话处于规划模式 | 发送时显式传 `mode: "executing"`；或检查业务角色配置的初始模式 |
| 智能体说找不到上传的文件 | 消息里写的路径与上传返回的 `uploaded` 路径不一致 | 用返回的 `uploaded` 路径原样写进消息 |
| Vue 界面不更新 | 用了 `ref` 深层包裹，或直接改了快照对象 | 用 `shallowRef`，在 `subscribe` 回调里整体赋值 `state.value = chat.getState()` |

## 排查步骤

**先分清是哪一层出问题**：

1. 打开浏览器 Network 面板，看 REST 请求（如 `/api/auth/me`）的状态码。
   - 200：鉴权正常，问题在实时通道或前端渲染。
   - 401：凭证问题，见上表。
   - CORS 报错：后端未放行你的 origin。
2. 看 `socket.io` 请求（Network → WS）。101 = 已建立；其他状态码看响应体。
3. 在代码里打日志：

```ts
chat.subscribe(() => console.log("[state]", chat.getState().connection, chat.getState().status))
chat.on("error", (e) => console.error("[error]", e.message))
chat.on("chatEnd", (e) => console.log("[chatEnd]", e.status))
```

## 不要这样做

| 错误写法 | 正确做法 |
| --- | --- |
| `import { BladeClient } from "@blade-hq/agent-kit/client"` | `import { BladeClient } from "@blade-hq/agent-client"` |
| `import { ChatView } from "@blade-hq/agent-kit/chat"` | `import { ChatView } from "@blade-hq/agent-react"` |
| `fetch("/api/sessions", { headers: { Authorization: ... } })` | `client.api.post("/api/sessions", ...)` |
| 手动 `io(baseUrl)` 连 Socket.IO 自己拼事件 | `client.sessions.connect(sessionId)`，用 `AgentSession` |
| `POST /api/chat` 发消息 | `chat.send("...")` |
| 在渲染期调用 `login()` | 放进按钮 click 回调 |

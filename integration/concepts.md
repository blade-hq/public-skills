# 核心概念

## SDK 包

Blade 的接入 SDK 分为前端和后端两侧：

| 包 | 语言 | 用途 |
| --- | --- | --- |
| `@blade-hq/agent-client` | TypeScript | 框架无关核心：连接、登录、会话实时状态、REST 通道。浏览器与 Node.js 通用 |
| `@blade-hq/agent-react` | TypeScript | React 绑定：现成的 `ChatView` 聊天组件 + hooks |
| `blade-agent-kit` | Python | Python 后端客户端 |

::: tip 选哪个
- React 应用要嵌聊天界面 → `@blade-hq/agent-react`（+ `@blade-hq/agent-client`）
- Vue / Svelte / 自建 UI / Node.js → 只要 `@blade-hq/agent-client`
- 用 iframe 嵌 Blade 聊天页 → `@blade-hq/agent-client` 的 `connectEmbedded()`
- Python 后端 → `blade-agent-kit`
:::

::: warning 旧包已废弃
`@blade-hq/agent-kit`（含 `/client`、`/react`、`/chat` 入口）已被上面两个包取代，不要再使用。
:::

## 快速开始

```bash
npm install @blade-hq/agent-client @blade-hq/agent-react
```

```tsx
import { BladeClient } from "@blade-hq/agent-client"
import { BladeProvider, ChatView } from "@blade-hq/agent-react"
import "@blade-hq/agent-react/style.css"

const client = new BladeClient({ baseUrl: "https://blade.example.com" })

export default function App() {
  return (
    <BladeProvider client={client}>
      <div style={{ height: "100vh", display: "flex", flexDirection: "column", minHeight: 0 }}>
        <ChatView />
      </div>
    </BladeProvider>
  )
}
```

用户未登录时 `ChatView` 会显示登录按钮，点击走弹窗授权。详见 [React 接入](./frontend/react.md)。

::: warning 后端地址
`baseUrl` 必须是 Blade Agent 后端的 origin（如 `http://<host>:8020`），不带路径。同主机 `:80` 端口是 Blade OS，接口前缀为 `/api/v1/*`，与本 SDK 不兼容。
:::

## 会话（Session）

会话是一次智能体交互的完整上下文。每个会话有唯一的 `session_id`，包含消息历史、工具调用记录和工作目录。

```ts
// 创建会话并直接连接，返回可收发消息的实时会话对象
const chat = await client.sessions.create({ intent: "用户任务" })

// 或只创建，拿 ID
const { session_id } = await client.sessions.createSessionWithRequest({ intent: "用户任务" })

// 连接已有会话
const chat2 = await client.sessions.connect(session_id)
```

`chat` 是一个 `AgentSession`——会话的实时状态机，把实时通道、历史加载、断线重连全部封装好，对外只有三样东西：

```ts
chat.getState()                          // 状态快照（messages / isStreaming / status ...）
chat.subscribe(() => render())           // 订阅状态变化
await chat.send("分析上传的报告")         // 动作
chat.on("toolCall", (e) => ...)          // 事件监听
```

## 工作目录（Workspace）

每个会话拥有独立的文件系统目录。上传的业务文件存放在此，智能体可以读写这些文件。

```ts
await client.sessions.uploadFiles(session_id, ".", [
  { file: new File([buffer], "report.md"), name: "report.md" },
])
```

## 访问凭证

三种方式：浏览器弹窗登录、直填访问令牌（自动化场景）、cookie 同域。详见[登录配置](./frontend/login.md)。

```ts
// 浏览器：弹窗授权。必须由用户点击触发，否则会被浏览器当弹窗广告拦截
loginButton.addEventListener("click", async () => {
  await client.auth.login()   // 用户点"许可授权"即完成
})

// 自动化（Node.js 等服务端场景）：直填访问令牌。
// 浏览器里绝对不要这么做——前端代码是公开的，等于把账号给所有访客
const client = new BladeClient({ baseUrl: "...", token: process.env.BLADE_TOKEN })
```

## 工作模式

| 模式 | 字段值 | 用途 |
| --- | --- | --- |
| 规划模式 | `planning` | 拆需求、列计划、评审方案，不执行工具 |
| 干活模式 | `executing` | 调用工具、读写文件、完成业务动作 |

不传 `mode` 时，使用会话所属业务角色配置的初始模式——那由配置角色的人决定，前端看不到。

::: warning 自己调 send() 时，要智能体动手干活就显式传
别依赖默认值。真实业务请求一律显式传 `mode: "executing"`，否则可能遇到"智能体只说不做"。

```ts
await chat.send("分析上传的报告", { mode: "executing" })
```

用 React 的 `<ChatView>` 则不用管：它没有 `mode` 属性，内部已经兜底为 `executing`，并自带模式切换开关。
:::

## 页面协作

智能体可以驱动你的页面（高亮地图、刷新表格），你的页面也可以把用户操作交给智能体：

```ts
chat.onCommand("map.highlight", (payload) => map.highlight(payload))  // 智能体 → 页面
chat.attach("选中点位", { lng: 116.4, lat: 39.9 })                    // 页面 → 智能体
```

指令的 action 字符串由技能作者在工具代码里定义，详见[页面协作](./frontend/host-integration.md)。

## 整体流程

```
┌──────────────┐         ┌──────────────────┐         ┌──────────────┐
│  用户/宿主应用  │         │  Blade 前端 SDK  │         │  Blade Agent │
└──────┬───────┘         └────────┬─────────┘         └──────┬───────┘
       │                          │                          │
       │  1. new BladeClient()    │                          │
       │─────────────────────────>│                          │
       │                          │                          │
       │  2. auth.login()         │  弹窗授权 → 访问令牌      │
       │─────────────────────────>│<────────────────────────>│
       │                          │                          │
       │  3. sessions.create()    │  POST /api/sessions      │
       │─────────────────────────>│─────────────────────────>│
       │                          │  AgentSession            │
       │                          │<─────────────────────────│
       │                          │                          │
       │  4. chat.send("...")     │  实时通道                 │
       │─────────────────────────>│─────────────────────────>│
       │                          │                          │
       │  5. subscribe() 状态更新  │  流式回复 + 工具调用      │
       │<─────────────────────────│<─────────────────────────│
       │                          │                          │
```

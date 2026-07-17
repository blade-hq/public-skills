# React 接入

Blade 前端 SDK 分两个 npm 包：

| 包 | 作用 |
| --- | --- |
| `@blade-hq/agent-client` | 框架无关核心：连接后端、登录、会话实时状态。浏览器和 Node.js 通用 |
| `@blade-hq/agent-react` | React 绑定：现成的聊天组件 `ChatView` 和一组 hooks |

React 项目两个都装。

## 10 行跑通

```bash
npm install @blade-hq/agent-client @blade-hq/agent-react react react-dom
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

跑起来就是一个完整聊天界面：

- 没传 `sessionId` 会**自动创建会话**（会话 = 一次与智能体交互的完整上下文，含消息历史、工具调用记录和工作目录）。想接着上次的对话聊，见下面「sessionId 从哪来」。
- **`new BladeClient` 要写在组件外面**（像上面这样）。写进组件里的话，每次重新渲染都会新建 client、重连一次，聊天会疯狂闪断。
- 用户没登录时，`ChatView` 自己显示"登录"按钮，点击弹出授权页，用户点"许可授权"即完成。第三方域名需要后端配置，见[登录配置](./login.md)。
- 必须引一次 `@blade-hq/agent-react/style.css`，否则没有样式。
- `ChatView` 撑满父容器，外层要给出高度。最简单的写法是给外层容器加上 `height: 100vh; display: flex; flex-direction: column; min-height: 0`。

::: tip React 版本
支持 React 18 和 19（peerDependencies 为 `^18 || ^19`）。不需要 `--force` 或 `--legacy-peer-deps`。
:::

## BladeProvider

`BladeProvider` 只承载 client 级共享（一条实时连接、登录态），**不承载聊天状态**——同一个 Provider 下放多个 `ChatView` 各自独立对话，互不干扰。

```tsx
<BladeProvider client={client}>
  <ChatView sessionId={sessionA} />
  <ChatView sessionId={sessionB} />
</BladeProvider>
```

只有一处用到、不想套 Provider 时，直接给组件传 `client`：

```tsx
<ChatView client={client} />
```

## ChatView 属性

```tsx
// 智能体下发给页面的指令，详见"页面协作"。payload 是 unknown，用前先断言
const commands = {
  "map.highlight": (payload: unknown) => {
    const { cityIds } = payload as { cityIds: string[] }
    map.highlight(cityIds)
  },
}

<ChatView
  sessionId={id}                    // 三选一：连已有会话 / session={AgentSession 实例} / 都不传自动新建
  commands={commands}
  onToolCall={(toolCall) => console.log("工具调用", toolCall.name)}
  onPreview={(target) => showPreview(target)}   // 工具产出的可视化预览
  theme="system"                    // "light" | "dark" | "system"
  features={{ voiceInput: false }}  // 关掉不需要的功能（模型选择 / 语音 / 技能提及等）
  classNames={{ root: "h-full", userMessage: "text-right" }}
  components={{ EmptyState: () => <div>开始一个新任务</div> }}
  renderers={{ tool: { Bash: MyBashCard } }}   // 按工具名自定义工具卡片
/>
```

| 属性 | 签名 / 取值 | 说明 |
| --- | --- | --- |
| `client` / `session` / `sessionId` | — | 三选一；都不传就用 Provider 的 client 并自动建会话 |
| `commands` | `Record<string, (payload: unknown) => void>` | action → 处理函数。**与 `session.onCommand(action, (payload, meta) => ...)` 不同，这里的 handler 只有 `payload`，没有第二个 `meta` 参数**。`payload` 是 `unknown`，用前需自行断言或校验 |
| `onToolCall` | `(toolCall: ToolCallInfo) => void` | 参数**直接是工具调用对象**，组件内部已经帮你取好了，不是事件对象 |
| `onPreview` | `(target) => void` | 工具返回可视化预览时触发（仅 `target: "preview"`，见[页面协作](./host-integration.md)） |
| `theme` | `"light" \| "dark" \| "system"` | **是字符串，不是对象** |
| `features` | `ChatFeatures` | 功能开关，见下表 |
| `classNames` / `components` / `renderers` | — | 样式与渲染定制 |

`ChatFeatures` 的全部字段（都**默认开启**，传 `false` 才关掉）：

| 字段 | 关掉后 |
| --- | --- |
| `modelSelector` | 输入框菜单里不再有模型选择与思考开关 |
| `voiceInput` | 没有语音输入按钮 |
| `skillMention` | 输入 `/` 不再补全技能，也不展示技能状态 |

`commands` 里的 action 字符串（如 `"map.highlight"`）来自技能作者的工具代码，不是 SDK 内置的枚举——详见[页面协作](./host-integration.md)。

::: tip ChatView 没有 mode 属性——不用找了
别的文档会告诉你"真实业务一律显式传 `mode: "executing"`"，那是指自己调 `send()` 的场景。

`ChatView` 内部已经处理好了：它用会话当前模式，取不到时**兜底为 `executing`**，并且提供了让用户自己切换规划/干活模式的开关。用 `ChatView` 就不用操心 `mode`。
:::

## 创建会话时指定参数

```tsx
import type { BladeClient } from "@blade-hq/agent-client"
import { ChatView, useAgentSession } from "@blade-hq/agent-react"

function App({ client }: { client: BladeClient }) {
  const { session } = useAgentSession(undefined, {
    client,
    createRequest: { intent: "季度报表分析", solution_id: "my-solution" },
  })
  return session ? <ChatView session={session} /> : null
}
```

## sessionId 从哪来

后端返回的字段名是 `session_id`（蛇形），前端参数名是 `sessionId`（驼峰），指的是同一个东西。三种来源，按需选：

1. **不用管它** —— 首次接入最省事：`<ChatView />` 不传 `sessionId` 就自动建一个新会话。
2. **自己建、自己存** —— 需要让用户下次回来接着上次聊：

   ```ts
   const { session_id } = await client.sessions.createSessionWithRequest({ intent: "季度报表分析" })
   // 把 session_id 存进你的数据库或写进 URL，
   // 下次用户进来时传给 <ChatView sessionId={session_id} /> 就能接着上次的对话
   ```

3. **列出用户已有的** —— 让用户自己挑：

   ```ts
   const sessions = await client.sessions.listSessions()   // [{ id, intent, ... }]
   ```

::: warning
不要凭空编一个 `"your-session-id"`。会话必须是真实存在的，否则连接会 404。拿不准就别传，让 SDK 自动建。
:::

## 自建 UI：useChat

不想用现成界面时，数据层一个 hook 全搞定：

```tsx
import { getTextContent } from "@blade-hq/agent-client"
import { useChat } from "@blade-hq/agent-react"

function MyChat({ sessionId }: { sessionId: string }) {
  const { messages, isStreaming, send, stop } = useChat(sessionId)

  return (
    <div>
      {messages.map((m, index) => (
        // content 可能是字符串，也可能是内容块数组（图片等多模态消息）。
        // getTextContent 两种都能处理；自己写 typeof 判断的话，图片消息会悄悄渲染成空白。
        // entry_id 是可选字段，兜底用 index。
        <p key={m.entry_id ?? index}>{getTextContent(m.content)}</p>
      ))}
      <button onClick={() => send("你好")} disabled={isStreaming}>发送</button>
      {isStreaming && <button onClick={stop}>停止</button>}
    </div>
  )
}
```

返回值：`{ session, state, messages, isStreaming, isStopping, error, send, append, stop, answer }`。

自建 UI 前**务必先读**[聊天 UI 与自渲染](./chat-ui.md)：消息结构、工具调用怎么渲染、哪些消息要过滤、智能体反问时怎么作答，都在那里。

## 只要会话对象：useAgentSession

hooks 必须写在组件内部——写在模块顶层 React 会直接报 `Invalid hook call`。

```tsx
import { useEffect } from "react"
import { useAgentSession } from "@blade-hq/agent-react"

function MapChat({ sessionId }: { sessionId: string }) {
  const { session, state, error } = useAgentSession(sessionId)

  // 监听智能体指令（等价于 ChatView 的 commands 属性）
  useEffect(() => {
    return session?.onCommand("map.highlight", (payload) => {
      const { cityIds } = payload as { cityIds: string[] }
      map.highlight(cityIds)
    })
  }, [session])

  // 地图选点后塞进聊天输入框
  const handleMapClick = (point: { lng: number; lat: number }) =>
    session?.attach("选中点位", point)

  if (error) return <p>连接失败：{error.message}</p>
  return <MapCanvas onPick={handleMapClick} busy={state.isStreaming} />
}
```

会话实例由 client 缓存，组件卸载不会断开；需要彻底释放时调用 `session.dispose()`。

## 登录态：useAuth

```tsx
import { useAuth } from "@blade-hq/agent-react"

function LoginGate() {
  const { user, isAuthenticated, isLoading, login, logout } = useAuth()
  if (isLoading) return null
  if (!isAuthenticated) return <button onClick={() => login()}>登录 Blade</button>
  return <span>你好，{user?.display_name}<button onClick={logout}>退出</button></span>
}
```

三种登录方式的选择见[登录配置](./login.md)。

## 文件预览组件

工作区文件树和多格式预览（代码 / Markdown / 图片 / PDF / Office）在独立入口，不用预览的项目不会为它增加体积。

::: warning 两个前提
预览组件内部调用 `useBladeClient()`，**必须放在 `BladeProvider` 内**；而且与 `ChatView` 不同，它没有内置的 QueryClient 包裹，**宿主必须自备 `QueryClientProvider`**（TanStack Query）。
:::

```bash
# 预览组件需要你自己装 TanStack Query（只用 ChatView 则不需要）
npm install @tanstack/react-query
```

```tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { BladeProvider } from "@blade-hq/agent-react"
import { WorkspaceFilesPanel } from "@blade-hq/agent-react/preview"

const queryClient = new QueryClient()

export default function FilesApp({ sessionId }: { sessionId: string }) {
  return (
    <QueryClientProvider client={queryClient}>
      <BladeProvider client={client}>
        <WorkspaceFilesPanel sessionId={sessionId} />
      </BladeProvider>
    </QueryClientProvider>
  )
}
```

## 常见问题

| 现象 | 原因与解法 |
| --- | --- |
| 报错"找不到 BladeClient" | 外层没包 `<BladeProvider client={client}>`，也没传 `client` 属性 |
| 界面没样式 | 忘了 `import "@blade-hq/agent-react/style.css"` |
| 一直显示登录按钮 | 后端未把你的页面 origin 加入 `BLADE_SDK_AUTH_ALLOWED_ORIGINS`，见[登录配置](./login.md) |
| `commands` 没反应 | action 拼写与技能工具返回值里的 `_meta.bridge.action` 不一致 |

更多见[调试与排查](../debugging.md)。

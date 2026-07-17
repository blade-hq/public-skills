# React 接入（@blade-hq/agent-react）

`@blade-hq/agent-react` 是 Blade 的 React 绑定包，提供现成的聊天组件 `ChatView` 和一组 hooks。支持 React 18 与 19（peerDependencies 为 `^18 || ^19`）。

## 安装

```bash
npm install @blade-hq/agent-client @blade-hq/agent-react react react-dom
```

## 10 行跑通

```tsx
import { BladeClient } from "@blade-hq/agent-client"
import { BladeProvider, ChatView } from "@blade-hq/agent-react"
import "@blade-hq/agent-react/style.css"

const client = new BladeClient({ baseUrl: "https://blade.example.com" })

export default function App() {
  return (
    <BladeProvider client={client}>
      <ChatView />
    </BladeProvider>
  )
}
```

- 不传 `sessionId` 时自动创建新会话（`sessionId` 从哪来见下节）。
- **`new BladeClient` 要写在组件外面**（像上面这样）。写进组件里的话，每次重新渲染都会新建 client、重连一次，聊天会疯狂闪断。
- 用户未登录时，`ChatView` 显示内置登录按钮，点击走弹窗授权流（第三方域名需后端配置 `BLADE_SDK_AUTH_ALLOWED_ORIGINS`，见 auth.md）。
- 必须导入 `@blade-hq/agent-react/style.css`，否则组件没有样式。
- `ChatView` 撑满父容器，外层要给出高度：`height: 100vh; display: flex; flex-direction: column; min-height: 0`。

## BladeProvider

`BladeProvider` 只承载 client 级共享（一条 Socket.IO 连接、鉴权、登录流），不承载聊天状态——每个 `ChatView` / `useChat` 各自持有自己的会话，同一 Provider 下放多个聊天互不干扰。

```tsx
<BladeProvider client={client}>
  <ChatView sessionId="session-a" />
  <ChatView sessionId="session-b" />
</BladeProvider>
```

不想用 Provider 时，所有组件和 hooks 也接受 `client` 属性直传：`<ChatView client={client} />`。

## sessionId 从哪来

后端返回的字段名是 `session_id`（蛇形），前端参数名是 `sessionId`（驼峰），同一个东西。三种来源，按需选：

1. **不用管它** —— 首次接入最省事：`<ChatView />` 不传 `sessionId` 就自动建一个新会话。
2. **自己建、自己存** —— 需要让用户下次回来接着上次聊：

   ```ts
   const { session_id } = await client.sessions.createSessionWithRequest({ intent: "季度报表分析" })
   // 把 session_id 存进你的数据库或 URL，下次传给 <ChatView sessionId={session_id} />
   ```

3. **列出用户已有的** —— `await client.sessions.listSessions()`，让用户自己挑。

不要凭空编一个 `"your-session-id"`：会话必须真实存在，否则连接会 404。

## ChatView 属性

```tsx
<ChatView
  sessionId={id}                    // 三选一：连已有会话 / session={AgentSession 实例} / 都不传自动新建
  commands={{                       // 智能体下发给页面的指令（详见 page-collaboration.md）
    "map.highlight": (payload) => {
      const { cityIds } = payload as { cityIds: string[] }
      map.highlight(cityIds)
    },
  }}
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
| `commands` | `Record<string, (payload: unknown) => void>` | action → 处理函数。**注意与 `session.onCommand(action, (payload, meta) => ...)` 的差异：这里的 handler 只有 `payload`，没有第二个 `meta` 参数**。`payload` 类型是 `unknown`，用前需自行断言或校验 |
| `onToolCall` | `(toolCall: ToolCallInfo) => void` | 组件内部已经帮你取好了，参数**直接是工具调用对象**，不是事件对象。对比：`session.on("toolCall", (e) => e.toolCall.name)` 拿到的才是事件对象 |
| `onPreview` | `(target) => void` | 工具返回可视化预览时触发 |
| `theme` | `"light" \| "dark" \| "system"` | **是字符串，不是对象** |
| `features` | `ChatFeatures` | 功能开关，见下表 |
| `classNames` / `components` / `renderers` | — | 样式与渲染定制 |

`ChatFeatures` 的全部字段（都**默认开启**，传 `false` 才关掉）：

| 字段 | 关掉后 |
| --- | --- |
| `modelSelector` | 输入框菜单里不再有模型选择与思考开关 |
| `voiceInput` | 没有语音输入按钮 |
| `skillMention` | 输入 `/` 不再补全技能，也不展示技能状态 |

::: tip ChatView 没有 mode 属性——不用找了
别处会告诉你"真实业务一律显式传 `mode: "executing"`"，那是指自己调 `send()` 的场景。

`ChatView` 内部已经处理好了：它用会话当前模式，取不到时**兜底为 `executing`**，并提供了让用户自己切换规划/干活模式的开关。用 `ChatView` 就不用操心 `mode`。
:::

## useChat：自建聊天 UI

连接会话、订阅消息流、给出发送/停止动作的一站式 hook：

```tsx
import { getTextContent } from "@blade-hq/agent-client"
import { useChat } from "@blade-hq/agent-react"

function MyChat({ sessionId }: { sessionId: string }) {
  const { messages, isStreaming, send, stop } = useChat(sessionId)
  return (
    <>
      {messages.map((m, index) => (
        // content 可能是字符串，也可能是内容块数组（图片等多模态消息）。
        // getTextContent 两种都能处理；自己写 typeof 判断的话，图片消息会悄悄渲染成空白。
        // entry_id 是可选字段，兜底用 index。
        <p key={m.entry_id ?? index}>{getTextContent(m.content)}</p>
      ))}
      <button onClick={() => send("你好")} disabled={isStreaming}>发送</button>
      {isStreaming && <button onClick={stop}>停止</button>}
    </>
  )
}
```

消息结构的完整说明（`tool_calls` 怎么渲染、`kind` 非空的消息要过滤等）见 [message-rendering.md](message-rendering.md) —— **自建 UI 必读**。

返回值：

| 字段 | 说明 |
| --- | --- |
| `messages` / `isStreaming` | 快捷字段（等于 `state.messages` / `state.isStreaming`） |
| `state` | 完整会话快照 `SessionState`（见 client-core.md） |
| `session` | 底层 `AgentSession` 实例（连接完成前为 null），可用 `session.on(...)` 监听事件 |
| `send(content, options?)` | 发送消息，自动处理 AskUserQuestion 待答场景 |
| `append(text)` | 运行中追加说明 |
| `stop()` / `isStopping` | 停止当前回复 |
| `answer(text, toolCallId, data)` | 回答智能体的 AskUserQuestion 提问 |
| `error` | 连接错误 |

`useChat` 也接受已连接的 `AgentSession` 实例：`useChat(session)`。

## useAgentSession：只要连接与状态

hooks 必须写在组件内部——写在模块顶层 React 会直接报 `Invalid hook call`。

```tsx
import { useEffect } from "react"
import { useAgentSession } from "@blade-hq/agent-react"

function MapChat({ sessionId }: { sessionId: string }) {
  const { session, state, error } = useAgentSession(sessionId)

  // 监听智能体下发的指令（等价于 ChatView 的 commands 属性）
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

不传 `sessionId` 时自动创建会话；可用 `options.createRequest` 定制创建参数：

```tsx
const { session } = useAgentSession(undefined, {
  createRequest: { intent: "数据分析", solution_id: "my-solution" },
})
```

会话实例由 client 缓存，组件卸载不断开；需要彻底释放时调用 `session.dispose()`。

## useAuth：登录态

```tsx
import { useAuth } from "@blade-hq/agent-react"

function LoginGate() {
  const { user, isLoading, isAuthenticated, login, logout } = useAuth()
  if (isLoading) return null
  if (!isAuthenticated) return <button onClick={() => login()}>登录 Blade</button>
  return <span>你好，{user?.display_name}<button onClick={logout}>退出</button></span>
}
```

`login()` 走弹窗授权流，成功后令牌立即生效，并自动重连实时通道。必须放在用户点击的回调里，否则会被浏览器当弹窗广告拦截。

## 文件树与预览组件

工作区文件树、文件预览等组件在独立入口 `@blade-hq/agent-react/preview`。

**两个前提**：预览组件内部调用 `useBladeClient()`，**必须放在 `BladeProvider` 内**；而且与 `ChatView` 不同，它没有内置的 QueryClient 包裹，**宿主必须自备 `QueryClientProvider`**。

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

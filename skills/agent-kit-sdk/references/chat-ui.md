# 聊天 UI 与自渲染

本文说明如何展示 Blade Agent 聊天界面。

## React：直接复用 ChatView

React 应用可以直接使用 SDK 组件：

新项目先按 [react-quickstart.md](react-quickstart.md) 安装 `@blade-hq/agent-kit@0.5.11`、React 19 和 peer dependencies，再使用 `ChatView`。

```tsx
import { ChatView } from "@blade-hq/agent-kit/chat"

export function AgentPanel({ sessionId }: { sessionId: string }) {
  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden">
      <ChatView sessionId={sessionId} />
    </div>
  )
}
```

`ChatView` 默认处理：

- 历史消息加载。
- Socket.IO 流式更新。
- 输入框和停止生成。
- 文件附件。
- `/` skill command 和 `@skill` mention。
- `AskUserQuestion` 回答。
- 滚动到底部和 turn navigation。
- 技能状态栏、上下文 pill、草稿追加等 SDK 内部 UI 信号。

布局要求：外层必须是可收缩容器，至少包含 `height`、`min-height: 0`、`display: flex`、`flex-direction: column`、`overflow: hidden`。

## React：自定义 ChatView

轻量改样式用 `classNames`：

```tsx
<ChatView
  sessionId={sessionId}
  classNames={{
    root: "bg-white text-slate-950",
    messageListContent: "max-w-4xl",
    chatInputRoot: "border-t",
  }}
/>
```

替换语义组件用 `components`：

```tsx
<ChatView
  sessionId={sessionId}
  components={{
    EmptyState: () => <div className="py-16 text-center">开始一个新任务</div>,
  }}
/>
```

替换特定工具调用展示用 `renderers.tool`：

```tsx
import type { ToolRendererProps } from "@blade-hq/agent-kit/chat"

function BashTool({ toolCall }: ToolRendererProps) {
  return <pre>{toolCall.arguments}</pre>
}

<ChatView sessionId={sessionId} renderers={{ tool: { Bash: BashTool } }} />
```

不要依赖 SDK 内部 DOM 层级。

## React：headless hooks

如果要完全自建聊天界面：

```tsx
import { useChat } from "@blade-hq/agent-kit/react"

function CustomChat({ sessionId }: { sessionId: string }) {
  const { messages, isStreaming, send, stop } = useChat(sessionId)
  // 自行渲染 messages，并调用 send / stop
}
```

## Vue / 其他前端：自渲染

Vue 不能直接使用 `ChatView`，因为它是 React 组件。Vue 应用使用 `@blade-hq/agent-kit/client` 和底层 socket，自行渲染消息列表、输入框、工具状态和附件。

最小流程：

1. 用 `BladeClient` 创建 REST client。
2. 创建或选择 session。
3. 建立 socket 并 `session:subscribe`。
4. 监听 `turn:start` / `turn:patch` / `turn:end` 更新 Vue state。
5. 发送时 emit `chat:send`，业务任务显式传 `mode: "executing"`。

无附件时，`chat:send.message` 使用纯字符串。只做方案、不执行工具时才传 `mode: "planning"`。

### 推荐：用 getSessionTurns 取回复，避免手动拼 patch

`turn:patch` 是增量投影，自己拼装文本较繁琐。最省事的做法是用 socket 只感知"开始/结束"，在 `chat:end` 后调一次 `client.sessions.getSessionTurns(sessionId)` 拿完整投影来渲染。每个 turn 的 `blocks` 里 `type === "text"` 的 `content` 就是文本。

Vue 最小示例（已实测）：

```ts
import { BladeClient } from "@blade-hq/agent-kit/client"

const client = new BladeClient({ baseUrl: window.location.origin, token: () => token })

function extractText(blocks: unknown): string {
  if (!Array.isArray(blocks)) return ""
  return blocks
    .filter((b: any) => b?.type === "text")
    .map((b: any) => String(b.content ?? ""))
    .join("")
}

const { session_id } = await client.sessions.createSession("vue chat")
const socket = client.socket()
socket.on("turn:patch", () => {/* 可选：标记“输出中…” */})
socket.on("chat:end", async () => {
  const turns = await client.sessions.getSessionTurns(session_id)
  // turns: { role, blocks }[]；渲染其中 role==="assistant" 的最新一条
  render(turns.map((t: any) => ({ role: t.role, text: extractText(t.blocks) })))
})
socket.connect()
socket.emit("session:subscribe", { session_id })
socket.emit("chat:send", { session_id, message: "你好", mode: "executing" })
```

只要最终结果时这种最稳；需要逐字流式动画时，再叠加解析 `turn:patch` 的增量。

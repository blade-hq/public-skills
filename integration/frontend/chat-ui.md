# 聊天 UI 与自渲染

## ChatView 组件

`ChatView` 是开箱即用的 React 聊天组件，默认处理消息加载、流式更新、输入框、文件附件、skill 命令、滚动等。

```tsx
import { ChatView } from "@blade-hq/agent-kit/chat"

<ChatView sessionId={sessionId} />
```

### 自定义样式

用 `classNames` 覆盖样式类名：

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

### 替换语义组件

用 `components` 替换内部子组件：

```tsx
<ChatView
  sessionId={sessionId}
  components={{
    EmptyState: () => <div className="py-16 text-center">开始一个新任务</div>,
  }}
/>
```

### 自定义工具调用渲染

用 `renderers.tool` 替换特定工具的展示：

```tsx
import type { ToolRendererProps } from "@blade-hq/agent-kit/chat"

function BashTool({ toolCall }: ToolRendererProps) {
  return <pre>{toolCall.arguments}</pre>
}

<ChatView sessionId={sessionId} renderers={{ tool: { Bash: BashTool } }} />
```

## useChat Headless Hook

完全自建聊天界面时使用：

```tsx
import { useChat } from "@blade-hq/agent-kit/react"

function CustomChat({ sessionId }: { sessionId: string }) {
  const { messages, isStreaming, send, stop } = useChat(sessionId)

  return (
    <div>
      {messages.map((msg) => (
        <div key={msg.entry_id}>{messageText(msg.content)}</div>
      ))}
      <input onKeyDown={(e) => { if (e.key === "Enter") send(e.target.value) }} />
    </div>
  )
}
```

## ChatMessage 结构

`useChat` 返回的 `messages` 数组元素类型：

```ts
import type { ChatMessage, ToolCallInfo } from "@blade-hq/agent-kit/react"

interface ChatMessage {
  role: "user" | "assistant" | "tool" | "error"
  content: MessageContent          // string 或内容块数组
  reasoning?: string               // 思考过程
  tool_calls?: ToolCallInfo[]      // 工具调用（工具名字段是 name）
  status?: "streaming" | "completed" | "paused" | "failed" | "interrupted"
  duration_ms?: number
  entry_id?: string                // 可做 React key
  blocks?: ContentBlock[]          // 块级渲染时用
}

type MessageContent = string | MessageContentPart[]
type MessageContentPart =
  | { type: "text"; text: string }
  | { type: "image_url"; image_url: { url: string } }
  | { type: "file"; name: string; data: string }
```

提取纯文本：

```ts
function messageText(content: MessageContent): string {
  if (typeof content === "string") return content
  return content
    .map((part) => (part.type === "text" ? part.text : ""))
    .filter(Boolean)
    .join("\n")
}
```

## 工具调用渲染

`ToolCallInfo` 的 `arguments` 是 JSON 字符串，渲染前需 `JSON.parse`：

```tsx
function ToolCallCard({ call }: { call: ToolCallInfo }) {
  return (
    <div>
      <div>{call.display_name || call.name} - {call.status}</div>
      <pre>{prettyJson(call.arguments)}</pre>
      {call.result != null && <pre>{prettyJson(call.result)}</pre>}
    </div>
  )
}

function prettyJson(value: unknown): string {
  if (typeof value === "string") {
    try { return JSON.stringify(JSON.parse(value), null, 2) } catch { return value }
  }
  return JSON.stringify(value, null, 2)
}
```

::: warning ToolCallInfo vs ToolCallProjection
- `ToolCallInfo`（来自 `useChat`）：工具名字段是 `name`
- `ToolCallProjection`（来自 `getSessionTurns`）：工具名字段是 `tool_name`

不要搞混。
:::

## 模式事件过滤

自渲染时，以下 content block 不要当正文展示：

- `mode_change`
- `planning_enter`
- `planning_exit`
- `plan_status`

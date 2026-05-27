# 聊天 UI 与自渲染

本文说明如何展示 Blade Agent 聊天界面。

## React：直接复用 ChatView

React 应用可以直接使用 SDK 组件：

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
5. 发送时 emit `chat:send`。

无附件时，`chat:send.message` 使用纯字符串。

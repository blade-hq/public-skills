# 事件与数据结构参考

自渲染聊天 UI（Vue、React headless、自建前端）时，需要知道每个 Socket 事件的 payload 和每个投影的字段。
**所有类型都从 SDK 导出，IDE 有自动补全**，本文是一份速查表，方便没有补全的场景（比如用 AI 生成代码）对照。

类型来源：

- `@blade-hq/agent-kit/client`：`ServerToClientEvents`、`ClientToServerEvents`、`TurnProjection`、`ContentBlock`、`ToolCallProjection`、`PatchEnvelope` 等。
- `@blade-hq/agent-kit/react`：`ChatMessage`、`ToolCallInfo`、`MessageContent`（`useChat` 返回的就是这些）。

```ts
import type { TurnProjection, ContentBlock, ToolCallProjection } from "@blade-hq/agent-kit/client"
import type { ChatMessage, ToolCallInfo } from "@blade-hq/agent-kit/react"
```

## Socket 事件 → payload

`socket.on(事件名, payload => ...)` 时 TS 会自动推断 `payload` 类型。下面是聊天相关的核心事件。

### 服务端 → 客户端（`ServerToClientEvents`）

| 事件 | payload 类型 | 含义 |
| --- | --- | --- |
| `chat:start` | `ChatStartPayload` | 一次回答开始 |
| `turn:start` | `TurnProjectionPayload` | 新 turn 开始，带完整初始投影 |
| `turn:patch` | `PatchEnvelopePayload` | turn 增量更新（流式逐字、工具状态变化等） |
| `turn:end` | `TurnProjectionPayload` | turn 结束，带该 turn 的完整最终投影 |
| `chat:end` | `ChatEndPayload` | 整次回答结束（headless 模式的结构化结果在 `result` 字段） |
| `session:updated` | `SessionUpdatedPayload` | 会话元数据变化（标题等） |
| `workspace:files_changed` | `WorkspaceFilesChangedPayload` | 工作区文件被工具改动 |
| `system:error` | `SystemErrorPayload` | 运行出错 |
| `system:notification` | `SystemNotificationPayload` | 系统提示 |

> 还有 `task:*`、`artifact:*`、`bg:*`、`skills:changed`、`asr:*`（语音）、`vibe:logs:*`（vibe coding）等专用事件，自渲染聊天一般用不到。

### 客户端 → 服务端（`ClientToServerEvents`）

| 事件 | payload | 说明 |
| --- | --- | --- |
| `session:subscribe` | `{ session_id }` | 订阅一个会话的流式更新（连上后先发这个） |
| `session:unsubscribe` | `{ session_id }` | 取消订阅 |
| `chat:send` | `ChatSendPayload` | 发消息。无附件时 `message` 用纯字符串 |
| `chat:stop` | `ChatStopPayload` | 停止当前生成 |
| `chat:compact` | `ChatCompactPayload`（带 ack 回调） | 手动压缩上下文 |

## TurnProjection（一个 turn 的完整投影）

`turn:start` / `turn:end` 的 payload，也是 `getSessionTurns()` 返回数组的元素。主要字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `role` | `"user" \| "assistant" \| "system"` | 谁说的 |
| `status` | `"streaming" \| "completed" \| "paused" \| "failed" \| "interrupted"` | turn 状态 |
| `blocks` | `ContentBlock[]` | 内容块（文本、思考、工具等都在这里，按出现顺序） |
| `tool_calls` | `ToolCallProjection[]` | 这个 turn 里的所有工具调用 |
| `kind` | `"message" \| "compaction"` | 普通消息还是上下文压缩 |
| `model` | `string \| null` | 使用的模型 |
| `usage` | `Record<string, unknown> \| null` | token 用量 |
| `duration_ms` | `number` | 耗时 |
| `memory_refs` | `MemoryRef[] \| null` | 本 turn 注入的记忆引用 |

> 还有 `sequence` / `turn_id` / `loop_id` / `context_window` 以及一组 `compaction` / `archived_*` 字段（仅压缩 turn 用到）。

## ContentBlock（内容块）

```ts
interface ContentBlock {
  type:
    | "text"            // 正文文本，content 是字符串
    | "thinking"        // 思考过程
    | "tool_use"        // 工具调用（content 是参数）
    | "tool_result"     // 工具结果
    | "tool_ui"         // 工具自带的 UI 卡片
    | "tool_bridge"     // 工具触发宿主页面动作
    | "system_notification"
    | "mode_change"     // 模式切换，content = { from, to }
    | "planning_enter"  // 进入规划
    | "planning_exit"   // 退出规划
    | "plan_status"     // 规划状态
    | "ask_user_answer" // 用户对 AskUserQuestion 的回答
  content: unknown          // 类型随 type 变化，最常见是字符串
  tool_call_id?: string | null
  tool_name?: string | null
  display_name?: string | null   // 工具的友好显示名
}
```

最常用的提取文本：取 `blocks` 里 `type === "text"` 的 `content` 拼起来。

## ToolCallProjection / ToolCallInfo（工具调用）

两个结构几乎一样，区别只在**工具名字段名不同**，别搞混：

| 来源 | 工具名字段 |
| --- | --- |
| `ToolCallProjection`（投影 / `getSessionTurns`） | `tool_name` |
| `ToolCallInfo`（React `useChat` 的 `message.tool_calls`） | `name` |

公共字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `string` | 工具调用 ID |
| `display_name` | `string \| null` | 友好显示名（优先用它展示给用户） |
| `arguments` | `string` | **入参的 JSON 字符串**（不是对象，要自己 `JSON.parse`） |
| `result` | `unknown` | 工具返回结果 |
| `status` | `"pending" \| "done" \| "error" \| "cancelled" \| "awaiting_answer"` | 状态 |
| `duration_ms` | `number \| null` | 耗时 |
| `pending_question_ref` | 对象 \| null | 子任务在等用户回答时的引用 |

> **skill 调用就是普通工具调用**：语义搜索技能、读取技能等会以工具调用形式出现，看 `display_name` / `tool_name` 即可，无需特殊处理。

### 处理 arguments / result 的中文转义

`arguments` 是 JSON 字符串，可能含 `情感` 这种转义。**`JSON.parse` 后再渲染就会还原成中文**（JS `JSON.stringify` 默认不转义非 ASCII）：

```ts
function prettyJson(value: unknown): string {
  if (typeof value === "string") {
    try {
      return JSON.stringify(JSON.parse(value), null, 2) // 解析后中文自动还原
    } catch {
      return value
    }
  }
  return JSON.stringify(value, null, 2)
}

// 工具调用渲染
prettyJson(call.arguments) // 参数
prettyJson(call.result)    // 结果
```

## ChatMessage（React headless）

`useChat(sessionId).messages` 数组的元素。比 `TurnProjection` 更贴近 UI：

```ts
interface ChatMessage {
  role: "user" | "assistant" | "tool" | "error"
  content: MessageContent          // string 或 内容块数组
  reasoning?: string               // 思考过程（可单独折叠展示）
  tool_calls?: ToolCallInfo[]      // 工具调用（注意工具名字段是 name）
  status?: "streaming" | "completed" | "paused" | "failed" | "interrupted"
  duration_ms?: number
  entry_id?: string                // 可做 React key
  kind?: string                    // planning_enter/exit 等非消息条目
  memory_refs?: MemoryRefInfo[]
  blocks?: ContentBlock[]          // 需要块级渲染时用
  compaction?: CompactionInfo      // 压缩 turn 的元信息
}
```

其中 `MessageContent`：

```ts
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

## 一个完整的自渲染消息（含思考 + 工具调用）

```tsx
function MessageCard({ message }: { message: ChatMessage }) {
  return (
    <article>
      <div>{message.role}</div>
      {message.reasoning ? <pre>💭 {message.reasoning}</pre> : null}
      {messageText(message.content) ? <pre>{messageText(message.content)}</pre> : null}
      {(message.tool_calls ?? []).map((call) => (
        <div key={call.id}>
          🔧 {call.display_name || call.name} · {call.status} · {call.duration_ms ?? "-"}ms
          <pre>{prettyJson(call.arguments)}</pre>
          {call.result != null ? <pre>{prettyJson(call.result)}</pre> : null}
        </div>
      ))}
    </article>
  )
}
```

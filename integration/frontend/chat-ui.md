# 聊天 UI 与自渲染

两条路：用 `@blade-hq/agent-react` 的现成组件 `ChatView`，或者用会话状态自己渲染。

## ChatView：现成组件（React）

```tsx
import { ChatView } from "@blade-hq/agent-react"
import "@blade-hq/agent-react/style.css"

<ChatView sessionId={sessionId} />
```

默认处理消息加载、流式更新、输入框、文件附件、技能提及、滚动等。完整属性见 [React 接入](./react.md#chatview-属性)。

### 自定义样式

用 `classNames` 覆盖各区块的类名：

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

```tsx
<ChatView
  sessionId={sessionId}
  components={{
    EmptyState: () => <div className="py-16 text-center">开始一个新任务</div>,
  }}
/>
```

### 自定义工具调用渲染

按工具名替换工具卡片：

```tsx
function BashTool({ toolCall }) {
  return <pre>{toolCall.arguments}</pre>
}

<ChatView sessionId={sessionId} renderers={{ tool: { Bash: BashTool } }} />
```

### 主题与功能开关

```tsx
<ChatView
  sessionId={sessionId}
  theme="system"                     // "light" | "dark" | "system"
  features={{ voiceInput: false }}   // 关掉不需要的功能
/>
```

## 自渲染：会话状态

不用现成组件时，直接读会话状态快照。React 用 `useChat`（见 [React 接入](./react.md#自建-ui-usechat)），Vue 用 composable（见 [Vue 接入](./vue.md)），两者拿到的 `state` 结构完全一致：

```ts
const state = chat.getState()
// state.messages     渲染就绪的消息列表
// state.isStreaming  是否正在回复
// state.status       会话状态：created | running | completed | failed | interrupted
//                    | waiting_for_input；尚未取得时为 null
// state.mode         "planning" | "executing" | null
// state.connection   实时连接状态
// state.errorMessage 最近一次运行错误
```

## ChatMessage 结构

`state.messages` 的元素类型：

```ts
// 这些类型都由 @blade-hq/agent-client 直接导出，不需要自己派生
import type {
  ChatMessage,
  CompactionInfo,
  ContentBlock,
  MemoryRefInfo,
  MessageContent,
  ToolCallInfo,
} from "@blade-hq/agent-client"

interface ChatMessage {
  role: "user" | "assistant" | "tool" | "error"
  content: MessageContent          // string 或内容块数组
  reasoning?: string               // 思考过程
  tool_calls?: ToolCallInfo[]      // 工具调用（工具名字段是 name）
  status?: "streaming" | "completed" | "paused" | "failed" | "interrupted"
  kind?: string                    // 特殊消息类型：compaction / mode_change / plan_status ...
  duration_ms?: number
  timestamp?: string               // 消息开始时间
  entry_id?: string                // 可做 React key / Vue key
  parent_id?: string | null
  loop_name?: string               // 所属智能体循环："root" 为主智能体，其余为子智能体
  memory_refs?: MemoryRefInfo[]    // 本轮注入上下文的记忆引用
  blocks?: ContentBlock[]          // 块级渲染时用
  compaction?: CompactionInfo      // kind === "compaction" 时的压缩详情
}

type MessageContent = string | MessageContentPart[]
type MessageContentPart =
  | { type: "text"; text: string }
  | { type: "image_url"; image_url: { url: string } }
  | { type: "file"; name: string; data: string }
```

## 多模态消息：文字 + 图片 + 文件

`content` 有两种形态：纯文字时是字符串；带图片、文件的消息则是内容块数组。别自己写 `typeof` 判断，用 SDK 自带的这几个函数，两种形态都能处理：

```ts
import {
  getTextContent,
  getImageParts,
  getFileParts,
  contentPreview,
  groupMessagesByLoop,
} from "@blade-hq/agent-client"

// 文字部分
getTextContent(message.content)        // "帮我看看这张图"

// 图片部分：返回 [{ type: "image_url", image_url: { url } }, ...]
getImageParts(message.content).map((part) => part.image_url.url)

// 文件部分：返回 [{ type: "file", name, data }, ...]
getFileParts(message.content)

// 其他
contentPreview(message.content, 80)    // 截断预览
groupMessagesByLoop(messages)          // 按主 / 子智能体分组
```

::: danger 只用 getTextContent 的话，图片会消失
`getTextContent` 只负责文字。要让用户发的图片显示出来，必须再用 `getImageParts`：
:::

```tsx
import { getImageParts, getTextContent, type ChatMessage } from "@blade-hq/agent-client"

function Message({ message }: { message: ChatMessage }) {
  const text = getTextContent(message.content)
  const images = getImageParts(message.content)
  return (
    <div>
      {text && <p>{text}</p>}
      {images.map((part) => (
        <img key={part.image_url.url} src={part.image_url.url} alt="" />
      ))}
    </div>
  )
}
```

Vue 里同理，见 [Vue 接入](./vue.md#发送与流式渲染)。

## 工具调用渲染

`ToolCallInfo` 的 `arguments` 是 JSON 字符串，渲染前需要 `JSON.parse`：

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
- `ToolCallInfo`（来自 `state.messages`）：工具名字段是 `name`
- `ToolCallProjection`（来自 `state.turns` / `getSessionTurns`）：工具名字段是 `tool_name`

不要搞混。日常渲染用 `messages` 就够了。
:::

## 四个 status 不是一回事

四个地方都有 `status`，值域部分重叠但含义不同，写错了往往静默失效：

| 出处 | 取值 | 含义 |
| --- | --- | --- |
| `state.status`（会话） | `created` / `running` / `completed` / `failed` / `interrupted` / `waiting_for_input`；未加载时 `null` | 整个会话当前处于什么阶段 |
| `message.status`（消息） | `streaming` / `completed` / `paused` / `failed` / `interrupted` | 这一条消息收完了没 |
| `toolCall.status`（工具调用） | **`pending`** / **`done`** / `error` / `cancelled` / `awaiting_answer` | 这一次工具调用的结果 |
| `chatEnd` 事件的 `status` | `completed` / `paused` / `interrupted` / `failed` | 这一轮回复怎么结束的 |

::: danger 最容易写错的一个
工具调用完成是 **`done`**，不是 `completed`。写成 `toolCall.status === "completed"` 永远不成立，而且不报错——工具卡片会一直显示"进行中"。
:::

## 智能体反问用户时怎么办

智能体有时会反问用户（比如"你要导出哪个季度？"）。这时会话 `status` 变成 `waiting_for_input`，对应的工具调用 `status` 是 `awaiting_answer`。

**不作答的话，会话会永远停在这里。** 自建 UI 必须处理这种情况。

React 用 `useChat` 的 `answer()`：

```tsx
function AskUserPrompt({ sessionId }: { sessionId: string }) {
  const { state, answer } = useChat(sessionId)

  // 从消息里找出正在等待作答的提问
  const pending = state.messages
    .flatMap((m) => m.tool_calls ?? [])
    .find((tc) => tc.status === "awaiting_answer" && tc.name.includes("AskUserQuestion"))

  if (!pending) return null

  // toolCallId 就是这个工具调用的 id
  const submit = (text: string) =>
    answer(text, pending.id, { selections: {}, custom: { "0": text } })

  return <button onClick={() => submit("导出 Q3")}>导出 Q3</button>
}
```

`answer(text, toolCallId, data)` 的 `data`：`selections` 是选项式作答（问题序号 → 选中项序号数组），`custom` 是自由文本作答（问题序号 → 文本）。只填一种即可。

不用 React 时直接用 `send`：

```ts
await chat.send("导出 Q3", {
  askUserAnswer: { tool_call_id: pending.id, selections: {}, custom: { "0": "导出 Q3" } },
})
```

::: tip React 的便利
`useChat().send()` 在会话处于 `waiting_for_input` 时会**自动**把用户在输入框里敲的文字转成对最后一个待答问题的作答——简单场景直接 `send(text)` 就行，不必手动找 `toolCallId`。
:::

## 特殊消息过滤

自渲染时，`kind` 非空的消息不是普通正文，按需处理或跳过：

- `mode_change` — 工作模式切换
- `plan_status` — 计划状态
- `compaction` — 上下文压缩记录

```ts
const visible = state.messages.filter((m) => !m.kind)
```

## 事件表

需要在消息渲染之外响应事件时，用 `chat.on(name, handler)`（返回取消函数）：

| 事件 | 触发时机 |
| --- | --- |
| `message` | 一条消息接收完毕（不再流式更新） |
| `toolCall` | 智能体发起一次工具调用（首次出现） |
| `toolResult` | 一次工具调用出结果（done / error / cancelled） |
| `chatEnd` | 一轮回复结束，`status`: completed / paused / interrupted / failed |
| `error` | 运行错误（系统错误、发送失败等） |
| `modeChange` | planning / executing 模式切换 |
| `command` | 智能体给页面下发指令（一般用 `onCommand` 消费，见[页面协作](./host-integration.md)） |
| `notification` | 系统通知（技能阶段提示、后台任务启动等） |
| `workspaceChanged` | 工作区文件发生变化 |
| `artifact` | 智能体产出文件成果 |
| `toolPreview` | 工具返回可视化预览（HTML / URI） |
| `taskListUpdated` | 任务清单更新 |
| `backgroundTask` | 沙盒后台命令状态更新 |
| `rewind` | 会话被回溯到某个检查点 |
| `sessionUpdated` | 会话属性（名称、状态等）被服务端更新 |
| `sandboxOom` | 沙盒内存超限自动重启 |
| `replayMismatch` | 回放输入与历史不匹配，需决定保持回放还是转自主模式。**无人监听时 SDK 自动选择 `continue_replay`** |
| `attachRequested` / `insertTextRequested` | `attach()` / `insertText()` 被调用，渲染层应更新输入框 |

```ts
const off = chat.on("toolCall", ({ toolCall }) => console.log(toolCall.name))
```

事件处理函数抛异常只告警，不会中断会话。

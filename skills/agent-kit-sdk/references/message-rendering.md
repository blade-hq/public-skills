# 消息渲染（自建 UI 必读）

自己画聊天界面时，你拿到的是 `chat.getState().messages`。本文讲这个列表里有什么、怎么渲染、哪些坑会静默出错。

用 React 现成的 `<ChatView>` 的话，这些它都处理好了，不用读本文。

## 消息列表从哪来

```ts
const state = chat.getState()
state.messages   // ChatMessage[]，渲染就绪
```

React 用 `useChat(sessionId)` 的 `messages`；Vue 见 vue.md 的 composable。

::: tip 那 state.turns 是什么
`state.turns` 是服务端下发的原始记录（一个 turn = 智能体的一轮动作：说了什么、调了哪些工具），`messages` 就是由它加工来的。**日常渲染用 `messages` 就够，不用碰 `turns`。**
:::

## ChatMessage 结构

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
  content: MessageContent          // string 或内容块数组 —— 见下方警告
  reasoning?: string               // 思考过程
  tool_calls?: ToolCallInfo[]      // 工具调用（工具名字段是 name）
  status?: "streaming" | "completed" | "paused" | "failed" | "interrupted"
  kind?: string                    // 非空 = 特殊消息，见"哪些消息要过滤"
  duration_ms?: number
  timestamp?: string
  entry_id?: string                // 可选字段
  parent_id?: string | null
  loop_name?: string               // "root" 为主智能体，其余为子智能体
  memory_refs?: MemoryRefInfo[]
  blocks?: ContentBlock[]          // 块级渲染时用
  compaction?: CompactionInfo      // kind === "compaction" 时的压缩详情
}
```

## 坑 1：content 不一定是字符串

`content` 的类型是 `string | MessageContentPart[]`——用户发图片、文件等多模态消息时是数组：

```ts
type MessageContent = string | MessageContentPart[]
type MessageContentPart =
  | { type: "text"; text: string }
  | { type: "image_url"; image_url: { url: string } }
  | { type: "file"; name: string; data: string }
```

::: danger 不要自己写 typeof 判断
`typeof m.content === "string" ? m.content : "…"` 这种写法**不会报错也不会崩溃**，但用户一发图片消息，界面上就悄悄变成省略号或空白——最难发现的一类 bug。

用 SDK 自带的这几个函数，两种形态都能处理：
:::

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
groupMessagesByLoop(messages)          // 按主 / 子智能体分组（用 loop_name）
```

### 把图片真正显示出来

`getTextContent` 只负责文字。要让用户发的图片显示出来，还得用 `getImageParts`：

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

Vue 里同理：

```vue
<template>
  <div>
    <p>{{ getTextContent(msg.content) }}</p>
    <img
      v-for="part in getImageParts(msg.content)"
      :key="part.image_url.url"
      :src="part.image_url.url"
      alt=""
    />
  </div>
</template>
```

## 坑 2：entry_id 是可选的，别直接当 key

`entry_id?: string` 可能是 `undefined`。当 key 时兜底：

```tsx
{messages.map((m, index) => (
  <p key={m.entry_id ?? index}>{getTextContent(m.content)}</p>
))}
```

## 坑 3：四个 status 不是一回事

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

## 渲染工具调用

`ToolCallInfo` 的 `arguments` 是 JSON **字符串**，渲染前要 `JSON.parse`：

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
- `ToolCallProjection`（来自 `state.turns`）：工具名字段是 `tool_name`

日常渲染用 `messages` 就够了。
:::

## 哪些消息要过滤

`kind` 非空的消息不是普通聊天正文，直接当正文渲染会显示出一堆 JSON：

- `mode_change` — 工作模式切换
- `plan_status` — 计划状态
- `compaction` — 上下文压缩记录（对话太长时系统自动把旧内容压缩成摘要）

```ts
const visible = state.messages.filter((m) => !m.kind)
```

## 智能体反问用户时怎么办（重要）

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
`useChat().send()` 在会话处于 `waiting_for_input` 时会**自动**把用户在输入框里敲的文字转成对最后一个待答问题的作答——所以简单场景直接 `send(text)` 就行，不必手动找 `toolCallId`。
:::

## role: "error" 消息

`role === "error"` 是 SDK 注入的本地错误气泡（运行出错、发送失败等），不是后端的聊天记录。正常渲染成错误提示即可；它会在对话继续推进时自动消失。

## 事件表

需要在消息渲染之外响应事件时用 `chat.on(name, handler)`（返回取消函数）。完整表见 [client-core.md](client-core.md#事件监听)。
